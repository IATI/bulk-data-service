import asyncio
import json
import uuid

from azure.servicebus import ServiceBusReceivedMessage
from azure.servicebus.aio import ServiceBusClient, ServiceBusReceiver
from azure.servicebus.exceptions import MessagingEntityNotFoundError, ServiceBusConnectionError

from bulk_data_service.data_converters import (
    convert_reporting_org_dto_to_reporting_org,
    get_new_dataset_from_dataset_registration_dto,
    update_dataset_from_dataset_registration_dto,
)
from config.bds_context import BDSContext
from utilities.db import (
    get_dataset_in_bds,
    get_db_connection,
    get_reporting_org_in_bds,
    insert_or_update_dataset,
    insert_or_update_reporting_org,
    remove_dataset_from_db,
    remove_reporting_org_from_db,
    update_dataset_registration_data,
)
from utilities.exceptions import BulkDataServiceRuntimeError
from utilities.misc import get_current_timestamp_as_str, get_timestamp_or_none


def registry_changes_processor_start(context: BDSContext):
    try:
        asyncio.run(registry_changes_service_loop(context))
    except KeyboardInterrupt:
        print("\n")
        print("User pressed Ctrl-C. Exiting")


async def registry_changes_service_loop(context: BDSContext):

    sb_client = None

    while True:
        try:
            context.logger.debug(f"registry_changes_service_loop - mark - {get_current_timestamp_as_str()}")

            if sb_client is None:
                sb_client = ServiceBusClient.from_connection_string(context["AZURE_SERVICE_BUS_CONNECTION_STRING"])

            try:
                receiver = await fetch_and_process_messages(context, sb_client)

                await asyncio.sleep(3)
            except MessagingEntityNotFoundError as e:
                context.logger.warning(
                    f"registry_changes_service_loop - Connected to Azure Service Bus "
                    f"but could not find topic or subscription - {e}"
                )
                await asyncio.sleep(15)
            finally:
                await receiver.close()

        except ServiceBusConnectionError as e:
            context.logger.warning(f"registry_changes_service_loop - Could not connect to Azure Service Bus - {e}")
            await asyncio.sleep(15)
        except Exception:
            context.logger.exception("registry_changes_service_loop - Unexpected Error")
            await asyncio.sleep(15)
        finally:
            if sb_client is not None:
                await sb_client.close()
                sb_client = None


def get_sb_receiver(context: BDSContext, sb_client: ServiceBusClient) -> ServiceBusReceiver:

    topic = context["AZURE_SERVICE_BUS_REGISTRY_TOPIC_NAME"]
    subscription = context["AZURE_SERVICE_BUS_REGISTRY_SUB_NAME"]
    wait_time = context.AZURE_SERVICE_BUS_WAIT_TIME

    return sb_client.get_subscription_receiver(topic, subscription, max_wait_time=wait_time)


async def fetch_and_process_messages(context: BDSContext, sb_client: ServiceBusClient) -> ServiceBusReceiver:

    receiver = get_sb_receiver(context, sb_client)

    msgs = await fetch_messages(context, receiver)

    for message in msgs:
        try:
            await process_message(context, message)
        except BulkDataServiceRuntimeError:
            context.logger.exception("process_message - Error processing message")
        finally:
            await receiver.complete_message(message)

    return receiver


async def fetch_messages(
    context: BDSContext, receiver: ServiceBusReceiver, num_messages: int = 5
) -> list[ServiceBusReceivedMessage]:

    wait_time = context.AZURE_SERVICE_BUS_WAIT_TIME

    return await receiver.receive_messages(max_wait_time=wait_time, max_message_count=num_messages)


async def process_message(context: BDSContext, msg: ServiceBusReceivedMessage):
    if msg.application_properties is not None and b"message_type" in msg.application_properties:
        message_type = msg.application_properties[b"message_type"].decode("utf-8")  # type: ignore[union-attr]
        await dispatch_message(context, message_type, json.loads(str(msg)))
    else:
        raise BulkDataServiceRuntimeError(
            "process_message - Message doesn't have the 'message_type' header in 'application_properties'"
        )


async def dispatch_message(context: BDSContext, message_type: str, message_payload: dict):

    message_date = get_timestamp_or_none(message_payload["message_date"])

    if message_date is None:
        raise BulkDataServiceRuntimeError(
            f"Recevied {message_type} message but 'message_date' is empty or badly formatted. "
            f"Message received: {json.dumps(message_payload)}"
        )

    match message_type:
        case "DATASET_CREATED":
            create_new_dataset(context, message_payload)

        case "DATASET_UPDATED":
            update_dataset(context, message_payload)

        case "DATASET_DELETED":
            delete_dataset(context, message_payload)

        case "REPORTING_ORG_CREATED":
            create_new_reporting_org(context, message_payload)

        case "REPORTING_ORG_UPDATED":
            update_reporting_org(context, message_payload)

        case "REPORTING_ORG_DELETED":
            delete_reporting_org(context, message_payload)

        case _:
            print("Received unknown message type: ")
            print(json.dumps(message_payload))


