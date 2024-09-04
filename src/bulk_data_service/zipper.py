import datetime
import os
import shutil
import time
import uuid

from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.core.exceptions import ResourceNotFoundError

from bulk_data_service.dataset_indexing import get_index_name
from utilities.azure import azure_download_blob, get_azure_blob_name, get_azure_container_name
from utilities.db import get_datasets_in_bds


def zipper(context: dict):

    datasets = get_datasets_in_bds(context)

    if context["single_run"]:
        zipper_run(context, {}, datasets)
    else:
        zipper_service_loop(context, {}, datasets)


def zipper_service_loop(context: dict, datasets_in_zip: dict[uuid.UUID, dict], datasets_in_bds: dict[uuid.UUID, dict]):

    while True:
        zipper_run(context, datasets_in_zip, datasets_in_bds)

        time.sleep(60 * 30)


def zipper_run(context: dict, datasets_in_zip: dict[uuid.UUID, dict], datasets_in_bds: dict[uuid.UUID, dict]):

    run_start = datetime.datetime.now(datetime.UTC)
    context["logger"].info("Zipper starting run")

    clean_working_dir(context, datasets_in_zip)

    datasets_with_downloads = {k: v for k, v in datasets_in_bds.items() if v["last_successful_download"] is not None}

    remove_datasets_without_dls_from_working_dir(context, datasets_in_zip, datasets_with_downloads)

    new_or_updated_datasets = {
        k: v
        for k, v in datasets_with_downloads.items()
        if k not in datasets_in_zip or datasets_in_zip[k]["hash"] != datasets_with_downloads[k]["hash"]
    }

    context["logger"].info(
        "Found {} datasets to ZIP. {} are new or updated and will be (re-)downloaded.".format(
            len(datasets_with_downloads), len(new_or_updated_datasets)
        )
    )

    download_new_or_updated_to_working_dir(context, new_or_updated_datasets)

    download_indices_to_working_dir(context)

    context["logger"].info("Zipping {} datasets.".format(len(datasets_with_downloads)))
    shutil.make_archive(
        get_big_zip_local_pathname_no_extension(context),
        "zip",
        root_dir=context["ZIP_WORKING_DIR"],
        base_dir="iati-data",
    )

    context["logger"].info("Uploading zipped datasets.")
    upload_zip_to_azure(context)

    run_end = datetime.datetime.now(datetime.UTC)
    context["logger"].info(
        "Zipper finished in {}. Datasets zipped: {}.".format(run_end - run_start, len(datasets_with_downloads))
    )

    datasets_in_zip.clear()
    datasets_in_zip.update(datasets_with_downloads)


def clean_working_dir(context: dict, datasets_in_zip: dict[uuid.UUID, dict]):
    if len(datasets_in_zip) == 0:
        context["logger"].info("First zip run of session, so deleting all XML " "files in the ZIP working dir.")
        shutil.rmtree("{}/{}".format(context["ZIP_WORKING_DIR"], "iati-data"), ignore_errors=True)


def remove_datasets_without_dls_from_working_dir(
    context: dict, datasets_in_zip: dict[uuid.UUID, dict], datasets_in_bds: dict[uuid.UUID, dict]
):
    datasets_removed = {k: v for k, v in datasets_in_zip.items() if v["id"] not in datasets_in_bds}

    for dataset in datasets_removed.values():
        delete_local_xml_from_zip_working_dir(context, dataset)


def upload_zip_to_azure(context: dict):
    az_blob_service = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    blob_client = az_blob_service.get_blob_client(
        context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_ZIP"], get_big_zip_full_filename(context)
    )

    content_settings = ContentSettings(content_type="zip")

    with open(get_big_zip_local_pathname(context), "rb") as data:
        blob_client.upload_blob(data, overwrite=True, content_settings=content_settings)

    az_blob_service.close()


def download_indices_to_working_dir(context: dict):
    az_blob_service = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    download_index_to_working_dir(context, az_blob_service, "minimal")

    download_index_to_working_dir(context, az_blob_service, "full")

    az_blob_service.close()


def download_index_to_working_dir(context: dict, az_blob_service: BlobServiceClient, index_type: str):

    index_filename = get_index_name(context, index_type)

    index_full_pathname = "{}/iati-data/{}".format(context["ZIP_WORKING_DIR"], index_filename)

    os.makedirs(os.path.dirname(index_full_pathname), exist_ok=True)

    azure_download_blob(az_blob_service, get_azure_container_name(context, "xml"), index_filename, index_full_pathname)


def download_new_or_updated_to_working_dir(context: dict, updated_datasets: dict[uuid.UUID, dict]):

    az_blob_service = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    xml_container_name = get_azure_container_name(context, "xml")

    for dataset in updated_datasets.values():
        filename = get_local_pathname_dataset_xml(context, dataset)

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        context["logger"].info("dataset id: {} - Downloading".format(dataset["id"]))

        try:
            azure_download_blob(az_blob_service, xml_container_name, get_azure_blob_name(dataset, "xml"), filename)
        except ResourceNotFoundError as e:
            context["logger"].error(
                "dataset id: {} - Failed to download from Azure: {}".format(dataset["id"], e).replace("\n", " ")
            )

    az_blob_service.close()


def get_big_zip_local_pathname_no_extension(context: dict) -> str:
    return "{}/{}".format(context["ZIP_WORKING_DIR"], get_big_zip_base_filename(context))


def get_big_zip_local_pathname(context: dict) -> str:
    return "{}/{}".format(context["ZIP_WORKING_DIR"], get_big_zip_full_filename(context))


def get_big_zip_base_filename(context: dict) -> str:
    return "iati-data"


def get_big_zip_full_filename(context: dict) -> str:
    return "{}.zip".format(get_big_zip_base_filename(context))


def get_local_pathname_dataset_xml(context: dict, dataset: dict) -> str:
    return "{}/iati-data/datasets/{}".format(context["ZIP_WORKING_DIR"], get_azure_blob_name(dataset, "xml"))


def delete_local_xml_from_zip_working_dir(context: dict, dataset: dict):
    dataset_local_xml = get_local_pathname_dataset_xml(context, dataset)

    if os.path.exists(dataset_local_xml):
        try:
            os.remove(dataset_local_xml)
        except FileNotFoundError as e:
            context["logger"].error(
                "dataset id: {} - Error removing local XML file from "
                "ZIP working dir. Details: {}.".format(dataset["id"], e)
            )
