import asyncio
import json
import uuid
from datetime import datetime
from typing import Callable

import pytest
from azure.servicebus import ServiceBusMessage
from azure.servicebus.aio import ServiceBusClient, ServiceBusReceiver

from bulk_data_service.registry_changes_processor import fetch_messages, get_sb_receiver, process_message
from utilities.exceptions import BulkDataServiceRuntimeError
from utilities.misc import get_timestamp


async def process_pending_messages(context: dict, sbreceiver: ServiceBusReceiver, should_raise_exception: bool):
    msgs = await fetch_messages(context, sbreceiver, num_messages=1)

    for message in msgs:
        if should_raise_exception:
            with pytest.raises(BulkDataServiceRuntimeError):
                await process_message(context, message)
        else:
            await process_message(context, message)
        await sbreceiver.complete_message(message)



def assert_dataset_db_records_equal(dataset_db_record_1: dict, dataset_db_record_2: dict):
    assert dataset_db_record_1["id"] == dataset_db_record_2["id"]
    assert dataset_db_record_1["short_name"] == dataset_db_record_2["short_name"]
    assert dataset_db_record_1["licence_id"] == dataset_db_record_2["licence_id"]
    assert dataset_db_record_1["source_url"] == dataset_db_record_2["url"]
    assert dataset_db_record_1["reporting_org_id"] == dataset_db_record_2["reporting_org_id"]
    assert dataset_db_record_1["reporting_org_short_name"] == dataset_db_record_2["reporting_org_short_name"]


def assert_dataset_db_record_equal_dataset_mq_object(dataset_db_record: dict, dataset_mq_object: dict[str, str]):
    assert dataset_db_record["id"] == uuid.UUID(dataset_mq_object["id"])
    assert dataset_db_record["short_name"] == dataset_mq_object["short_name"]
    assert dataset_db_record["licence_id"] == dataset_mq_object["licence_id"]
    assert dataset_db_record["source_url"] == dataset_mq_object["url"]
    assert dataset_db_record["reporting_org_id"] == uuid.UUID(dataset_mq_object["reporting_org_id"])
    assert dataset_db_record["reporting_org_short_name"] == dataset_mq_object["reporting_org_short_name"]


def assert_dataset_db_record_content_differs_dataset_mq_object(dataset_db_record: dict, dataset_mq_object: dict[str, str]):
    assert dataset_db_record["short_name"] != dataset_mq_object["short_name"]
    assert dataset_db_record["licence_id"] != dataset_mq_object["licence_id"]
    assert dataset_db_record["source_url"] != dataset_mq_object["url"]


def generate_dataset_deleted_payload(dataset: dict) -> dict:
    return {
        "message_type": f"DATASET_DELETED",
        "message_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dataset": {
            "id": str(dataset["id"]),
        },
    }


def generate_dataset_created_updated_payload(dataset_db_record: dict, update_type: str) -> dict:
    return {
        "message_type": f"DATASET_{update_type.upper()}",
        "message_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dataset": {
            "id": str(dataset_db_record["id"]),
            "short_name": dataset_db_record["short_name"],
            "source_type": "primary-source",  # hard coded because BDS doesn't use it
            "licence_id": dataset_db_record["licence_id"],
            "url": dataset_db_record["source_url"],
            "last_url_update_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "last_metadata_update_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "reporting_org_id": str(dataset_db_record["reporting_org_id"]),
            "reporting_org_short_name": dataset_db_record["reporting_org_short_name"],
        },
    }


async def initialise_mq(context: dict) -> tuple[ServiceBusClient, ServiceBusReceiver]:
    sbclient = ServiceBusClient.from_connection_string(context["AZURE_SERVICE_BUS_CONNECTION_STRING"])

    sbreceiver = get_sb_receiver(context, sbclient)

    await clear_messages_from_subscription(context, sbreceiver)

    return (sbclient, sbreceiver)


async def teardown_mq(context: dict, sbclient: ServiceBusClient, sbreceiver: ServiceBusReceiver):
    await sbreceiver.close()
    await sbclient.close()


async def clear_messages_from_subscription(context: dict, sbreceiver: ServiceBusReceiver):
    messages = await sbreceiver.receive_messages(50, max_wait_time=0.1)
    for message in messages:
        await sbreceiver.complete_message(message)


async def send_dataset_created_message(
    context: dict, sb_client: ServiceBusClient, dataset_id: str, reporting_org_id: str
):

    dataset_data = {
        "id": dataset_id,
        "short_name": "test_foundation_a_new_dataset_from_mq",
        "licence_id": "uk-ogl",
        "source_url": "http://localhost/dataset-created-from-mq-via-tests.xml",
        "reporting_org_id": reporting_org_id,
        "reporting_org_short_name": "test_foundation_a",
    }

    # send and return test message
    return await send_dataset_message(context, sb_client, dataset_data, "created")


async def send_dataset_message(
    context: dict,
    sb_client: ServiceBusClient,
    dataset: dict,
    update_type: str,
) -> dict:

    if update_type == "deleted":
        msg_payload = generate_dataset_deleted_payload(dataset)
    else:
        msg_payload = generate_dataset_created_updated_payload(dataset, update_type)

    msg_payload_str = json.dumps(msg_payload, indent=2)

    message = ServiceBusMessage(
        body=msg_payload_str, application_properties={"message_type": msg_payload["message_type"]}
    )

    topic_sender = sb_client.get_topic_sender(topic_name=context["AZURE_SERVICE_BUS_REGISTRY_TOPIC_NAME"])

    await topic_sender.send_messages(message, timeout=0.1)

    await topic_sender.close()

    return msg_payload