def create_new_reporting_org(context: BDSContext, message_payload: dict):
    reporting_org_db_record = get_reporting_org_in_bds(context, uuid.UUID(message_payload["reporting_org"]["id"]))

    if reporting_org_db_record is not None:
        raise BulkDataServiceRuntimeError(
            f"Received REPORTING_ORG_CREATED message for reporting_org ID {message_payload["reporting_org"]["id"]} "
            f"but a reporting_org already exists with that ID. "
            f"Message received: {json.dumps(message_payload)}"
        )

    new_reporting_org_db_record = convert_reporting_org_dto_to_reporting_org(message_payload["reporting_org"])

    new_reporting_org_db_record["registration_service_metadata_refreshed_datetime"] = get_timestamp_or_none(
        message_payload["message_date"]
    )

    with get_db_connection(context) as connection:
        insert_or_update_reporting_org(connection, new_reporting_org_db_record)
    context.logger.info(f"Created reporting org with ID {new_reporting_org_db_record["id"]}")


def update_reporting_org(context: BDSContext, message_payload: dict):
    reporting_org_db_record = get_reporting_org_in_bds(context, uuid.UUID(message_payload["reporting_org"]["id"]))

    if reporting_org_db_record is None:
        raise BulkDataServiceRuntimeError(
            f"Recevied REPORTING_ORG_UPDATED message for reporting org ID {message_payload["reporting_org"]["id"]} "
            f"but no reporting org with that ID exists. "
            f"Message received: {json.dumps(message_payload)}"
        )

    reporting_org_db_record = convert_reporting_org_dto_to_reporting_org(message_payload["reporting_org"])

    reporting_org_db_record["registration_service_metadata_refreshed_datetime"] = get_timestamp_or_none(
        message_payload["message_date"]
    )

    with get_db_connection(context) as connection:
        insert_or_update_reporting_org(connection, reporting_org_db_record)
    context.logger.info(f"Updated metadata for reporting org ID {reporting_org_db_record["id"]}")


def delete_reporting_org(context: BDSContext, message_payload: dict):

    reporting_org_db_record = get_reporting_org_in_bds(context, uuid.UUID(message_payload["reporting_org"]["id"]))

    if reporting_org_db_record is None:
        raise BulkDataServiceRuntimeError(
            f"Recevied REPORTING_ORG_DELETED message for reporting org ID {message_payload["reporting_org"]["id"]} "
            f"but no reporting org with that ID exists. "
            f"Message received: {json.dumps(message_payload)}"
        )

    with get_db_connection(context) as connection:
        remove_reporting_org_from_db(connection, message_payload["reporting_org"]["id"])

    context.logger.info(f"Deleted reporting org with ID {message_payload["reporting_org"]["id"]}")


def create_new_dataset(context: BDSContext, message_payload: dict):
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

    new_dataset_db_record = get_new_dataset_from_dataset_registration_dto("suitecrm-mq", message_payload["dataset"])

    new_dataset_db_record["registration_service_metadata_refreshed_datetime"] = get_timestamp_or_none(
        message_payload["message_date"]
    )

    with get_db_connection(context) as connection:
        insert_or_update_dataset(connection, new_dataset_db_record)
    context.logger.info(f"Created dataset with ID {new_dataset_db_record["id"]}")


def update_dataset(context: BDSContext, message_payload: dict):
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

    # get an updated dataset db record. we can't use the dataset MQ payload alone because
    # it only contains the registration fields (and those are the only ones we want to update)
    update_dataset_from_dataset_registration_dto("suitecrm-mq", dataset_db_record, message_payload["dataset"])

    dataset_db_record["registration_service_metadata_refreshed_datetime"] = get_timestamp_or_none(
        message_payload["message_date"]
    )

    with get_db_connection(context) as connection:
        update_dataset_registration_data(connection, dataset_db_record)
    context.logger.info(f"Updated metadata for dataset ID {dataset_db_record["id"]}")


def delete_dataset(context: BDSContext, message_payload: dict):

    dataset_db_record = get_dataset_in_bds(context, uuid.UUID(message_payload["dataset"]["id"]))

    if dataset_db_record is None:
        raise BulkDataServiceRuntimeError(
            f"Recevied DATASET_DELETED message for dataset ID {message_payload["dataset"]["id"]} "
            f"but no dataset with that ID exists. "
            f"Message received: {json.dumps(message_payload)}"
        )

    with get_db_connection(context) as connection:
        remove_dataset_from_db(connection, message_payload["dataset"]["id"])

    context.logger.info(f"Deleted dataset with ID {message_payload["dataset"]["id"]}")
