import copy
from uuid import UUID

import pytest

from bulk_data_service.checker import checker_run
from helpers.assert_helpers import (
    assert_dataset_db_record_content_differs_dataset_mq_object,
    assert_dataset_db_record_equal_dataset_mq_object,
)
from helpers.azure_service_bus_helpers import (  # noqa: F401
    generate_and_send_message,
    process_pending_messages,
    send_dataset_created_message,
    service_bus_context,
)
from helpers.data_helpers import check_registration_service_refreshed_datetime
from helpers.helpers import get_and_clear_up_context  # noqa: F401
from utilities.db import get_dataset_in_bds, get_datasets_in_bds


@pytest.mark.asyncio
async def test_dataset_created_message_01_success(get_and_clear_up_context, service_bus_context):  # noqa: F811

    context = get_and_clear_up_context

    sbclient, sbreceiver = service_bus_context

    datasets_in_bds = {}

    checker_run(context, datasets_in_bds)

    dataset_id = UUID("6309e3d9-68a0-4538-a834-432d9f8d65ae")

    dataset_msg_payload = await send_dataset_created_message(
        context, sbclient, dataset_id, UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")
    )

    await process_pending_messages(context, sbreceiver, False)

    # now check results
    datasets_in_bds = get_datasets_in_bds(context)

    assert dataset_id in datasets_in_bds

    assert_dataset_db_record_equal_dataset_mq_object(datasets_in_bds[dataset_id], dataset_msg_payload["dataset"])

    check_registration_service_refreshed_datetime(datasets_in_bds[dataset_id])



@pytest.mark.asyncio
async def test_dataset_created_message_02_error_dataset_already_exists(
    get_and_clear_up_context, service_bus_context  # noqa: F811
):

    context = get_and_clear_up_context

    sbclient, sbreceiver = service_bus_context

    datasets_in_bds = {}

    checker_run(context, datasets_in_bds)

    dataset_id = UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")

    dataset_msg_payload = await send_dataset_created_message(
        context, sbclient, dataset_id, UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")
    )

    await process_pending_messages(context, sbreceiver, True)

    # check that the database hasn't been updated
    datasets_in_bds = get_datasets_in_bds(context)

    assert_dataset_db_record_content_differs_dataset_mq_object(
        datasets_in_bds[dataset_id], dataset_msg_payload["dataset"]
    )


@pytest.mark.asyncio
async def test_dataset_created_message_03_error_no_reporting_org(
    get_and_clear_up_context, service_bus_context  # noqa: F811
):

    context = get_and_clear_up_context

    sbclient, sbreceiver = service_bus_context

    datasets_in_bds = {}

    checker_run(context, datasets_in_bds)

    dataset_id = UUID("6309e3d9-68a0-4538-a834-432d9f8d65ae")

    await send_dataset_created_message(context, sbclient, dataset_id, UUID("00000000-1111-2222-3333-963e95493c1b"))

    await process_pending_messages(context, sbreceiver, True)

    # now check results
    datasets_in_bds = get_datasets_in_bds(context)

    assert dataset_id not in datasets_in_bds


@pytest.mark.asyncio
async def test_dataset_updated_message_01_success(get_and_clear_up_context, service_bus_context):  # noqa: F811

    context = get_and_clear_up_context

    sbclient, sbreceiver = service_bus_context

    datasets_in_bds = {}

    checker_run(context, datasets_in_bds)

    dataset_id = UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")

    datasets_in_bds[dataset_id]["short_name"] = "test_foundation_new_name_from_mq"
    datasets_in_bds[dataset_id]["licence_id"] = "gpl-3.0"
    datasets_in_bds[dataset_id]["source_url"] = "http://localhost:3000/data/url-from-mq.xml"

    # send test message
    dataset_msg_payload = await generate_and_send_message(
        context, sbclient, "dataset", "updated", datasets_in_bds[dataset_id]
    )

    await process_pending_messages(context, sbreceiver, False)

    # now check results
    dataset_from_db = get_dataset_in_bds(context, dataset_id)

    assert dataset_from_db is not None

    assert_dataset_db_record_equal_dataset_mq_object(dataset_from_db, dataset_msg_payload["dataset"])


@pytest.mark.asyncio
async def test_dataset_updated_message_02_error_unknown_dataset(
    get_and_clear_up_context, service_bus_context  # noqa: F811
):

    context = get_and_clear_up_context

    sbclient, sbreceiver = service_bus_context

    datasets_in_bds = {}

    checker_run(context, datasets_in_bds)

    dataset_id = UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")
    non_existent_dataset_id = UUID("00000000-1111-2222-3333-0123456789ab")

    # create a dataset record with a non-existent ID to attempt to update
    # do this just by changing the ID on an existing DB record, so we can reuse
    # the payload generation function. safe to do as we're not doing anything
    # further with this object
    dataset_db_record = datasets_in_bds[dataset_id]
    dataset_db_record["id"] = non_existent_dataset_id

    # send test message
    await generate_and_send_message(context, sbclient, "dataset", "updated", dataset_db_record)

    await process_pending_messages(context, sbreceiver, True)

    # now check results
    dataset_from_db = get_dataset_in_bds(context, non_existent_dataset_id)

    assert dataset_from_db is None


