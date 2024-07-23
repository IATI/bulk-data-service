import os
import uuid

from azure.storage.blob import BlobServiceClient

from bulk_data_service.checker import checker_run
from bulk_data_service.zipper import get_local_pathname_dataset_xml, zipper_run
from helpers.helpers import get_and_clear_up_context  # noqa: F401
from utilities.azure import get_azure_blob_name, get_azure_container_name
from utilities.db import execute_scalar_db_query, get_datasets_in_bds


def test_remove_unregistered_dataset_from_memory(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    datasets_in_bds = get_datasets_in_bds(context)
    assert len(datasets_in_bds) == 0

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-02"
    checker_run(context, datasets_in_bds)

    datasets_in_bds = get_datasets_in_bds(context)
    assert len(datasets_in_bds) == 2

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01"
    checker_run(context, datasets_in_bds)

    assert len(datasets_in_bds) == 1

    # check the right dataset remains
    assert uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159") in datasets_in_bds


def test_remove_unregistered_dataset_from_db(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    datasets_in_bds = get_datasets_in_bds(context)

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-02"
    checker_run(context, datasets_in_bds)

    datasets_in_bds = get_datasets_in_bds(context)

    num_datasets_in_db = execute_scalar_db_query(context, "SELECT COUNT(*) from iati_datasets")
    assert num_datasets_in_db == 2

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01"
    checker_run(context, datasets_in_bds)

    num_datasets_in_db = execute_scalar_db_query(context, "SELECT COUNT(*) from iati_datasets")
    assert num_datasets_in_db == 1

    dataset_id_remaining = execute_scalar_db_query(context, "SELECT id from iati_datasets")
    assert dataset_id_remaining == uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")


def test_remove_unregistered_dataset_from_azure_blob(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    datasets_in_bds = get_datasets_in_bds(context)

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-02"

    checker_run(context, datasets_in_bds)

    datasets_in_bds = get_datasets_in_bds(context)

    num_datasets_in_db = execute_scalar_db_query(context, "SELECT COUNT(*) from iati_datasets")
    assert num_datasets_in_db == 2

    # save ref to the dataset which exists in `datasets-02` but not in `datasets-01`
    deleted_dataset = datasets_in_bds[uuid.UUID("90f4282f-9ac5-4385-804d-1a377f5b57be")]

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01"
    checker_run(context, datasets_in_bds)

    blob_service_client = \
        BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    xml_container_name = get_azure_container_name(context, "xml")
    zip_container_name = get_azure_container_name(context, "zip")

    xml_blob_name = get_azure_blob_name(deleted_dataset, "xml")
    zip_blob_name = get_azure_blob_name(deleted_dataset, "zip")

    xml_blob = blob_service_client.get_blob_client(xml_container_name, xml_blob_name)
    assert not xml_blob.exists()

    zip_blob = blob_service_client.get_blob_client(zip_container_name, zip_blob_name)
    assert not zip_blob.exists()

    blob_service_client.close()


def test_remove_unregistered_dataset_from_zip_working_dir(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    datasets_in_bds = get_datasets_in_bds(context)
    datasets_in_zip = {}

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-02"
    checker_run(context, datasets_in_bds)
    zipper_run(context, datasets_in_zip, datasets_in_bds)
    datasets_in_bds = get_datasets_in_bds(context)

    # save ref to the dataset which exists in `datasets-02` but not in `datasets-01`
    deleted_dataset = datasets_in_bds[uuid.UUID("90f4282f-9ac5-4385-804d-1a377f5b57be")]
    dataset_local_xml_filename = get_local_pathname_dataset_xml(context, deleted_dataset)

    assert os.path.exists(dataset_local_xml_filename) is True

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01"
    checker_run(context, datasets_in_bds)
    zipper_run(context, datasets_in_zip, datasets_in_bds)

    assert os.path.exists(dataset_local_xml_filename) is False


def test_remove_unregistered_dataset_with_no_download(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    datasets_in_bds = get_datasets_in_bds(context)

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-04"

    checker_run(context, datasets_in_bds)

    datasets_in_bds = get_datasets_in_bds(context)

    # sanity check
    num_datasets_in_db = execute_scalar_db_query(context, "SELECT COUNT(*) from iati_datasets")
    assert num_datasets_in_db == 2

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01"
    checker_run(context, datasets_in_bds)

    num_datasets_in_db = execute_scalar_db_query(context, "SELECT COUNT(*) from iati_datasets")
    assert num_datasets_in_db == 1

    dataset_id_remaining = execute_scalar_db_query(context, "SELECT id from iati_datasets")
    assert dataset_id_remaining == uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")
