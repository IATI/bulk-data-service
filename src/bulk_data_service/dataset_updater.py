import concurrent.futures
import json
import traceback
import uuid
from datetime import datetime, timedelta
from itertools import batched
from random import random

import psycopg
import requests
from azure.storage.blob import BlobServiceClient

from utilities.azure import azure_blob_exists, azure_upload_to_blob
from utilities.db import get_db_connection, insert_or_update_dataset
from utilities.http import (
    determine_response_encoding,
    get_last_modified_header_if_exists,
    get_requests_session,
    http_download_dataset,
    http_head_dataset,
)
from utilities.misc import (
    content_has_iati_opening_element,
    dataset_has_iati_xml_download,
    get_hash_excluding_generated_timestamp,
    get_hash_of_bytes,
    get_initial_chars_if_text,
    get_timestamp,
    set_timestamp_tz_utc,
    zip_data_as_single_file,
)
from utilities.prometheus import update_prom_metric


def add_or_update_datasets(
    context: dict, datasets_in_bds: dict[uuid.UUID, dict], registered_datasets: dict[uuid.UUID, dict]
):

    update_prom_metric(context, "total_number_of_datasets", len(registered_datasets))
    update_prom_metric(context, "datasets_added", len(registered_datasets) - len(datasets_in_bds))

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

    session = get_requests_session(context)

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
        old_source_url = ""
        bds_dataset = create_bds_dataset(registered_datasets[registered_dataset_id])
        datasets_in_bds[registered_dataset_id] = bds_dataset
    else:
        bds_dataset = datasets_in_bds[registered_dataset_id]
        old_source_url = bds_dataset["source_url"]
        update_bds_dataset_registration_info(bds_dataset, registered_datasets[registered_dataset_id])

    bds_dataset["last_update_check"] = get_timestamp()

    attempt_download = True

    download_within_hours = get_randomised_download_within_hours(context)

    if bds_dataset["source_url"] == old_source_url and dataset_downloaded_within(bds_dataset, download_within_hours):

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
            bds_dataset["most_recent_get_attempt_error_details"] = json.dumps(
                {"bds_message": "Download of IATI XML failed with non-200 HTTP status"} | e.args[0]
            )
            context["logger"].warning(
                "dataset id: {} - {}".format(
                    registered_dataset_id, bds_dataset["most_recent_get_attempt_error_details"]
                )
            )
            bds_dataset["most_recent_get_attempt_datetime"] = get_timestamp()
            bds_dataset["most_recent_get_attempt_http_status"] = e.args[0]["http_status_code"]
            insert_or_update_dataset(db_conn, bds_dataset)
        except Exception as e:
            bds_dataset["most_recent_get_attempt_datetime"] = get_timestamp()
            bds_dataset["most_recent_get_attempt_error_details"] = json.dumps(
                {
                    "bds_message": "Download of IATI XML produced EXCEPTION with GET request",
                    "message": "{}".format(e),
                }
            )
            context["logger"].warning(
                "dataset id: {} - {}".format(
                    registered_dataset_id, bds_dataset["most_recent_get_attempt_error_details"]
                )
            )
            insert_or_update_dataset(db_conn, bds_dataset)


def get_randomised_download_within_hours(context: dict) -> int:
    hours_force_redownload = int(context["FORCE_REDOWNLOAD_AFTER_HOURS"])

    if hours_force_redownload > 8:
        hours_force_redownload -= int(random() * 8)

    return hours_force_redownload


