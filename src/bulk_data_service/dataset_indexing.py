import json
import uuid
from datetime import datetime
from typing import Any

from azure.storage.blob import BlobServiceClient

from utilities.azure import azure_upload_to_blob, get_azure_blob_public_url
from utilities.misc import dataset_has_iati_xml_download, get_timestamp


def create_and_upload_indices(
    context: dict, datasets_in_bds: dict[uuid.UUID, dict], reporting_orgs_in_bds: dict[uuid.UUID, dict]
):
    index_creation_time = get_timestamp()

    context["logger"].info("Creating indices")

    dataset_index_minimal = create_dataset_index_json(context, index_creation_time, datasets_in_bds, "minimal")

    dataset_index_full = create_dataset_index_json(context, index_creation_time, datasets_in_bds, "full")

    reporting_org_index_full = create_reporting_org_index_json(
        context, index_creation_time, datasets_in_bds, reporting_orgs_in_bds
    )

    upload_index_json_to_azure(context, get_dataset_index_name(context, "minimal"), dataset_index_minimal)

    upload_index_json_to_azure(context, get_dataset_index_name(context, "full"), dataset_index_full)

    upload_index_json_to_azure(context, get_reporting_org_index_name(context), reporting_org_index_full)

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


def create_dataset_index_json(
    context: dict,
    created_time: datetime,
    datasets_in_bds: dict[uuid.UUID, dict],
    index_type: str,
) -> str:

    index = create_index_time_entries(created_time)

    index["datasets"] = get_dataset_index(context, datasets_in_bds, index_type)

    return json.dumps(index, default=str, sort_keys=True, indent=True)


def create_reporting_org_index_json(
    context: dict,
    created_time: datetime,
    datasets_in_bds: dict[uuid.UUID, dict],
    reporting_orgs_in_bds: dict[uuid.UUID, dict],
) -> str:

    index = create_index_time_entries(created_time)

    index["reporting_orgs"] = get_reporting_orgs_for_datasets(context, datasets_in_bds, reporting_orgs_in_bds)

    return json.dumps(index, default=str, sort_keys=True, indent=True)


def create_index_time_entries(created_time: datetime) -> dict[str, Any]:
    return {"index_created": created_time, "index_created_unix_timestamp": int(created_time.timestamp())}


def get_reporting_orgs_for_datasets(
    context: dict, datasets_in_bds: dict[uuid.UUID, dict], reporting_orgs_in_bds: dict[uuid.UUID, dict]
) -> list:
    reporting_org_names_w_datasets = set([dataset["reporting_org_short_name"] for dataset in datasets_in_bds.values()])

    orgs_w_datasets = [
        {
            "id": org["id"],
            "short_name": org["short_name"],
            "human_readable_name": org["human_readable_name"],
            "iati_identifier": org["iati_identifier"],
        }
        for org in reporting_orgs_in_bds.values()
        if org["short_name"] in reporting_org_names_w_datasets
    ]

    return orgs_w_datasets


def get_dataset_index(context: dict, datasets_in_bds: dict[uuid.UUID, dict], index_type: str) -> list:
    return [get_index_entry(context, dataset, index_type) for _, dataset in datasets_in_bds.items()]


def get_index_entry(context: dict, dataset: dict, index_type: str) -> dict[str, Any]:

    if index_type == "minimal":
        dataset_index_entry = get_minimal_index_entry_from_dataset(context, dataset)
    else:
        dataset_index_entry = get_full_index_entry_from_dataset(context, dataset)

    dataset_index_entry["url_xml"] = None
    dataset_index_entry["url_zip"] = None

    if dataset_has_iati_xml_download(dataset):
        dataset_index_entry["url_xml"] = get_azure_blob_public_url(context, dataset, "xml")
        dataset_index_entry["url_zip"] = get_azure_blob_public_url(context, dataset, "zip")

    return dataset_index_entry


def get_dataset_index_name(context: dict, index_type: str) -> str:
    if index_type not in ["minimal", "full"]:
        raise ValueError("Unknown type for dataset index")

    return "datasets-{}".format(index_type)


def get_reporting_org_index_name(context: dict) -> str:
    return "reporting-orgs"


def get_minimal_index_entry_from_dataset(context: dict, dataset: dict) -> dict:
    return {k: v for k, v in dataset.items() if k in get_minimal_index_dataset_fields(context)}


def get_full_index_entry_from_dataset(context: dict, dataset: dict) -> dict:
    full_index_entry = {k: v for k, v in dataset.items() if k in get_full_index_dataset_source_fields(context)}

    field_from_json_str_to_object(full_index_entry, "most_recent_get_attempt_error_details", "download_error_details")

    field_from_json_str_to_object(full_index_entry, "most_recent_head_attempt_error_details", "head_error_details")

    return full_index_entry


def field_from_json_str_to_object(entry: dict, source_field: str, dest_field: str):
    entry[dest_field] = json.loads(
        entry[source_field] if entry[source_field] is not None and entry[source_field] != "" else "{}"
    )
    del entry[source_field]


def get_full_index_dataset_source_fields(context: dict) -> list[str]:
    return [
        "id",
        "short_name",
        "reporting_org_id",
        "reporting_org_short_name",
        "source_url",
        "hash",
        "hash_excluding_generated_timestamp",
        "last_update_check",
        "most_recent_head_attempt_datetime",
        "most_recent_head_attempt_http_status",
        "most_recent_head_attempt_error_details",
        "most_recent_get_attempt_datetime",
        "most_recent_get_attempt_http_status",
        "last_successful_download",
        "last_verified_on_server",
        "download_content_length",
        "download_initial_contents",
        "most_recent_get_attempt_error_details",
        "server_header_last_modified",
        "server_header_etag",
    ]


def get_minimal_index_dataset_fields(context: dict) -> list[str]:
    return [
        "id",
        "short_name",
        "reporting_org_id",
        "reporting_org_short_name",
        "source_url",
        "hash",
        "hash_excluding_generated_timestamp",
        "last_successful_download",
    ]
