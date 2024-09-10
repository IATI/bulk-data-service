import datetime
import os
import shutil
import time
import uuid

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient

from bulk_data_service.dataset_indexing import get_index_name
from bulk_data_service.zippers import CodeforIATILegacyZipper, IATIBulkDataServiceZipper
from utilities.azure import azure_download_blob, get_azure_blob_name, get_azure_container_name
from utilities.db import get_datasets_in_bds


def zipper(context: dict):

    datasets = get_datasets_in_bds(context)

    if context["single_run"]:
        zipper_run(context, {}, datasets)
    else:
        zipper_service_loop(context, {}, datasets)


def zipper_service_loop(
    context: dict, datasets_in_working_dir: dict[uuid.UUID, dict], datasets_in_bds: dict[uuid.UUID, dict]
):

    while True:
        zipper_run(context, datasets_in_working_dir, datasets_in_bds)

        time.sleep(60 * 30)


def zipper_run(context: dict, datasets_in_working_dir: dict[uuid.UUID, dict], datasets_in_bds: dict[uuid.UUID, dict]):

    run_start = datetime.datetime.now(datetime.UTC)
    context["logger"].info("Zipper run starting")

    setup_working_dir_with_downloaded_datasets(context, datasets_in_working_dir, datasets_in_bds)

    zip_creators = [
        IATIBulkDataServiceZipper(
            context, "{}-1".format(context["ZIP_WORKING_DIR"]), datasets_in_working_dir, datasets_in_bds
        ),
        CodeforIATILegacyZipper(
            context, "{}-2".format(context["ZIP_WORKING_DIR"]), datasets_in_working_dir, datasets_in_bds
        ),
    ]

    for zip_creator in zip_creators:

        if os.path.exists(zip_creator.zip_working_dir):
            shutil.rmtree(zip_creator.zip_working_dir)
        shutil.copytree(context["ZIP_WORKING_DIR"], zip_creator.zip_working_dir)

        zip_creator.prepare()

        zip_creator.zip()

        zip_creator.upload()

    run_end = datetime.datetime.now(datetime.UTC)
    context["logger"].info("Zipper run finished in {}.".format(run_end - run_start))


def setup_working_dir_with_downloaded_datasets(
    context: dict, datasets_in_working_dir: dict[uuid.UUID, dict], datasets_in_bds: dict[uuid.UUID, dict]
):

    clean_working_dir(context, datasets_in_working_dir)

    datasets_with_downloads = {k: v for k, v in datasets_in_bds.items() if v["last_successful_download"] is not None}

    remove_datasets_without_dls_from_working_dir(context, datasets_in_working_dir, datasets_with_downloads)

    new_or_updated_datasets = {
        k: v
        for k, v in datasets_with_downloads.items()
        if k not in datasets_in_working_dir or datasets_in_working_dir[k]["hash"] != datasets_with_downloads[k]["hash"]
    }

    context["logger"].info(
        "Found {} datasets with downloads. "
        "{} are new or updated and will be (re-)downloaded.".format(
            len(datasets_with_downloads), len(new_or_updated_datasets)
        )
    )

    download_new_or_updated_to_working_dir(context, new_or_updated_datasets)

    datasets_in_working_dir.clear()
    datasets_in_working_dir.update(datasets_with_downloads)


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

    os.makedirs("{}/iati-data/datasets".format(context["ZIP_WORKING_DIR"]), exist_ok=True)

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