@pytest.mark.asyncio
async def test_dataset_updated_message_03_error_unknown_reporting_org(
    get_and_clear_up_context, service_bus_context  # noqa: F811
):

    context = get_and_clear_up_context

    sbclient, sbreceiver = service_bus_context

    datasets_in_bds = {}

    checker_run(context, datasets_in_bds)

    dataset_id = UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")
    non_existent_repoting_org_id = UUID("00000000-1111-2222-3333-0123456789ab")

    # create a dataset record with a non-existent reporting_org ID to attempt to update
    dataset_db_record = copy.deepcopy(datasets_in_bds[dataset_id])
    dataset_db_record["short_name"] = "test_foundation_a_new_dataset_name"
    dataset_db_record["reporting_org_id"] = non_existent_repoting_org_id

    # send test message
    await generate_and_send_message(context, sbclient, "dataset", "updated", dataset_db_record)

    await process_pending_messages(context, sbreceiver, True)

    # check that the dataset in the databse is the same as that first read from the database
    # that is, the dataset record should not have the short_name or reporting_org_id
    # fields updated because there is no reporting_org with 'reporting_org_id' in the DB
    # and we shouldn't be able to update with reporting_orgs that don't exist.
    dataset_from_db = get_dataset_in_bds(context, dataset_id)

    assert dataset_from_db is not None

    assert dataset_from_db == datasets_in_bds[dataset_id]


@pytest.mark.asyncio
async def test_dataset_updated_message_04_error_reporting_org_short_name_mismatch(
    get_and_clear_up_context, service_bus_context  # noqa: F811
):

    context = get_and_clear_up_context

    sbclient, sbreceiver = service_bus_context

    datasets_in_bds = {}

    checker_run(context, datasets_in_bds)

    dataset_id = UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")

    # create a dataset record with a non-existent reporting_org ID to attempt to update
    dataset_db_record = copy.deepcopy(datasets_in_bds[dataset_id])
    dataset_db_record["short_name"] = "test_foundation_NEW_NAME_a_new_dataset_name"
    dataset_db_record["reporting_org_short_name"] = "test_foundation_NEW_NAME"

    # send test message
    await generate_and_send_message(context, sbclient, "dataset", "updated", dataset_db_record)

    await process_pending_messages(context, sbreceiver, True)

    # check that the dataset in the databse is the same as that first read from the database
    # that is, the dataset record should not have the short_name or reporting_org_short_name
    # fields updated because 'reporting_org_short_name' doesn't match the DB record for the
    # reporting org ID, and the DATASET_UPDATED message should not be a way to update the
    # name of the reporting org.
    dataset_from_db = get_dataset_in_bds(context, dataset_id)

    assert dataset_from_db is not None

    assert dataset_from_db == datasets_in_bds[dataset_id]


@pytest.mark.asyncio
async def test_dataset_deleted_message_01_success(get_and_clear_up_context, service_bus_context):  # noqa: F811

    context = get_and_clear_up_context

    sbclient, sbreceiver = service_bus_context

    datasets_in_bds = {}

    checker_run(context, datasets_in_bds)

    dataset_id = UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")

    # send test message
    await generate_and_send_message(context, sbclient, "dataset", "deleted", datasets_in_bds[dataset_id])

    await process_pending_messages(context, sbreceiver, False)

    # check that the dataset has been deleted from the database
    dataset_from_db = get_dataset_in_bds(context, dataset_id)

    assert dataset_from_db is None


@pytest.mark.asyncio
async def test_dataset_deleted_message_02_error_unknown_dataset(
    get_and_clear_up_context, service_bus_context  # noqa: F811
):

    context = get_and_clear_up_context

    sbclient, sbreceiver = service_bus_context

    datasets_in_bds = {}

    checker_run(context, datasets_in_bds)

    dataset_id = UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")
    non_existent_dataset_id = UUID("00000000-1111-2222-3333-0123456789ab")

    # modify dataset record with a non-existent ID and then send request to
    # delete this non-existent dataset. safe to do as we're not doing anything
    # further with this object
    dataset_db_record = datasets_in_bds[dataset_id]
    dataset_db_record["id"] = non_existent_dataset_id

    # send test message
    await generate_and_send_message(context, sbclient, "dataset", "deleted", dataset_db_record)

    await process_pending_messages(context, sbreceiver, True)
