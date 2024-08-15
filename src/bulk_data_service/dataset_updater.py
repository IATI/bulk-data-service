import concurrent.futures
import uuid
from datetime import datetime, timedelta
from itertools import batched
from random import random

import psycopg
import requests
from azure.storage.blob import BlobServiceClient

from utilities.azure import azure_upload_to_blob
from utilities.db import get_db_connection, insert_or_update_dataset
from utilities.http import get_requests_session, http_download_dataset, http_head_dataset
from utilities.misc import (
    get_hash,
    get_hash_excluding_generated_timestamp,
    get_timestamp,
    set_timestamp_tz_utc,
    zip_data_as_single_file,
)


def add_or_update_datasets(
    context: dict, datasets_in_bds: dict[uuid.UUID, dict], registered_datasets: dict[uuid.UUID, dict]
):

    context["prom_metrics"]["total_number_of_datasets"].set(len(registered_datasets))
    context["prom_metrics"]["datasets_added"].set(len(registered_datasets) - len(datasets_in_bds))

    threads = []

    num_batches = int(len(registered_datasets) / int(context["NUMBER_DOWNLOADER_THREADS"])) + 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_batches) as executor:
        for dataset_batch_ids in batched(registered_datasets, num_batches):

            dataset_batch = {k: registered_datasets[k] for k in dataset_batch_ids}

            threads.append(executor.submit(add_or_update_dataset_batch, context, datasets_in_bds, dataset_batch))

        for future in concurrent.futures.as_completed(threads):
            future.result()


def add_or_update_dataset_batch(
    context: dict, datasets_in_bds: dict[uuid.UUID, dict], registered_datasets_to_update: dict[uuid.UUID, dict]
):

    db_conn = get_db_connection(context)

    az_blob_service = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    session = get_requests_session()

    for registered_dataset_id in registered_datasets_to_update:

        add_or_update_registered_dataset(
            context,
            registered_dataset_id,
            datasets_in_bds,
            registered_datasets_to_update,
            az_blob_service,
            session,
            db_conn,
        )

    session.close()

    az_blob_service.close()

    db_conn.close()


def add_or_update_registered_dataset(
    context: dict,
    registered_dataset_id: uuid.UUID,
    datasets_in_bds: dict[uuid.UUID, dict],
    registered_datasets: dict[uuid.UUID, dict],
    az_blob_service: BlobServiceClient,
    session: requests.Session,
    db_conn: psycopg.Connection,
):

    if registered_dataset_id not in datasets_in_bds:
        bds_dataset = create_bds_dataset(registered_datasets[registered_dataset_id])
        datasets_in_bds[registered_dataset_id] = bds_dataset
    else:
        bds_dataset = datasets_in_bds[registered_dataset_id]
        update_bds_dataset_registration_info(bds_dataset, registered_datasets[registered_dataset_id])

    attempt_download = True

    bds_dataset["last_update_check"] = get_timestamp()

    download_within_hours = get_randomised_download_within_hours(context)

    if dataset_downloaded_within(bds_dataset, download_within_hours):

        attempt_download = check_dataset_etag_last_mod_header(
            context, db_conn, session, bds_dataset, download_within_hours
        )

    if attempt_download:
        try:
            download_and_save_dataset(context, session, az_blob_service, bds_dataset)

            datasets_in_bds[registered_dataset_id] = bds_dataset

            insert_or_update_dataset(db_conn, bds_dataset)

            context["logger"].info("dataset id: {} - Added/updated dataset".format(bds_dataset["id"]))

        except RuntimeError as e:
            bds_dataset["download_error_message"] = "Download of IATI XML failed with non-200 HTTP status: {}".format(
                e
            )
            context["logger"].warning(
                "dataset id: {} - {}".format(registered_dataset_id, bds_dataset["download_error_message"])
            )
            bds_dataset["last_download_attempt"] = get_timestamp()
            bds_dataset["last_download_http_status"] = e.args[0]["http_status_code"]
            insert_or_update_dataset(db_conn, bds_dataset)
        except Exception as e:
            bds_dataset["last_download_attempt"] = get_timestamp()
            bds_dataset["download_error_message"] = (
                "Download of IATI XML produced EXCEPTION with GET request: {}".format(e)
            )
            context["logger"].warning(
                "dataset id: {} - {}".format(registered_dataset_id, bds_dataset["download_error_message"])
            )
            insert_or_update_dataset(db_conn, bds_dataset)


def get_randomised_download_within_hours(context: dict) -> int:
    hours_force_redownload = int(context["FORCE_REDOWNLOAD_AFTER_HOURS"])

    if hours_force_redownload > 8:
        hours_force_redownload -= int(random() * 8)

    return hours_force_redownload


def dataset_downloaded_within(bds_dataset: dict, hours: int) -> bool:
    hours_ago = get_timestamp() - timedelta(hours=hours)
    return bds_dataset["last_successful_download"] is not None and bds_dataset["last_successful_download"] > hours_ago


