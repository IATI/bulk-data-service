import json
import uuid
from datetime import datetime
from typing import Any

from azure.storage.blob import BlobServiceClient

from utilities.azure import azure_upload_to_blob, get_azure_blob_public_url
from utilities.misc import dataset_has_iati_xml_download, get_timestamp, filter_dict_by_structure


def create_and_upload_indices(context: dict, datasets: dict[uuid.UUID, dict], reporting_orgs: dict[uuid.UUID, dict]):
    index_creation_time = get_timestamp()

    context["logger"].info("Creating indices")

    dataset_index_minimal = create_dataset_index_json(context, index_creation_time, datasets, "minimal")

    dataset_index_full = create_dataset_index_json(context, index_creation_time, datasets, "full")

    reporting_org_index = create_reporting_org_index_json(context, index_creation_time, datasets, reporting_orgs)

    upload_index_json_to_azure(context, get_dataset_index_name(context, "minimal"), dataset_index_minimal)

    upload_index_json_to_azure(context, get_dataset_index_name(context, "full"), dataset_index_full)

    upload_index_json_to_azure(context, get_reporting_org_index_name(context), reporting_org_index)

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

    index = create_index_created_entries(created_time)

    index["datasets"] = get_index_all_datasets(context, datasets_in_bds, index_type)

    return json.dumps(index, default=str, sort_keys=True, indent=True)


def create_reporting_org_index_json(
    context: dict,
    created_time: datetime,
    datasets_in_bds: dict[uuid.UUID, dict],
    reporting_orgs_in_bds: dict[uuid.UUID, dict],
) -> str:

    index = create_index_created_entries(created_time)

    index["reporting_orgs"] = get_reporting_orgs_for_datasets(context, datasets_in_bds, reporting_orgs_in_bds)

    return json.dumps(index, default=str, sort_keys=True, indent=True)


def create_index_created_entries(created_time: datetime) -> dict[str, Any]:
    return {"index_created": created_time, "index_created_unix_timestamp": int(created_time.timestamp())}


def get_reporting_orgs_for_datasets(
    context: dict, datasets: dict[uuid.UUID, dict], reporting_orgs: dict[uuid.UUID, dict]
) -> list:
    reporting_org_names_w_datasets = set([dataset["reporting_org_short_name"] for dataset in datasets.values()])

    orgs_w_datasets = [
        {
            "id": org["id"],
            "short_name": org["short_name"],
            "human_readable_name": org["human_readable_name"],
            "iati_identifier": org["iati_identifier"],
        }
        for org in reporting_orgs.values()
        if org["short_name"] in reporting_org_names_w_datasets
    ]

    return orgs_w_datasets


def get_index_all_datasets(context: dict, datasets: dict[uuid.UUID, dict], index_type: str) -> list:
    return [get_dataset_index_entry(context, dataset, index_type) for _, dataset in datasets.items()]


def get_dataset_index_entry(context: dict, dataset: dict, index_type: str) -> dict[str, Any]:

    minimal_index_structure = {
        "id": None,
        "short_name": None,
        "reporting_org_id": None,
        "reporting_org_short_name": None,
        "source_url": None,
        "license_id": None,
        "last_update_check": None,

        "last_known_good_dataset": {
            "downloaded": None,
            "verified_on_server": None,
            "hash": None,
            "hash_excluding_generated_timestamp": None,
            "cached_dataset_url_xml": None,
            "cached_dataset_url_zip": None
        }
    }

    index_entry = get_full_index_entry_from_dataset(context, dataset)

    if index_type == "minimal":
        index_entry = filter_dict_by_structure(index_entry, minimal_index_structure)

    return index_entry


def get_dataset_index_name(context: dict, index_type: str) -> str:
    if index_type not in ["minimal", "full"]:
        raise ValueError("Unknown type for dataset index")

    return "datasets-{}".format(index_type)


def get_reporting_org_index_name(context: dict) -> str:
    return "reporting-orgs"


