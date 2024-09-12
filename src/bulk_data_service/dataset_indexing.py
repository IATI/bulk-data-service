import json
import uuid
from typing import Any

from azure.storage.blob import BlobServiceClient

from utilities.azure import azure_upload_to_blob, get_azure_blob_public_url
from utilities.misc import get_timestamp


def create_and_upload_indices(context: dict, datasets_in_bds: dict[uuid.UUID, dict]):

    context["logger"].info("Creating indices")

    minimal_index = create_index_json(context, datasets_in_bds, "minimal")

    full_index = create_index_json(context, datasets_in_bds, "full")

    upload_index_json_to_azure(context, get_index_name(context, "minimal"), minimal_index)

    upload_index_json_to_azure(context, get_index_name(context, "full"), full_index)

    context["logger"].info("Creation of indices finished")


def upload_index_json_to_azure(context: dict, index_name: str, index_json: str):

    az_blob_service = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    for container in set(
        [
            context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_XML"],
            context["AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_ZIP"],
        ]
    ):
        azure_upload_to_blob(az_blob_service, container, index_name, index_json, "application/json")

    az_blob_service.close()


def create_index_json(context: dict, datasets_in_bds: dict[uuid.UUID, dict], index_type: str) -> str:

    index = {"index_created": get_timestamp(), "datasets": {}}

    index["datasets"] = get_dataset_index(context, datasets_in_bds, index_type)

    return json.dumps(index, default=str, sort_keys=True, indent=True)


def get_dataset_index(context: dict, datasets_in_bds: dict[uuid.UUID, dict], index_type: str) -> dict:
    return {v["name"]: get_index_entry(context, v, index_type) for _, v in datasets_in_bds.items()}


def get_index_entry(context: dict, dataset: dict, index_type: str) -> dict[str, Any]:

    if index_type == "minimal":
        dataset_index_entry = get_minimal_index_entry_from_dataset(context, dataset)
    else:
        dataset_index_entry = get_full_index_entry_from_dataset(context, dataset)

    dataset_index_entry["url_xml"] = ""
    dataset_index_entry["url_zip"] = ""

    if dataset_index_entry["last_successful_download"] is not None:
        dataset_index_entry["url_xml"] = get_azure_blob_public_url(context, dataset, "xml")
        dataset_index_entry["url_zip"] = get_azure_blob_public_url(context, dataset, "zip")

    return dataset_index_entry


def get_index_name(context: dict, index_type: str) -> str:
    if index_type not in ["minimal", "full"]:
        raise ValueError("Unknown type for dataset index")

    return "dataset-index-{}.json".format(index_type)


def get_minimal_index_entry_from_dataset(context: dict, dataset: dict) -> dict:
    return {k: v for k, v in dataset.items() if k in get_minimal_index_fields(context)}


def get_full_index_entry_from_dataset(context: dict, dataset: dict) -> dict:
    full_index_entry = {k: v for k, v in dataset.items() if k in get_full_index_fields(context)}

    field_from_json_str_to_object(full_index_entry, "download_error_message", "download_error_details")

    field_from_json_str_to_object(full_index_entry, "head_error_message", "head_error_details")

    return full_index_entry


def field_from_json_str_to_object(entry: dict, source_field: str, dest_field: str):
    entry[dest_field] = json.loads(
        entry[source_field] if entry[source_field] is not None and entry[source_field] != "" else "{}"
    )
    del entry[source_field]


def get_full_index_fields(context: dict) -> list[str]:
    return [
        "id",
        "name",
        "publisher_name",
        "type",
        "source_url",
        "hash",
        "hash_excluding_generated_timestamp",
        "last_update_check",
        "last_head_attempt",
        "last_head_http_status",
        "head_error_message",
        "last_download_attempt",
        "last_download_http_status",
        "last_successful_download",
        "last_verified_on_server",
        "download_error_message",
        "content_modified",
        "content_modified_excluding_generated_timestamp",
        "server_header_last_modified",
        "server_header_etag",
    ]


def get_minimal_index_fields(context: dict) -> list[str]:
    return [
        "id",
        "name",
        "publisher_name",
        "source_url",
        "hash",
        "hash_excluding_generated_timestamp",
        "last_successful_download",
    ]