def check_dataset_etag_last_mod_header(
    context: dict,
    db_conn: psycopg.Connection,
    session: requests.Session,
    bds_dataset: dict,
    download_within_hours: int,
) -> bool:

    attempt_download = True

    try:
        head_response = http_head_dataset(session, bds_dataset["source_url"])

        if "ETag" in head_response.headers and head_response.headers["ETag"] != bds_dataset["server_header_etag"]:

            context["logger"].info(
                "dataset id: {} - Last successful download within {} hours, "
                "but ETag changed so redownloading".format(bds_dataset["id"], download_within_hours)
            )

            update_dataset_head_request_fields(bds_dataset, head_response.status_code)

        elif "Last-Modified" in head_response.headers and set_timestamp_tz_utc(
            datetime.strptime(head_response.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S GMT")
        ) != set_timestamp_tz_utc(bds_dataset["server_header_last_modified"]):

            context["logger"].info(
                "dataset id: {} - Last successful download within {} hours, "
                "but Last-Modified header changed so redownloading".format(bds_dataset["id"], download_within_hours)
            )

            update_dataset_head_request_fields(bds_dataset, head_response.status_code)

        else:
            context["logger"].info(
                "dataset id: {} - Last successful download within {} hours, "
                "Last-Modified and ETag same, so not redownloading".format(bds_dataset["id"], download_within_hours)
            )

            update_dataset_head_request_fields(bds_dataset, head_response.status_code)

            bds_dataset["last_verified_on_server"] = bds_dataset["last_head_attempt"]

            insert_or_update_dataset(db_conn, bds_dataset)

            attempt_download = False

    except RuntimeError as e:

        if dataset_downloaded_within(bds_dataset, 6):
            extra_err_message = (
                "Dataset downloaded within the last 6 hours so not " "forcing full re-download attempt."
            )
            attempt_download = False
        else:
            extra_err_message = (
                "Dataset not downloaded within the last 6 hours so " "forcing full re-download attempt."
            )
            attempt_download = True

        bds_dataset["head_error_message"] = (
            "Last successful download within {} hours, "
            "but HEAD request to check ETag/Last-Modified "
            "return non-200 status. {} "
            "HEAD request exception details: {}".format(download_within_hours, extra_err_message, e)
        )

        context["logger"].warning("dataset id: {} - {}".format(bds_dataset["id"], bds_dataset["head_error_message"]))

        update_dataset_head_request_fields(
            bds_dataset, e.args[0]["http_status_code"], bds_dataset["head_error_message"]
        )

        insert_or_update_dataset(db_conn, bds_dataset)

    except Exception as e:
        context["logger"].warning(
            "dataset id: {} - EXCEPTION with HEAD request, details: " "{}".format(bds_dataset["id"], e)
        )

    return attempt_download


def download_and_save_dataset(
    context: dict, session: requests.Session, az_blob_service: BlobServiceClient, bds_dataset: dict
):

    last_download_attempt = get_timestamp()

    download_response = http_download_dataset(session, bds_dataset["source_url"])

    hash = get_hash(download_response.text)
    hash_excluding_generated = get_hash_excluding_generated_timestamp(download_response.text)

    if hash == bds_dataset["hash"]:
        context["logger"].info(
            "dataset id: {} - Hash of download is identical to "
            "previous value, so not re-zipping and re-uploading to Azure".format(bds_dataset["id"])
        )
    else:
        iati_xml_zipped = zip_data_as_single_file(bds_dataset["name"] + ".xml", download_response.text)

        azure_upload_to_blob(
            az_blob_service,
            context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_XML"],
            "{}/{}.xml".format(bds_dataset["publisher_name"], bds_dataset["name"]),
            download_response.text,
            "application/xml",
        )

        azure_upload_to_blob(
            az_blob_service,
            context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_ZIP"],
            "{}/{}.zip".format(bds_dataset["publisher_name"], bds_dataset["name"]),
            iati_xml_zipped,
            "application/zip",
        )

    bds_dataset.update(
        {
            "hash": hash,
            "hash_excluding_generated_timestamp": hash_excluding_generated,
            "last_update_check": last_download_attempt,
            "last_download_attempt": last_download_attempt,
            "last_download_http_status": download_response.status_code,
            "last_successful_download": last_download_attempt,
            "last_verified_on_server": last_download_attempt,
            "download_error_message": None,
            "content_modified": None,
            "content_modified_excluding_generated_timestamp": None,
            "server_header_last_modified": download_response.headers.get("Last-Modified", None),
            "server_header_etag": download_response.headers.get("ETag", None),
        }
    )


def update_dataset_head_request_fields(dataset: dict, status_code: int, error_msg: str = ""):
    dataset["last_head_attempt"] = get_timestamp()
    dataset["last_head_http_status"] = status_code
    dataset["head_error_message"] = error_msg


def create_bds_dataset(registered_dataset: dict) -> dict:
    return {
        "id": registered_dataset["id"],
        "name": registered_dataset["name"],
        "publisher_id": registered_dataset["publisher_id"],
        "publisher_name": registered_dataset["publisher_name"],
        "type": registered_dataset["type"],
        "source_url": registered_dataset["source_url"],
        "hash": None,
        "hash_excluding_generated_timestamp": None,
        "last_update_check": None,
        "last_head_attempt": None,
        "last_head_http_status": None,
        "head_error_message": None,
        "last_verified_on_server": None,
        "last_download_attempt": None,
        "last_download_http_status": None,
        "last_successful_download": None,
        "download_error_message": None,
        "content_modified": None,
        "content_modified_excluding_generated_timestamp": None,
        "server_header_last_modified": None,
        "server_header_etag": None,
    }


def update_bds_dataset_registration_info(bds_dataset: dict, registered_dataset: dict):
    for field in ["publisher_id", "publisher_name", "type", "source_url"]:
        bds_dataset[field] = registered_dataset[field]
