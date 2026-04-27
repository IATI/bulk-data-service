import uuid
from unittest.mock import Mock

import pytest
from azure.storage.blob import BlobServiceClient

from bulk_data_service.checker import checker_run
from bulk_data_service.dataset_indexing import get_dataset_index_name, get_reporting_org_index_name
from helpers.assert_helpers import assert_reporting_org_plain_record_equal_db_record
from helpers.data_helpers import (
    check_index_common_last_known_good_fields,
    check_index_most_recent_fields,
    check_index_registration_fields,
)
from helpers.helpers import download_index_from_azure, get_and_clear_up_context  # noqa: F401
from utilities.azure import get_azure_container_name
from utilities.db import get_reporting_orgs_in_bds
from utilities.misc import find_object_by_key


def test_indices_uploaded_to_blob_storage(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-01-1-dataset"
    checker_run(context, {})

    blob_service_client = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    zip_container_name = get_azure_container_name(context, "zip")

    dataset_index_minimal_name = get_dataset_index_name(context, "minimal")
    dataset_index_full_name = get_dataset_index_name(context, "full")
    reporting_org_index_name = get_reporting_org_index_name(context)

    minimal_blob = blob_service_client.get_blob_client(zip_container_name, dataset_index_minimal_name)
    assert minimal_blob.exists()

    reporting_org_blob = blob_service_client.get_blob_client(zip_container_name, dataset_index_full_name)
    assert reporting_org_blob.exists()

    reporting_org_blob = blob_service_client.get_blob_client(zip_container_name, reporting_org_index_name)
    assert reporting_org_blob.exists()

    blob_service_client.close()


@pytest.mark.parametrize(
    "index_name",
    [
        get_dataset_index_name(Mock(), "minimal"),
        get_dataset_index_name(Mock(), "full"),
        get_reporting_org_index_name(Mock()),
    ],
)
def test_index_created_field_is_generated_for_indices(get_and_clear_up_context, index_name):  # noqa: F811
    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-01-1-dataset"
    checker_run(context, {})

    index_from_azure = download_index_from_azure(context, index_name)

    assert index_from_azure["index_created"] is not None
    assert index_from_azure["index_created_unix_timestamp"] is not None


def test_index_created_fields_in_dataset_indices_have_same_value(get_and_clear_up_context):  # noqa: F811
    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-01-1-dataset"
    checker_run(context, {})

    minimal_index = download_index_from_azure(context, get_dataset_index_name(context, "minimal"))

    full_index = download_index_from_azure(context, get_dataset_index_name(context, "full"))

    assert minimal_index["index_created_unix_timestamp"] == full_index["index_created_unix_timestamp"]


def test_index_created_fields_in_dataset_reporting_org_indices_have_same_value(get_and_clear_up_context):  # noqa: F811
    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-01-1-dataset"
    checker_run(context, {})

    minimal_index = download_index_from_azure(context, get_dataset_index_name(context, "minimal"))

    reporting_org_index = download_index_from_azure(context, get_reporting_org_index_name(context))

    assert minimal_index["index_created_unix_timestamp"] == reporting_org_index["index_created_unix_timestamp"]


def test_creation_of_entry_in_reporting_org_index(get_and_clear_up_context):  # noqa: F811
    context = get_and_clear_up_context

    context["DATA_REGISTRY_PUBLISHER_METADATA_URL"] = (
        "http://localhost:3000/ckan-registration/reporting-orgs-01-four-orgs"
    )
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-01-1-dataset"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    reporting_orgs_in_bds = get_reporting_orgs_in_bds(context)

    reporting_org_index = download_index_from_azure(context, get_reporting_org_index_name(context))

    reporting_org = reporting_orgs_in_bds[uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")]

    reporting_org_index_item = find_object_by_key(
        reporting_org_index["reporting_orgs"], "short_name", reporting_org["short_name"]
    )

    assert reporting_org_index_item is not None

    assert_reporting_org_plain_record_equal_db_record(reporting_org_index_item, reporting_org)


@pytest.mark.parametrize(
    "dataset_filename",
    [
        ("test_foundation_a-dataset-001.xml"),
        ("test_foundation_a-dataset-empty.xml"),
        ("test_foundation_a-dataset-html.xml"),
        ("test_foundation_a-dataset.pdf"),
        ("test_foundation_a-dataset-404.xml"),
    ],
)
def test_creation_of_dataset_entry_in_full_index(get_and_clear_up_context, dataset_filename):  # noqa: F811
    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = (
        "http://localhost:3000/ckan-registration/datasets-01-1-dataset/"
        "http%3A%2F%2Flocalhost%3A3000%2Fdata%2F{}".format(dataset_filename)
    )
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    full_index = download_index_from_azure(context, get_dataset_index_name(context, "full"))

    dataset = datasets_in_bds[uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")]

    dataset_index_item = find_object_by_key(full_index["datasets"], "short_name", dataset["short_name"])

    assert dataset_index_item is not None

    check_index_registration_fields(dataset, dataset_index_item)

    check_index_most_recent_fields(context, "head", dataset, dataset_index_item)

    check_index_most_recent_fields(context, "get", dataset, dataset_index_item)

    check_index_common_last_known_good_fields(context, dataset, dataset_index_item)


@pytest.mark.parametrize(
    "dataset_filename",
    [
        ("test_foundation_a-dataset-001.xml"),
        ("test_foundation_a-dataset-empty.xml"),
        ("test_foundation_a-dataset-html.xml"),
        ("test_foundation_a-dataset.pdf"),
        ("test_foundation_a-dataset-404.xml"),
    ],
)
def test_creation_of_dataset_entry_in_minimal_index(get_and_clear_up_context, dataset_filename):  # noqa: F811
    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = (
        "http://localhost:3000/ckan-registration/datasets-01-1-dataset/"
        "http%3A%2F%2Flocalhost%3A3000%2Fdata%2F{}".format(dataset_filename)
    )
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    minimal_index = download_index_from_azure(context, get_dataset_index_name(context, "minimal"))

    dataset = datasets_in_bds[uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")]

    dataset_index_item = find_object_by_key(minimal_index["datasets"], "short_name", dataset["short_name"])

    assert dataset_index_item is not None

    check_index_registration_fields(dataset, dataset_index_item)

    assert "most_recent_head_attempt" not in dataset_index_item

    assert "most_recent_get_attempt" not in dataset_index_item

    check_index_common_last_known_good_fields(context, dataset, dataset_index_item)
