import datetime
import os
import pathlib
import shutil
import time
import uuid

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient

from bulk_data_service.zippers import CodeforIATILegacyZipper, IATIBulkDataServiceZipper
from config.bds_context import BDSContext
from utilities.azure import azure_download_blob, get_azure_blob_name, get_azure_container_name
from utilities.db import get_datasets_in_bds, get_reporting_orgs_in_bds
from utilities.misc import dataset_has_iati_xml_download
from utilities.prometheus import update_prom_metric


def zipper(context: BDSContext):

    datasets = get_datasets_in_bds(context)

    reporting_orgs = get_reporting_orgs_in_bds(context)

    if context["single_run"]:
        zipper_run(context, {}, datasets, reporting_orgs)
    else:
        zipper_service_loop(context, {}, datasets, reporting_orgs)


def zipper_service_loop(
    context: BDSContext,
    datasets_in_working_dir: dict[uuid.UUID, dict],
    datasets_in_bds: dict[uuid.UUID, dict],
    reporting_orgs: dict[uuid.UUID, dict],
):

    while True:
        zipper_run(context, datasets_in_working_dir, datasets_in_bds, reporting_orgs)

        time.sleep(60 * 30)


def zipper_run(
    context: BDSContext,
    datasets_in_working_dir: dict[uuid.UUID, dict],
    datasets_in_bds: dict[uuid.UUID, dict],
    reporting_orgs: dict[uuid.UUID, dict],
):

    run_start = datetime.datetime.now(datetime.UTC)
    context.logger.info("Zipper run starting")

    setup_working_dir_with_downloaded_datasets(context, False, datasets_in_working_dir, datasets_in_bds)

    zip_creators = [
        IATIBulkDataServiceZipper(
            context,
            "{}-1".format(context["ZIP_WORKING_DIR"]),
            datasets_in_working_dir,
            datasets_in_bds,
            reporting_orgs,
        ),
        CodeforIATILegacyZipper(
            context,
            "{}-2".format(context["ZIP_WORKING_DIR"]),
            datasets_in_working_dir,
            datasets_in_bds,
            reporting_orgs,
        ),
    ]

    for zip_creator in zip_creators:

        for _ in range(2):
            zip_creator.clean_working_dir()

            shutil.copytree(context["ZIP_WORKING_DIR"], zip_creator.zip_working_dir)

            zip_creator.prepare()

            zip_creator.zip()

            if zip_creator.valid_zip_created():
                zip_creator.upload()
                break
            else:
                context.logger.error("Zip validation failed so resetting working directory and re-trying")
                setup_working_dir_with_downloaded_datasets(context, True, datasets_in_working_dir, datasets_in_bds)

        # Whether ZIP was successfully created and uploaded or not, we wipe the working dir for this ZIP format
        # We have to do this because now that we verify the ZIP by unpacking it, more storage is needed, but ACI
        # temporary disks are not configurable and max out at 50 Gb.
        zip_creator.clean_working_dir()

    run_end = datetime.datetime.now(datetime.UTC)
    context.logger.info("Zipper run finished in {}.".format(run_end - run_start))
    update_prom_metric(context, "zipper_run_duration", (run_end - run_start).seconds)


def setup_working_dir_with_downloaded_datasets(
    context: BDSContext,
    force_full_clean: bool,
    datasets_in_working_dir: dict[uuid.UUID, dict],
    datasets_in_bds: dict[uuid.UUID, dict],
):

    clean_working_dir(context, force_full_clean, datasets_in_working_dir, datasets_in_bds)

    datasets_with_downloads = {k: v for k, v in datasets_in_bds.items() if dataset_has_iati_xml_download(v)}

    remove_datasets_without_dls_from_working_dir(context, datasets_in_working_dir, datasets_with_downloads)

    new_or_updated_datasets = {
        k: v
        for k, v in datasets_with_downloads.items()
        if k not in datasets_in_working_dir
        or datasets_in_working_dir[k]["last_known_good_dataset_hash"]
        != datasets_with_downloads[k]["last_known_good_dataset_hash"]
        or datasets_in_working_dir[k]["short_name"] != datasets_with_downloads[k]["short_name"]
    }

    context.logger.info(
        "Found {} datasets with downloads. "
        "{} are new or updated and will be (re-)downloaded.".format(
            len(datasets_with_downloads), len(new_or_updated_datasets)
        )
    )

    download_new_or_updated_to_working_dir(context, new_or_updated_datasets)

    datasets_in_working_dir.clear()
    for k, dataset in datasets_with_downloads.items():
        datasets_in_working_dir[k] = dataset.copy()