def get_minimal_index_entry_from_dataset(context: dict, dataset: dict) -> dict:
    return get_full_index_entry_from_dataset(context, dataset)


def get_full_index_entry_from_dataset(context: dict, dataset: dict) -> dict:

    index_field_structure = get_full_index_structured_fields(context)

    full_index_entry = {}

    for _, index_prefix, _, _ in index_field_structure:
        if index_prefix is not None and index_prefix not in full_index_entry:
            full_index_entry[index_prefix] = {}

    for db_field, index_prefix, index_field, conversion_func in index_field_structure:
        target = full_index_entry if index_prefix is None else full_index_entry[index_prefix]
        target[index_field] = (
            dataset[db_field]
            if conversion_func is None
            else conversion_func(dataset, db_field, index_prefix, index_field)
        )

    return full_index_entry


def get_object_from_json_str(json_str: str | None):
    return json.loads(json_str if json_str is not None and json_str != "" else "{}")


def get_full_index_structured_fields(context: dict) -> list[Any]:

    def convert_to_object_from_json(dataset, db_field, index_prefix, index_field):
        return get_object_from_json_str(dataset[db_field])

    def create_cached_dataset_url(dataset, db_field, index_prefix, index_field):
        return (
            get_azure_blob_public_url(context, dataset, index_field[-3:])
            if dataset_has_iati_xml_download(dataset)
            else None
        )

    return [
        ("id", None, "id", None),
        ("short_name", None, "short_name", None),
        ("reporting_org_id", None, "reporting_org_id", None),
        ("reporting_org_short_name", None, "reporting_org_short_name", None),
        ("source_url", None, "source_url", None),
        ("license_id", None, "license_id", None),
        ("last_update_check", None, "last_update_check", None),
        ("most_recent_head_attempt_datetime", "most_recent_head_attempt", "datetime", None),
        ("most_recent_head_attempt_http_status", "most_recent_head_attempt", "http_status", None),
        (
            "most_recent_head_attempt_error_details",
            "most_recent_head_attempt",
            "error_details",
            convert_to_object_from_json,
        ),
        ("most_recent_get_attempt_datetime", "most_recent_get_attempt", "datetime", None),
        ("most_recent_get_attempt_http_status", "most_recent_get_attempt", "http_status", None),
        (
            "most_recent_get_attempt_error_details",
            "most_recent_get_attempt",
            "error_details",
            convert_to_object_from_json,
        ),
        ("last_known_good_dataset_hash", "last_known_good_dataset", "hash", None),
        (
            "last_known_good_dataset_hash_excluding_generated_timestamp",
            "last_known_good_dataset",
            "hash_excluding_generated_timestamp",
            None,
        ),
        ("last_known_good_dataset_downloaded", "last_known_good_dataset", "downloaded", None),
        ("last_known_good_dataset_verified_on_server", "last_known_good_dataset", "verified_on_server", None),
        ("last_known_good_dataset_content_length", "last_known_good_dataset", "content_length", None),
        ("last_known_good_dataset_initial_contents", "last_known_good_dataset", "initial_contents", None),
        (
            "last_known_good_dataset_server_header_last_modified",
            "last_known_good_dataset",
            "server_header_last_modified",
            None,
        ),
        ("last_known_good_dataset_server_header_etag", "last_known_good_dataset", "server_header_etag", None),
        ("last_known_good_dataset_source_url", "last_known_good_dataset", "source_url", None),
        (None, "last_known_good_dataset", "cached_dataset_url_xml", create_cached_dataset_url),
        (None, "last_known_good_dataset", "cached_dataset_url_zip", create_cached_dataset_url),
    ]


def get_minimal_index_dataset_fields(context: dict) -> list[str]:
    return [
        "id",
        "short_name",
        "reporting_org_id",
        "reporting_org_short_name",
        "source_url",
        "license_id",
        "last_known_good_dataset_hash",
        "last_known_good_dataset_hash_excluding_generated_timestamp",
        "last_known_good_dataset_downloaded",
    ]
