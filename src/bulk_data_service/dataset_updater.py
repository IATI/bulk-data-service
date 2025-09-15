import concurrent.futures
import copy
import uuid
from datetime import datetime, timedelta
from itertools import batched
from random import random

import psycopg
import requests
from azure.storage.blob import BlobServiceClient

from bulk_data_service.dataset import (
    DATASET_REGISTRATION_FIELDS,
    create_empty_dataset,
    update_dataset_http_attempt_fields_as_error,
    update_dataset_http_attempt_fields_as_success,
)
from config.bds_context import BDSContext
from utilities.azure import azure_get_blob_etag, azure_upload_to_blob_and_verify, send_dataset_check_result_message
from utilities.db import get_db_connection, insert_or_update_dataset
from utilities.http import (
    determine_response_encoding,
    get_last_modified_header_if_exists,
    get_requests_session,
    http_download_dataset,
    http_head_dataset,
)
from utilities.message_formatters import create_dataset_check_result_msg_payload
from utilities.misc import (
    dataset_has_iati_xml_download,
    get_hash_excluding_generated_timestamp,
    get_hash_of_bytes,
    get_initial_chars_if_text,
    get_initial_iati_content,
    get_timestamp,
    set_timestamp_tz_utc,
    zip_data_as_single_file,
)
from utilities.prometheus import update_prom_metric


def add_or_update_datasets(
    context: BDSContext, datasets_in_bds: dict[uuid.UUID, dict], registered_datasets: dict[uuid.UUID, dict]
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
    context: BDSContext, datasets_in_bds: dict[uuid.UUID, dict], registered_datasets_to_update: dict[uuid.UUID, dict]
):

    db_conn = get_db_connection(context)

    az_blob_service = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    session = get_requests_session(context)

    for registered_dataset_id in registered_datasets_to_update:

        if db_conn.closed:
            db_conn = get_db_connection(context)

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
    context: BDSContext,
    registered_dataset_id: uuid.UUID,
    datasets_in_bds: dict[uuid.UUID, dict],
    registered_datasets: dict[uuid.UUID, dict],
    az_blob_service: BlobServiceClient,
    session: requests.Session,
    db_conn: psycopg.Connection,
):

    dataset_previous_version = copy.deepcopy(datasets_in_bds.get(registered_dataset_id, None))

    if registered_dataset_id not in datasets_in_bds:
        bds_dataset = create_dataset_from_registered_dataset(registered_datasets[registered_dataset_id])
        old_source_url = ""
        datasets_in_bds[registered_dataset_id] = bds_dataset
    else:
        bds_dataset = datasets_in_bds[registered_dataset_id]
        old_source_url = bds_dataset["source_url"]
        update_dataset_from_registered_dataset(bds_dataset, registered_datasets[registered_dataset_id])

    check_time = get_timestamp()

    bds_dataset["last_update_check"] = check_time
    bds_dataset["registration_service_metadata_refreshed_datetime"] = check_time

    attempt_download = True

    hours = get_randomised_redownload_after_n_hours(context)

    if bds_dataset["source_url"] == old_source_url and dataset_downloaded_within(bds_dataset, hours):

        attempt_download = check_dataset_etag_last_mod_header(
            context, db_conn, session, bds_dataset, hours, check_time
        )

    if attempt_download:
        try:
            download_and_save_dataset(context, session, az_blob_service, bds_dataset, check_time)

            datasets_in_bds[registered_dataset_id] = bds_dataset

            context.logger.info("dataset id: {} - Added/updated dataset".format(bds_dataset["id"]))

        except RuntimeError as e:
            summary_message = "Download of IATI XML failed with non-200 HTTP status"

            update_dataset_http_attempt_fields_as_error(
                bds_dataset,
                get_timestamp(),
                "get",
                error_type="http_non_200",
                http_headers=e.args[0]["http_headers"],
                http_reason=e.args[0]["http_reason"],
                http_status=e.args[0]["http_status"],
                summary_message=summary_message,
                source_url=bds_dataset["source_url"],
            )

            context.logger.info(f"dataset id: {registered_dataset_id} - {summary_message}")

        except Exception as e:

            error_type, summary_message = get_error_type_and_summary_message("Download of IATI XML", e)

            update_dataset_http_attempt_fields_as_error(
                bds_dataset,
                get_timestamp(),
                "get",
                detailed_message="{}".format(e),
                error_type=error_type,
                summary_message=summary_message,
                source_url=bds_dataset["source_url"],
            )

            context.logger.info(f"dataset id: {registered_dataset_id} - {summary_message}")

        insert_or_update_dataset(db_conn, bds_dataset)

    if context.SEND_DATASET_CHECK_MESSAGES:
        msg_payload = create_dataset_check_result_msg_payload(dataset_previous_version, bds_dataset)

        try:
            send_dataset_check_result_message(context, msg_payload, 2)
        except RuntimeError as e:
            context["logger"].error(
                f"dataset id: {registered_dataset_id} - Error sending DATASET_CHECK_RESULT message. Details: {str(e)}"
            )


