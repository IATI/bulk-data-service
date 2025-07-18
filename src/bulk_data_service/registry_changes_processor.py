import asyncio
import json
import traceback
import uuid

from azure.servicebus import ServiceBusReceivedMessage
from azure.servicebus.aio import ServiceBusClient, ServiceBusReceiver
from azure.servicebus.exceptions import MessagingEntityNotFoundError, ServiceBusConnectionError

from utilities.dataset_reporting_org_utils import (
    get_new_dataset_db_record_from_mq_dataset,
    get_updated_dataset_db_record_from_mq_dataset,
)
from utilities.db import (
    get_dataset_in_bds,
    get_db_connection,
    get_reporting_org_in_bds,
    insert_or_update_dataset,
    update_dataset_registration_data,
)
from utilities.exceptions import BulkDataServiceRuntimeError
from utilities.misc import get_timestamp_as_str

from .dataset_updater import create_full_bds_dataset


def registry_changes_processor_start(context: dict):
    try:
        asyncio.run(registry_changes_service_loop(context))
    except KeyboardInterrupt:
        print("\n")
        print("User pressed Ctrl-C. Exiting")


async def registry_changes_service_loop(context: dict):

    registry_topic = context["AZURE_SERVICE_BUS_REGISTRY_TOPIC_NAME"]
    registry_sub = context["AZURE_SERVICE_BUS_REGISTRY_SUB_NAME"]

    sb_client = None

    while True:
        try:

            context["logger"].debug(f"registry_changes_service_loop - mark - {get_timestamp_as_str()}")

            if sb_client is None:
                sb_client = ServiceBusClient.from_connection_string(context["AZURE_SERVICE_BUS_CONNECTION_STRING"])

            try:
                receiver = await fetch_and_process_messages(context, sb_client)

                await asyncio.sleep(3)
            except MessagingEntityNotFoundError as e:
                context["logger"].warning(
                    f"registry_changes_service_loop - Connected to Azure Service Bus but could not find topic or subscription - {e}"
                )
                await asyncio.sleep(15)
            finally:
                await receiver.close()

        except ServiceBusConnectionError as e:
            context["logger"].warning(f"registry_changes_service_loop - Could not connect to Azure Service Bus - {e}")
            await asyncio.sleep(15)
        except Exception as e:
            context["logger"].warning(f"registry_changes_service_loop - Unexpected Error - {e}")
            print(traceback.format_exc())
            await asyncio.sleep(15)
        finally:
            if sb_client is not None:
                await sb_client.close()
                sb_client = None


def get_sb_receiver(context: dict, sb_client: ServiceBusClient) -> ServiceBusReceiver:

    topic = context["AZURE_SERVICE_BUS_REGISTRY_TOPIC_NAME"]
    subscription = context["AZURE_SERVICE_BUS_REGISTRY_SUB_NAME"]
    wait_time = context["AZURE_SERVICE_BUS_WAIT_TIME"]

    return sb_client.get_subscription_receiver(topic, subscription, max_wait_time=wait_time)


async def fetch_and_process_messages(context: dict, sb_client: ServiceBusClient) -> ServiceBusReceiver:

    receiver = get_sb_receiver(context, sb_client)

    msgs = await fetch_messages(context, receiver)

    for message in msgs:
        try:
            await process_message(context, message)
        except BulkDataServiceRuntimeError as e:
            context["logger"].error(f"process_message - Error processing message: {e}")
        finally:
            await receiver.complete_message(message)

    return receiver


async def fetch_messages(
    context: dict, receiver: ServiceBusReceiver, num_messages: int = 5
) -> list[ServiceBusReceivedMessage]:

    wait_time = context["AZURE_SERVICE_BUS_WAIT_TIME"]

    return await receiver.receive_messages(max_wait_time=wait_time, max_message_count=num_messages)


async def process_message(context: dict, msg: ServiceBusReceivedMessage):
    if msg.application_properties is not None and b"message_type" in msg.application_properties:
        message_type = msg.application_properties[b"message_type"].decode("utf-8")  # type: ignore[union-attr]
        await dispatch_message(context, message_type, json.loads(str(msg)))
    else:
        raise BulkDataServiceRuntimeError(
            "process_message - Message doesn't have the 'message_type' header in 'application_properties'"
        )