def clean_working_dir(
    context: BDSContext,
    force_full_clean: bool,
    datasets_in_zip: dict[uuid.UUID, dict],
    datasets_in_bds: dict[uuid.UUID, dict],
) -> None:
    if len(datasets_in_zip) == 0 or force_full_clean:
        if len(datasets_in_zip) == 0:
            context.logger.info("First zip run of session, so deleting all XML files in the ZIP working dir.")
        else:
            context.logger.info("Force clean requested, so deleting all XML files in the ZIP working dir.")
        shutil.rmtree("{}/{}".format(context["ZIP_WORKING_DIR"], "iati-data"), ignore_errors=True)
    else:
        context.logger.info("Zipper: removing deleted or renamed datasets from working directory")

        ds_partial_paths = [
            dataset["reporting_org_short_name"] + "/" + dataset["short_name"] for dataset in datasets_in_bds.values()
        ]

        path_datasets = pathlib.Path(os.path.join(context["ZIP_WORKING_DIR"], "iati-data", "datasets"))

        for file in path_datasets.glob("**/*.xml"):
            dataset_partial_path = file.parts[-2] + "/" + file.stem
            if dataset_partial_path not in ds_partial_paths:
                try:
                    os.remove(str(file))
                except (FileNotFoundError, PermissionError, IsADirectoryError, OSError) as e:
                    context.logger.error(f"Zipper: error removing XML file {file} from working directory: {e}")


def remove_datasets_without_dls_from_working_dir(
    context: BDSContext, datasets_in_zip: dict[uuid.UUID, dict], datasets_in_bds: dict[uuid.UUID, dict]
):
    datasets_removed = {k: v for k, v in datasets_in_zip.items() if v["id"] not in datasets_in_bds}

    for dataset in datasets_removed.values():
        delete_local_xml_from_zip_working_dir(context, dataset)


def download_new_or_updated_to_working_dir(context: BDSContext, updated_datasets: dict[uuid.UUID, dict]):

    az_blob_service = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    xml_container_name = get_azure_container_name(context, "xml")

    os.makedirs("{}/iati-data/datasets".format(context["ZIP_WORKING_DIR"]), exist_ok=True)

    for dataset in updated_datasets.values():
        filename = get_local_pathname_dataset_xml(context, dataset)

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        context.logger.info("dataset id: {} - Downloading".format(dataset["id"]))

        try:
            azure_download_blob(az_blob_service, xml_container_name, get_azure_blob_name(dataset, "xml"), filename)
        except ResourceNotFoundError as e:
            context.logger.error(
                "dataset id: {} - Failed to download from Azure: {}".format(dataset["id"], e).replace("\n", " ")
            )

    az_blob_service.close()


def get_local_pathname_dataset_xml(context: BDSContext, dataset: dict) -> str:
    return "{}/iati-data/datasets/{}".format(context["ZIP_WORKING_DIR"], get_azure_blob_name(dataset, "xml"))


def delete_local_xml_from_zip_working_dir(context: BDSContext, dataset: dict):
    dataset_local_xml = get_local_pathname_dataset_xml(context, dataset)

    if os.path.exists(dataset_local_xml):
        try:
            os.remove(dataset_local_xml)
        except FileNotFoundError as e:
            context.logger.error(
                "dataset id: {} - Error removing local XML file from "
                "ZIP working dir. Details: {}.".format(dataset["id"], e)
            )