def get_randomised_redownload_after_n_hours(context: BDSContext) -> int:
    hours_force_redownload = context.FORCE_DOWNLOAD_AFTER_HOURS

    if hours_force_redownload > 8:
        hours_force_redownload -= int(random() * 8)

    return hours_force_redownload


def dataset_downloaded_within(bds_dataset: dict, hours: int) -> bool:
    hours_ago = get_timestamp() - timedelta(hours=hours)
    return dataset_has_iati_xml_download(bds_dataset) and bds_dataset["last_known_good_dataset_downloaded"] > hours_ago


def check_dataset_etag_last_mod_header(
    context: BDSContext,
    db_conn: psycopg.Connection,
    session: requests.Session,
    bds_dataset: dict,
    download_within_hours: int,
    attempt_time: datetime,
) -> bool:

    attempt_download = True

    try:
        head_response = http_head_dataset(session, bds_dataset["source_url"], timeout=context.DATASET_HEAD_TIMEOUT)

        if (
            "ETag" in head_response.headers
            and head_response.headers["ETag"] != bds_dataset["last_known_good_dataset_server_header_etag"]
        ):

            context.logger.info(
                "dataset id: {} - Last successful download within {} hours, "
                "but ETag changed so redownloading".format(bds_dataset["id"], download_within_hours)
            )

            update_dataset_http_attempt_fields_as_success(bds_dataset, attempt_time, "head", head_response.status_code)

        elif "Last-Modified" in head_response.headers and set_timestamp_tz_utc(
            datetime.strptime(head_response.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S GMT")
        ) != set_timestamp_tz_utc(bds_dataset["last_known_good_dataset_server_header_last_modified"]):

            context.logger.info(
                "dataset id: {} - Last successful download within {} hours, "
                "but Last-Modified header changed so redownloading".format(bds_dataset["id"], download_within_hours)
            )

            update_dataset_http_attempt_fields_as_success(bds_dataset, attempt_time, "head", head_response.status_code)

        else:
            context.logger.info(
                "dataset id: {} - Last successful download within {} hours, "
                "Last-Modified and ETag same, so not redownloading".format(bds_dataset["id"], download_within_hours)
            )

            update_dataset_http_attempt_fields_as_success(bds_dataset, attempt_time, "head", head_response.status_code)

            bds_dataset["last_known_good_dataset_verified_on_server"] = bds_dataset[
                "most_recent_head_attempt_datetime"
            ]

            insert_or_update_dataset(db_conn, bds_dataset)

            attempt_download = False

    except RuntimeError as e:

        if dataset_downloaded_within(bds_dataset, context.REDOWNLOAD_FROM_NON_HEAD_SERVERS_AFTER_HOURS):
            extra_err_message = (
                f"Dataset downloaded within the last {context.REDOWNLOAD_FROM_NON_HEAD_SERVERS_AFTER_HOURS} "
                "hours so not forcing full re-download attempt."
            )
            attempt_download = False
        else:
            extra_err_message = (
                f"Dataset not downloaded within the last {context.REDOWNLOAD_FROM_NON_HEAD_SERVERS_AFTER_HOURS} "
                "hours so not forcing full re-download attempt."
            )
            attempt_download = True

        summary_message = (
            f"Last successful download within {download_within_hours} hours, but HEAD request to check "
            f"ETag/Last-Modified returned non-200 status. {extra_err_message}"
        )

        update_dataset_http_attempt_fields_as_error(
            bds_dataset,
            attempt_time,
            "head",
            error_type="method_not_allowed" if e.args[0]["http_status"] == 405 else "other_error",
            http_headers=e.args[0]["http_headers"],
            http_reason=e.args[0]["http_reason"],
            http_status=e.args[0]["http_status"],
            summary_message=summary_message,
            source_url=bds_dataset["source_url"],
        )

        context.logger.info(f"dataset id: {bds_dataset["id"]} - {summary_message}")

        insert_or_update_dataset(db_conn, bds_dataset)

    except (requests.ConnectionError, requests.exceptions.TooManyRedirects) as e:

        error_type, summary_message = get_error_type_and_summary_message("HEAD request", e)

        update_dataset_http_attempt_fields_as_error(
            bds_dataset,
            get_timestamp(),
            "head",
            error_type=error_type,
            summary_message=summary_message,
            detailed_message=str(e),
            source_url=bds_dataset["source_url"],
        )

        context.logger.info(f"dataset id: {bds_dataset["id"]} - {summary_message}")

    return attempt_download


def get_error_type_and_summary_message(base_msg: str, e: Exception) -> tuple[str, str]:

    if isinstance(e, requests.exceptions.SSLError):
        error_type = "ssl_error"
        summary_message = f"{base_msg} failed due to SSL error"
    elif isinstance(e, requests.exceptions.ConnectTimeout):
        error_type = "connection_timeout"
        summary_message = f"{base_msg} failed due to connection timeout"
    elif isinstance(e, requests.exceptions.TooManyRedirects):
        error_type = "too_many_redirects"
        summary_message = f"{base_msg} failed due to too many redirects"
    elif isinstance(e, requests.ConnectionError):
        error_type = "connection_error"
        summary_message = f"{base_msg} failed due to connection error"
    else:
        error_type = "other_error"
        summary_message = f"{base_msg} produced EXCEPTION with GET request"

    return (error_type, summary_message)


def download_and_save_dataset(
    context: BDSContext,
    session: requests.Session,
    az_blob_service: BlobServiceClient,
    bds_dataset: dict,
    attempt_datetime: datetime,
):
    download_response = http_download_dataset(session, bds_dataset["source_url"], timeout=context.DATASET_GET_TIMEOUT)

    last_modified_header = get_last_modified_header_if_exists(download_response)

    encoding = determine_response_encoding(download_response)

    initial_iati_content = get_initial_iati_content(get_initial_chars_if_text(download_response, encoding))

    if initial_iati_content is None:
        update_dataset_http_attempt_fields_as_error(
            bds_dataset,
            attempt_datetime,
            "get",
            error_type="not_iati_content",
            http_headers=dict(download_response.headers),
            http_status=download_response.status_code,
            summary_message="File does not appear to be IATI XML",
        )
        return

    hash = get_hash_of_bytes(download_response.content)

    hash_excluding_generated = get_hash_excluding_generated_timestamp(download_response.text, encoding)  # type: ignore

    xml_blob_name = "{}/{}.xml".format(bds_dataset["reporting_org_short_name"], bds_dataset["short_name"])

    zip_blob_name = "{}/{}.zip".format(bds_dataset["reporting_org_short_name"], bds_dataset["short_name"])

    xml_blob_etag = azure_get_blob_etag(context, az_blob_service, xml_blob_name)

    zip_blob_etag = azure_get_blob_etag(context, az_blob_service, zip_blob_name)

    if (
        hash == bds_dataset["last_known_good_dataset_hash"]
        and xml_blob_etag == bds_dataset["last_known_good_dataset_cached_dataset_xml_etag"]
        and zip_blob_etag == bds_dataset["last_known_good_dataset_cached_dataset_zip_etag"]
    ):
        context.logger.info(
            "dataset id: {} - Hash and Azure blob etags are the same"
            ", so not re-zipping and re-uploading to Azure".format(bds_dataset["id"])
        )
    else:
        iati_xml_zipped = zip_data_as_single_file(bds_dataset["short_name"] + ".xml", download_response.content)

        cached_xml_url, cached_xml_etag = azure_upload_to_blob_and_verify(
            context,
            bds_dataset,
            az_blob_service,
            context["AZURE_STORAGE_BLOB_CONTAINER_NAME"],
            xml_blob_name,
            download_response.content,
            "application/xml",
            encoding=encoding,
        )

        cached_zip_url, cached_zip_etag = azure_upload_to_blob_and_verify(
            context,
            bds_dataset,
            az_blob_service,
            context["AZURE_STORAGE_BLOB_CONTAINER_NAME"],
            zip_blob_name,
            iati_xml_zipped,
            "application/zip",
        )

        bds_dataset.update(
            {
                "last_known_good_dataset_cached_dataset_xml_etag": cached_xml_etag,
                "last_known_good_dataset_cached_dataset_xml_url": cached_xml_url,
                "last_known_good_dataset_cached_dataset_zip_etag": cached_zip_etag,
                "last_known_good_dataset_cached_dataset_zip_url": cached_zip_url,
            }
        )

    update_dataset_http_attempt_fields_as_success(bds_dataset, attempt_datetime, "get", download_response.status_code)

    bds_dataset.update(
        {
            "last_update_check": attempt_datetime,
            "last_known_good_dataset_hash": hash,
            "last_known_good_dataset_hash_excluding_generated_timestamp": hash_excluding_generated,
            "last_known_good_dataset_downloaded": attempt_datetime,
            "last_known_good_dataset_verified_on_server": attempt_datetime,
            "last_known_good_dataset_content_length": len(download_response.content),
            "last_known_good_dataset_initial_contents": initial_iati_content,
            "last_known_good_dataset_server_header_last_modified": last_modified_header,
            "last_known_good_dataset_server_header_etag": download_response.headers.get("ETag", None),
            "last_known_good_dataset_source_url": bds_dataset["source_url"],
        }
    )


def create_dataset_from_registered_dataset(registered_dataset: dict) -> dict:
    dataset = create_empty_dataset()

    return dataset | {
        "id": registered_dataset["id"],
        "short_name": registered_dataset["short_name"],
        "reporting_org_id": registered_dataset["reporting_org_id"],
        "reporting_org_short_name": registered_dataset["reporting_org_short_name"],
        "source_url": registered_dataset["source_url"],
        "licence_id": registered_dataset["licence_id"],
        "registration_service_dataset_metadata": registered_dataset["registration_service_dataset_metadata"],
        "registration_service_name": registered_dataset["registration_service_name"],
    }


def update_dataset_from_registered_dataset(bds_dataset: dict, registered_dataset: dict):
    for field in filter(lambda x: x != "id" and x in registered_dataset.keys(), DATASET_REGISTRATION_FIELDS):
        bds_dataset[field] = registered_dataset[field]