async def dispatch_message(context: dict, message_type: str, message_payload: dict):
    match message_type:
        case "DATASET_CREATED":
            create_new_dataset(context, message_payload)

        case "DATASET_UPDATED":
            update_dataset_metadata(context, message_payload)

        case "REPORTING_ORG_CREATED":
            # TODO: update DB
            context["logger"].info("Received REPORTING_ORG_CREATED event")

        case "REPORTING_ORG_UPDATED":
            # TODO: update DB
            context["logger"].info("Received REPORTING_ORG_UPDATED event")

        case "DATASET_DELETED" | "REPORTING_ORG_DELETED":
            context["logger"].info(f"Received {message_type} event")

        case _:
            print("Received unknown message type: ")
            print(json.dumps(message_payload))


def create_new_dataset(context: dict, message_payload: dict):
    dataset_db_record = get_dataset_in_bds(context, uuid.UUID(message_payload["dataset"]["id"]))

    if dataset_db_record is not None:
        raise BulkDataServiceRuntimeError(
            f"Recevied DATASET_CREATED message for dataset ID {message_payload["dataset"]["id"]} "
            f"but a dataset already exists with that ID. "
            f"Message received: {json.dumps(message_payload)}"
        )

    reporting_org_db_record = get_reporting_org_in_bds(
        context, uuid.UUID(message_payload["dataset"]["reporting_org_id"])
    )

    if reporting_org_db_record is None:
        raise BulkDataServiceRuntimeError(
            f"Recevied DATASET_CREATED message for dataset ID {message_payload["dataset"]["id"]} "
            f"but there is no reporting_org with the specified ID in the database. "
            f"Message received: {json.dumps(message_payload)}"
        )

    new_dataset_db_record = get_new_dataset_db_record_from_mq_dataset(message_payload["dataset"])
    with get_db_connection(context) as connection:
        insert_or_update_dataset(connection, new_dataset_db_record)
    context["logger"].info(f"Created dataset with ID {new_dataset_db_record["id"]}")


def update_dataset_metadata(context: dict, message_payload: dict):
    dataset_db_record = get_dataset_in_bds(context, uuid.UUID(message_payload["dataset"]["id"]))

    if dataset_db_record is None:
        raise BulkDataServiceRuntimeError(
            f"Recevied DATASET_UPDATED message for dataset ID {message_payload["dataset"]["id"]} "
            f"but no dataset with that ID exists. "
            f"Message received: {json.dumps(message_payload)}"
        )

    reporting_org_db_record = get_reporting_org_in_bds(
        context, uuid.UUID(message_payload["dataset"]["reporting_org_id"])
    )

    if reporting_org_db_record is None:
        raise BulkDataServiceRuntimeError(
            f"Recevied DATASET_UPDATED message for dataset ID {message_payload["dataset"]["id"]} "
            f"but there is no reporting_org with the specified reporting_org ID "
            f"{message_payload["dataset"]["reporting_org_id"]} in the database. "
            f"Message received: {json.dumps(message_payload)}"
        )

    if reporting_org_db_record["short_name"] != message_payload["dataset"]["reporting_org_short_name"]:
        raise BulkDataServiceRuntimeError(
            f"Recevied DATASET_UPDATED message for dataset ID {message_payload["dataset"]["id"]} "
            f"but the reporting_org_short_name specified does not match the short_name for the "
            f"reporting_org with ID {message_payload["dataset"]["reporting_org_id"]}. "
            f"Message received: {json.dumps(message_payload)}"
        )

    dataset_db_record = get_updated_dataset_db_record_from_mq_dataset(dataset_db_record, message_payload["dataset"])

    with get_db_connection(context) as connection:
        update_dataset_registration_data(connection, dataset_db_record)
    context["logger"].info(f"Updated metadata for dataset ID {dataset_db_record["id"]}")
