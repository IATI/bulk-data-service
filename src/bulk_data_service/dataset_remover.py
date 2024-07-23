import uuid
from datetime import timedelta
from typing import Any

import psycopg
from azure.storage.blob import BlobServiceClient

from utilities.azure import delete_azure_iati_blob
from utilities.db import get_db_connection, insert_or_update_dataset, remove_dataset_from_db
from utilities.misc import get_timestamp


def remove_deleted_datasets_from_bds(
    context: dict[str, Any], datasets_in_bds: dict[uuid.UUID, dict], registered_datasets: dict[uuid.UUID, dict]
):

    db_conn = get_db_connection(context)

    az_blob_service = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    ids_to_delete = [k for k in datasets_in_bds.keys() if k not in registered_datasets]

    context["prom_metrics"]["datasets_unregistered"].set(len(ids_to_delete))

    for id in ids_to_delete:

        context["logger"].info(
            "dataset id: {} - Dataset no longer exists in registration "
            "service so removing from Bulk Data Service".format(id)
        )

        remove_dataset_from_db(db_conn, id)

        delete_azure_iati_blob(context, az_blob_service, datasets_in_bds[id], "xml")

        delete_azure_iati_blob(context, az_blob_service, datasets_in_bds[id], "zip")

        del datasets_in_bds[id]

    az_blob_service.close()

    db_conn.close()


def remove_expired_downloads(context: dict[str, Any], datasets_in_bds: dict[uuid.UUID, dict]):

    db_conn = get_db_connection(context)

    az_blob_service = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    expired_datasets = 0

    for dataset in datasets_in_bds.values():
        if dataset_has_expired(context, dataset):
            remove_download_for_expired_dataset(context, db_conn, az_blob_service, dataset)
            expired_datasets += 1

    context["prom_metrics"]["datasets_expired"].set(expired_datasets)

    az_blob_service.close()

    db_conn.close()


def remove_download_for_expired_dataset(
    context: dict[str, Any], db_conn: psycopg.Connection, az_blob_service: BlobServiceClient, bds_dataset: dict
) -> dict:

    max_hours = int(context["REMOVE_LAST_GOOD_DOWNLOAD_AFTER_FAILING_HOURS"])

    context["logger"].info(
        "dataset id: {} - Last good download for dataset "
        "is over max threshold of {} hours, so removing "
        "last good download from Bulk Data Service".format(bds_dataset["id"], max_hours)
    )

    bds_dataset["last_successful_download"] = None
    bds_dataset["hash"] = None
    bds_dataset["hash_excluding_generated_timestamp"] = None

    insert_or_update_dataset(db_conn, bds_dataset)

    delete_azure_iati_blob(context, az_blob_service, bds_dataset, "xml")

    delete_azure_iati_blob(context, az_blob_service, bds_dataset, "zip")

    return bds_dataset


def dataset_has_expired(context: dict[str, Any], bds_dataset: dict) -> bool:

    max_hours = int(context["REMOVE_LAST_GOOD_DOWNLOAD_AFTER_FAILING_HOURS"])

    return bds_dataset["last_successful_download"] is not None and bds_dataset["last_successful_download"] < (
        get_timestamp() - timedelta(hours=max_hours)
    )
