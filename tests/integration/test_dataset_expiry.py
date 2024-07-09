import uuid
from datetime import timedelta

from azure.storage.blob import BlobServiceClient

from bulk_data_service.checker import checker_run, zipper_run
from helpers.helpers import get_and_clear_up_context  # noqa: F401
from helpers.helpers import get_number_xml_files_in_working_dir
from utilities.azure import get_azure_blob_name, get_azure_container_name
from utilities.db import get_datasets_in_bds


def test_dataset_expiry_after_72_hours_failed_downloads(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    max_hours = int(context["REMOVE_LAST_GOOD_DOWNLOAD_AFTER_FAILING_HOURS"])

    datasets_in_bds = get_datasets_in_bds(context)
    datasets_in_zip = {}

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01"
    checker_run(context, datasets_in_bds)
    zipper_run(context, datasets_in_zip, datasets_in_bds)

    assert get_number_xml_files_in_working_dir(context) == 1

    dataset = datasets_in_bds[uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")]
    dataset["last_successful_download"] = (dataset["last_successful_download"]
                                           - timedelta(hours=max_hours + 2))

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-03"
    checker_run(context, datasets_in_bds)
    zipper_run(context, datasets_in_zip, datasets_in_bds)

    dataset = datasets_in_bds[uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")]

    assert len(datasets_in_bds) == 1
    assert dataset["last_successful_download"] is None

    blob_service_client = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    xml_container_name = get_azure_container_name(context, "xml")
    zip_container_name = get_azure_container_name(context, "zip")

    xml_blob_name = get_azure_blob_name(dataset, "xml")
    zip_blob_name = get_azure_blob_name(dataset, "zip")

    xml_blob = blob_service_client.get_blob_client(xml_container_name, xml_blob_name)
    assert not xml_blob.exists()

    zip_blob = blob_service_client.get_blob_client(zip_container_name, zip_blob_name)
    assert not zip_blob.exists()

    blob_service_client.close()

    assert get_number_xml_files_in_working_dir(context) == 0
