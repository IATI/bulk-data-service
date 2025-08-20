import uuid

import pytest

from bulk_data_service.checker import checker_run
from helpers.assert_helpers import (
    assert_reporting_org_db_record_content_differs_reporting_org_mq_object,
    assert_reporting_org_db_record_equal_reporting_org_mq_object,
)
from helpers.azure_service_bus_helpers import (  # noqa: F401
    generate_and_send_message,
    process_pending_messages,
    send_reporting_org_created_message,
    service_bus_context,
)
from helpers.helpers import get_and_clear_up_context  # noqa: F401
from utilities.db import get_reporting_org_in_bds, get_reporting_orgs_in_bds


@pytest.mark.asyncio
async def test_reporting_org_created_message_01_success(get_and_clear_up_context, service_bus_context):  # noqa: F811

    context = get_and_clear_up_context

    sbclient, sbreceiver = service_bus_context

    # the ID for the new reporting org
    reporting_org_id = uuid.UUID("48b3333e-66e4-11f0-9dcb-f724703f1a70")

    reporting_orgs_in_bds = get_reporting_orgs_in_bds(context)

    assert reporting_org_id not in reporting_orgs_in_bds

    reporting_org_msg_payload = await send_reporting_org_created_message(context, sbclient, reporting_org_id)

    await process_pending_messages(context, sbreceiver, False)

    # now check results
    reporting_orgs_in_bds = get_reporting_orgs_in_bds(context)

    assert reporting_org_id in reporting_orgs_in_bds

    assert_reporting_org_db_record_equal_reporting_org_mq_object(
        reporting_orgs_in_bds[reporting_org_id], reporting_org_msg_payload["reporting_org"]
    )


@pytest.mark.asyncio
async def test_reporting_org_created_message_02_error_reporting_org_already_exists(
    get_and_clear_up_context, service_bus_context  # noqa: F811
):

    context = get_and_clear_up_context

    sbclient, sbreceiver = service_bus_context

    checker_run(context, {})

    # the ID for the new reporting org which matches the existing reporting org
    reporting_org_id = uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")

    reporting_org_msg_payload = await send_reporting_org_created_message(context, sbclient, reporting_org_id)

    await process_pending_messages(context, sbreceiver, True)

    # now check results
    reporting_orgs_in_bds = get_reporting_orgs_in_bds(context)

    assert_reporting_org_db_record_content_differs_reporting_org_mq_object(
        reporting_orgs_in_bds[reporting_org_id], reporting_org_msg_payload["reporting_org"]
    )


@pytest.mark.asyncio
async def test_reporting_org_updated_message_01_success(get_and_clear_up_context, service_bus_context):  # noqa: F811

    context = get_and_clear_up_context

    sbclient, sbreceiver = service_bus_context

    checker_run(context, {})

    reporting_org_id = uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")

    reporting_orgs_in_bds = get_reporting_orgs_in_bds(context)

    reporting_orgs_in_bds[reporting_org_id]["short_name"] = "test_foundation_b_new_name_from_mq"
    reporting_orgs_in_bds[reporting_org_id]["human_readable_name"] = "Test Foundation B - Updated Name"
    reporting_orgs_in_bds[reporting_org_id]["iati_identifier"] = "TEST-GOV-2-NEW"

    # send test message
    reporting_org_msg_payload = await generate_and_send_message(
        context, sbclient, "reporting_org", "updated", reporting_orgs_in_bds[reporting_org_id]
    )

    await process_pending_messages(context, sbreceiver, False)

    # now check results
    reporting_org_from_db = get_reporting_org_in_bds(context, reporting_org_id)

    assert reporting_org_from_db is not None

    assert_reporting_org_db_record_equal_reporting_org_mq_object(
        reporting_org_from_db, reporting_org_msg_payload["reporting_org"]
    )


@pytest.mark.asyncio
async def test_reporting_org_updated_message_02_error_unknown_reporting_org(
    get_and_clear_up_context, service_bus_context  # noqa: F811
):

    context = get_and_clear_up_context

    sbclient, sbreceiver = service_bus_context

    checker_run(context, {})

    reporting_org_id = uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")
    non_existent_reporting_org_id = uuid.UUID("00000000-1111-2222-3333-0123456789ab")

    reporting_orgs_in_bds = get_reporting_orgs_in_bds(context)

    # use one of the existing reporting orgs but give it a non-existent ID
    reporting_org_db_record = reporting_orgs_in_bds[reporting_org_id]
    reporting_org_db_record["id"] = non_existent_reporting_org_id

    # send test message
    await generate_and_send_message(context, sbclient, "reporting_org", "updated", reporting_org_db_record)

    await process_pending_messages(context, sbreceiver, True)

    # now check results
    reporting_org_from_db = get_reporting_org_in_bds(context, non_existent_reporting_org_id)

    assert reporting_org_from_db is None


@pytest.mark.asyncio
async def test_reporting_org_deleted_message_01_success(get_and_clear_up_context, service_bus_context):  # noqa: F811

    context = get_and_clear_up_context

    sbclient, sbreceiver = service_bus_context

    checker_run(context, {})

    # this reporting org has no datasets in the test setup so straightforward test
    reporting_org_id = uuid.UUID("31ffc713-cba9-4af9-a71e-9306d00c11e8")

    reporting_org_to_delete = get_reporting_org_in_bds(context, reporting_org_id)

    assert reporting_org_to_delete is not None

    # send test message
    await generate_and_send_message(context, sbclient, "reporting_org", "deleted", reporting_org_to_delete)

    await process_pending_messages(context, sbreceiver, False)

    # check that the dataset has been deleted from the database
    reporting_org_from_db = get_reporting_org_in_bds(context, reporting_org_id)

    assert reporting_org_from_db is None


@pytest.mark.asyncio
async def test_reporting_org_deleted_message_02_success_associated_datasets(
    get_and_clear_up_context, service_bus_context  # noqa: F811
):

    context = get_and_clear_up_context

    sbclient, sbreceiver = service_bus_context

    checker_run(context, {})

    # this reporting org has datasets in the test setup so we'll check those are deleted too
    reporting_org_id = uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")

    reporting_org_to_delete = get_reporting_org_in_bds(context, reporting_org_id)

    assert reporting_org_to_delete is not None

    # send test message
    await generate_and_send_message(context, sbclient, "reporting_org", "deleted", reporting_org_to_delete)

    await process_pending_messages(context, sbreceiver, False)

    # check that the dataset has been deleted from the database
    reporting_org_from_db = get_reporting_org_in_bds(context, reporting_org_id)

    assert reporting_org_from_db is None


@pytest.mark.asyncio
async def test_reporting_org_deleted_message_03_error_unknown_reporting_org(
    get_and_clear_up_context, service_bus_context  # noqa: F811
):

    context = get_and_clear_up_context

    sbclient, sbreceiver = service_bus_context

    checker_run(context, {})

    # this reporting org has no datasets in the test setup so straightforward test
    reporting_org_id = uuid.UUID("31ffc713-cba9-4af9-a71e-9306d00c11e8")
    non_existent_reporting_org_id = uuid.UUID("00000000-1111-2222-a71e-9306d00c11e8")

    reporting_org_to_delete = get_reporting_org_in_bds(context, reporting_org_id)

    assert reporting_org_to_delete is not None

    reporting_org_to_delete["id"] = non_existent_reporting_org_id

    # send test message
    await generate_and_send_message(context, sbclient, "reporting_org", "deleted", reporting_org_to_delete)

    await process_pending_messages(context, sbreceiver, True)
