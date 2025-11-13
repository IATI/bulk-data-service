import json
from datetime import datetime
from uuid import UUID

import pytest
import pytest_asyncio
from azure.servicebus import ServiceBusMessage
from azure.servicebus.aio import ServiceBusClient, ServiceBusReceiver

from bulk_data_service.registry_changes_processor import fetch_messages, get_sb_receiver, process_message
from config.bds_context import BDSContext
from helpers.mq_data_helpers import get_dataset_message_payload, get_reporting_org_message_payload
from utilities.exceptions import BulkDataServiceRuntimeError
from utilities.misc import get_timestamp


@pytest_asyncio.fixture
async def service_bus_context(get_and_clear_up_context):
    context = get_and_clear_up_context
    sbclient, sbreceiver = await initialise_mq(context)
    yield (sbclient, sbreceiver)
    await teardown_mq(context, sbclient, sbreceiver)


async def process_pending_messages(context: BDSContext, sbreceiver: ServiceBusReceiver, should_raise_exception: bool):
    msgs = await fetch_messages(context, sbreceiver, num_messages=1)

    for message in msgs:
        if should_raise_exception:
            with pytest.raises(BulkDataServiceRuntimeError):
                await process_message(context, message)
        else:
            await process_message(context, message)
        await sbreceiver.complete_message(message)


async def initialise_mq(context: BDSContext) -> tuple[ServiceBusClient, ServiceBusReceiver]:
    sbclient = ServiceBusClient.from_connection_string(context["AZURE_SERVICE_BUS_CONNECTION_STRING"])

    sbreceiver = get_sb_receiver(context, sbclient)

    await clear_messages_from_subscription(context, sbreceiver)

    return (sbclient, sbreceiver)


async def teardown_mq(context: BDSContext, sbclient: ServiceBusClient, sbreceiver: ServiceBusReceiver):
    await sbreceiver.close()
    await sbclient.close()


async def clear_messages_from_subscription(context: BDSContext, sbreceiver: ServiceBusReceiver):
    messages = await sbreceiver.receive_messages(50, max_wait_time=0.1)
    for message in messages:
        await sbreceiver.complete_message(message)


async def send_dataset_created_message(
    context: BDSContext, sbclient: ServiceBusClient, dataset_id: UUID, reporting_org_id: UUID
):

    dataset_db_record = {
        "id": dataset_id,
        "short_name": "test_foundation_a_new_dataset_from_mq",
        "licence_id": "uk-ogl",
        "source_url": "http://localhost/dataset-created-from-mq-via-tests.xml",
        "reporting_org_id": reporting_org_id,
        "reporting_org_short_name": "test_foundation_a",
    }

    return await generate_and_send_message(context, sbclient, "dataset", "created", dataset_db_record)


async def send_reporting_org_created_message(context: BDSContext, sbclient: ServiceBusClient, reporting_org_id: UUID):

    reporting_org_db_record = {
        "created_date": get_timestamp(),
        "default_licence_id": "cc-by",
        "data_portal_url": "https://www.example.org/data-portal",
        "description": "Eos ex saepe accusamus enim magnam omnis placeat doloremque qui.",
        "exclusions_policy_url": "https://www.example.org/exclusions-policy",
        "first_publication_date": get_timestamp(),
        "hq_country": "GB",
        "human_readable_name": "New MQ Test Foundation B",
        "id": reporting_org_id,
        "organisation_identifier": "TEST-GOV-CH-A-0123456",
        "organisation_type": "23",
        "region": "789",
        "registration_service_reporting_org_metadata": "",
        "reporting_source_type": "primary-source",
        "short_name": "new_mq_test_foundation_b",
        "website": "https://www.example.org",
    }

    # send and return test message
    return await generate_and_send_message(context, sbclient, "reporting_org", "created", reporting_org_db_record)


async def generate_and_send_message(
    context: BDSContext,
    sbclient: ServiceBusClient,
    record_type: str,
    update_type: str,
    data: dict,
):
    if record_type == "dataset":
        msg_payload = get_dataset_message_payload(data, update_type)
    else:
        msg_payload = get_reporting_org_message_payload(data, update_type)

    return await send_message(context, sbclient, msg_payload)


async def send_message(context: BDSContext, sbclient: ServiceBusClient, payload: dict) -> dict:

    payload_str = json.dumps(payload, indent=2)

    message = ServiceBusMessage(body=payload_str, application_properties={"message_type": payload["message_type"]})

    topic_sender = sbclient.get_topic_sender(topic_name=context["AZURE_SERVICE_BUS_REGISTRY_TOPIC_NAME"])

    await topic_sender.send_messages(message, timeout=2)

    await topic_sender.close()

    return payload