def dataset_downloaded_within(bds_dataset: dict, hours: int) -> bool:
    hours_ago = get_timestamp() - timedelta(hours=hours)
    return dataset_has_iati_xml_download(bds_dataset) and bds_dataset["last_known_good_dataset_downloaded"] > hours_ago


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

        if (
            "ETag" in head_response.headers
            and head_response.headers["ETag"] != bds_dataset["last_known_good_dataset_server_header_etag"]
        ):

            context["logger"].info(
                "dataset id: {} - Last successful download within {} hours, "
                "but ETag changed so redownloading".format(bds_dataset["id"], download_within_hours)
            )

            update_dataset_head_request_fields(bds_dataset, head_response.status_code)

        elif "Last-Modified" in head_response.headers and set_timestamp_tz_utc(
            datetime.strptime(head_response.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S GMT")
        ) != set_timestamp_tz_utc(bds_dataset["last_known_good_dataset_server_header_last_modified"]):

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

            bds_dataset["last_known_good_dataset_verified_on_server"] = bds_dataset[
                "most_recent_head_attempt_datetime"
            ]

            insert_or_update_dataset(db_conn, bds_dataset)

            attempt_download = False

    except RuntimeError as e:

        if dataset_downloaded_within(bds_dataset, 6):
            extra_err_message = "Dataset downloaded within the last 6 hours so not forcing full re-download attempt."
            attempt_download = False
        else:
            extra_err_message = "Dataset not downloaded within the last 6 hours so forcing full re-download attempt."
            attempt_download = True

        bds_dataset["most_recent_head_attempt_error_details"] = json.dumps(
            {
                "bds_message": (
                    "Last successful download within {} hours, "
                    "but HEAD request to check ETag/Last-Modified "
                    "return non-200 status. {} "
                    "HEAD request exception details: {}".format(download_within_hours, extra_err_message, e)
                )
            }
            | e.args[0]
        )

        context["logger"].warning(
            "dataset id: {} - {}".format(bds_dataset["id"], bds_dataset["most_recent_head_attempt_error_details"])
        )

        update_dataset_head_request_fields(
            bds_dataset, e.args[0]["http_status_code"], bds_dataset["most_recent_head_attempt_error_details"]
        )

        insert_or_update_dataset(db_conn, bds_dataset)

    except Exception as e:
        context["logger"].warning(
            "dataset id: {} - EXCEPTION with HEAD request, details: {}".format(bds_dataset["id"], e)
        )
        if "{}".format(e) == "str.replace() takes no keyword arguments":
            context["logger"].error("Full traceback: " "{}".format(traceback.format_exc()))

    return attempt_download


def download_and_save_dataset(
    context: dict, session: requests.Session, az_blob_service: BlobServiceClient, bds_dataset: dict
):

    most_recent_get_attempt_datetime = get_timestamp()

    download_response = http_download_dataset(session, bds_dataset["source_url"])

    last_modified_header = get_last_modified_header_if_exists(download_response)

    encoding = determine_response_encoding(download_response)

    inital_chars = get_initial_chars_if_text(download_response, encoding)

    bds_dataset["last_known_good_dataset_content_length"] = len(download_response.content)
    bds_dataset["last_known_good_dataset_initial_contents"] = inital_chars

    download_has_opening_iati_element = content_has_iati_opening_element(inital_chars)

    if not download_has_opening_iati_element:
        bds_dataset.update(
            {
                "most_recent_get_attempt_datetime": most_recent_get_attempt_datetime,
                "most_recent_get_attempt_http_status": download_response.status_code,
                "last_known_good_dataset_verified_on_server": most_recent_get_attempt_datetime,
                "most_recent_get_attempt_error_details": json.dumps(
                    {
                        "bds_message": "File does not appear to be IATI XML",
                        "http_headers": dict(download_response.headers),
                    }
                ),
                "last_known_good_dataset_server_header_last_modified": last_modified_header,
                "last_known_good_dataset_server_header_etag": download_response.headers.get("ETag", None),
            }
        )
        return

    hash = get_hash_of_bytes(download_response.content)
    hash_excluding_generated = get_hash_excluding_generated_timestamp(download_response.text, encoding)  # type: ignore

    if hash == bds_dataset["last_known_good_dataset_hash"]:
        context["logger"].info(
            "dataset id: {} - Hash of download is identical to "
            "previous value, so not re-zipping and re-uploading to Azure".format(bds_dataset["id"])
        )
    else:
        iati_xml_zipped = zip_data_as_single_file(bds_dataset["short_name"] + ".xml", download_response.content)

        response_xml = azure_upload_to_blob(
            az_blob_service,
            context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_XML"],
            "{}/{}.xml".format(bds_dataset["reporting_org_short_name"], bds_dataset["short_name"]),
            download_response.content,
            "application/xml",
            encoding=encoding,
        )

        context["logger"].debug(
            "dataset id: {} - Azure XML upload response: {}".format(bds_dataset["id"], response_xml)
        )

        response_zip = azure_upload_to_blob(
            az_blob_service,
            context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_ZIP"],
            "{}/{}.zip".format(bds_dataset["reporting_org_short_name"], bds_dataset["short_name"]),
            iati_xml_zipped,
            "application/zip",
        )

        if not azure_blob_exists(
            az_blob_service,
            context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_XML"],
            "{}/{}.xml".format(bds_dataset["reporting_org_short_name"], bds_dataset["short_name"]),
        ):
            context["logger"].error("dataset id: {} - Azure XML upload failed")
            context["logger"].debug(
                "dataset id: {} - Azure ZIP upload response: {}".format(bds_dataset["id"], response_xml)
            )

    bds_dataset.update(
        {
            "last_known_good_dataset_hash": hash,
            "last_known_good_dataset_hash_excluding_generated_timestamp": hash_excluding_generated,
            "last_update_check": most_recent_get_attempt_datetime,
            "most_recent_get_attempt_datetime": most_recent_get_attempt_datetime,
            "most_recent_get_attempt_http_status": download_response.status_code,
            "last_known_good_dataset_downloaded": most_recent_get_attempt_datetime,
            "last_known_good_dataset_verified_on_server": most_recent_get_attempt_datetime,
            "most_recent_get_attempt_error_details": None,
            "last_known_good_dataset_server_header_last_modified": last_modified_header,
            "last_known_good_dataset_server_header_etag": download_response.headers.get("ETag", None),
        }
    )


def update_dataset_head_request_fields(dataset: dict, status_code: int, error_msg: str = ""):
    dataset["most_recent_head_attempt_datetime"] = get_timestamp()
    dataset["most_recent_head_attempt_http_status"] = status_code
    dataset["most_recent_head_attempt_error_details"] = error_msg


def create_bds_dataset(registered_dataset: dict) -> dict:
    return {
        "id": registered_dataset["id"],
        "short_name": registered_dataset["short_name"],
        "reporting_org_id": registered_dataset["reporting_org_id"],
        "reporting_org_short_name": registered_dataset["reporting_org_short_name"],
        "source_url": registered_dataset["source_url"],
        "license_id": registered_dataset["license_id"],
        "registration_service_dataset_metadata": registered_dataset["registration_service_dataset_metadata"],
        "registration_service_name": registered_dataset["registration_service_name"],
        "last_update_check": None,
        "last_known_good_dataset_hash": None,
        "last_known_good_dataset_hash_excluding_generated_timestamp": None,
        "last_known_good_dataset_verified_on_server": None,
        "last_known_good_dataset_downloaded": None,
        "last_known_good_dataset_server_header_last_modified": None,
        "last_known_good_dataset_server_header_etag": None,
        "last_known_good_dataset_content_length": None,
        "last_known_good_dataset_initial_contents": None,
        "most_recent_head_attempt_datetime": None,
        "most_recent_head_attempt_http_status": None,
        "most_recent_head_attempt_error_details": None,
        "most_recent_head_attempt_server_headers": None,
        "most_recent_get_attempt_datetime": None,
        "most_recent_get_attempt_http_status": None,
        "most_recent_get_attempt_error_details": None,
        "most_recent_get_attempt_server_headers": None,
    }


def update_bds_dataset_registration_info(bds_dataset: dict, registered_dataset: dict):
    for field in [
        "reporting_org_id",
        "reporting_org_short_name",
        "source_url",
        "license_id",
        "registration_service_dataset_metadata",
        "registration_service_name",
    ]:
        bds_dataset[field] = registered_dataset[field]
