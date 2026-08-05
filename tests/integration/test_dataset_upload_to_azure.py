import uuid

import pytest
from azure.storage.blob import BlobServiceClient

from bulk_data_service.checker import checker_run
from helpers.helpers import (  # noqa: F401
    download_dataset_from_azure,
    get_and_clear_up_context,
    get_file_contents,
    unzip_from_buffer,
)
from utilities.azure import get_azure_blob_name, get_azure_container_name


@pytest.mark.parametrize(
    "artifact_filename",
    [
        ("test_foundation_a-dataset-001.xml"),
        ("test_foundation_a-dataset-001-utf-8-with-bom"),
        ("test_foundation_a-dataset-001-utf-16-le"),
        ("test_foundation_a-dataset-001-utf-16-be"),
        ("test_foundation_a-dataset-001-utf-32-le"),
        ("test_foundation_a-dataset-001-utf-32-be"),
        ("test_foundation_a-dataset-001-iso-8859-1"),
    ],
)
def test_valid_dataset_azure_xml_upload(get_and_clear_up_context, artifact_filename):  # noqa: F811

    context = get_and_clear_up_context

    dataset_id = uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")
    context["DATA_REGISTRY_BASE_URL"] = (
        "http://localhost:3000/ckan-registration/datasets-01-1-dataset/http%3A%2F%2Flocalhost%3A3000%2Fdata%2F{}"
    ).format(artifact_filename)
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    dataset_contents_from_disk = get_file_contents("tests/artifacts/iati-xml-files/{}".format(artifact_filename))

    dataset_contents_from_azure = download_dataset_from_azure(context, datasets_in_bds[dataset_id], "xml")

    assert dataset_contents_from_disk == dataset_contents_from_azure


@pytest.mark.parametrize(
    "artifact_filename",
    [
        ("test_foundation_a-dataset-001.xml"),
        ("test_foundation_a-dataset-001-utf-8-with-bom"),
        ("test_foundation_a-dataset-001-utf-16-le"),
        ("test_foundation_a-dataset-001-utf-16-be"),
        ("test_foundation_a-dataset-001-utf-32-le"),
        ("test_foundation_a-dataset-001-utf-32-be"),
        ("test_foundation_a-dataset-001-iso-8859-1"),
    ],
)
def test_valid_dataset_azure_zip_upload(get_and_clear_up_context, artifact_filename):  # noqa: F811

    context = get_and_clear_up_context

    dataset_id = uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")
    context["DATA_REGISTRY_BASE_URL"] = (
        "http://localhost:3000/ckan-registration/datasets-01-1-dataset/http%3A%2F%2Flocalhost%3A3000%2Fdata%2F{}"
    ).format(artifact_filename)
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    dataset_contents_from_disk = get_file_contents("tests/artifacts/iati-xml-files/{}".format(artifact_filename))

    dataset_contents_from_azure_zipped = download_dataset_from_azure(context, datasets_in_bds[dataset_id], "zip")

    dataset_contents_from_azure = unzip_from_buffer(
        "{}.xml".format(datasets_in_bds[dataset_id]["short_name"]), dataset_contents_from_azure_zipped
    )

    assert dataset_contents_from_disk == dataset_contents_from_azure


@pytest.mark.parametrize(
    "artifact_filename",
    [
        ("test_foundation_a-dataset-empty.xml"),
        ("test_foundation_a-dataset-html.xml"),
        ("test_foundation_a-dataset.pdf"),
    ],
)
def test_invalid_dataset_no_azure_xml_upload(get_and_clear_up_context, artifact_filename):  # noqa: F811

    context = get_and_clear_up_context

    dataset_id = uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")
    context["DATA_REGISTRY_BASE_URL"] = (
        "http://localhost:3000/ckan-registration/datasets-01-1-dataset/http%3A%2F%2Flocalhost%3A3000%2Fdata%2F{}"
    ).format(artifact_filename)
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    blob_service_client = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])
    container_name = get_azure_container_name(context, "zip")
    blob_name = get_azure_blob_name(datasets_in_bds[dataset_id], "xml")
    blob_client = blob_service_client.get_blob_client(container_name, blob_name)
    assert blob_client.exists() is False
