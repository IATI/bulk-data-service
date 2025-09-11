import json
import uuid
from datetime import datetime
from typing import Any

from azure.storage.blob import BlobServiceClient

from bulk_data_service.data_converters import (
    convert_reporting_org_to_reporting_org_dto,
    get_full_dataset_check_result_dto,
    get_minimal_dataset_check_result_dto,
)
from config.bds_context import BDSContext
from utilities.azure import azure_upload_to_blob
from utilities.misc import get_timestamp


def create_and_upload_indices(
    context: BDSContext, datasets: dict[uuid.UUID, dict], reporting_orgs: dict[uuid.UUID, dict]
):
    index_creation_time = get_timestamp()

    context.logger.info("Creating indices")

    dataset_index_minimal = create_dataset_index_json(context, index_creation_time, datasets, "minimal")

    dataset_index_full = create_dataset_index_json(context, index_creation_time, datasets, "full")

    reporting_org_index = create_reporting_org_index_json(context, index_creation_time, datasets, reporting_orgs)

    upload_index_json_to_azure(context, get_dataset_index_name(context, "minimal"), dataset_index_minimal)

    upload_index_json_to_azure(context, get_dataset_index_name(context, "full"), dataset_index_full)

    upload_index_json_to_azure(context, get_reporting_org_index_name(context), reporting_org_index)

    context.logger.info("Creation of indices finished")


def upload_index_json_to_azure(context: BDSContext, index_name: str, index_json: str):

    az_blob_service = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])

    azure_upload_to_blob(
        az_blob_service, context["AZURE_STORAGE_BLOB_CONTAINER_NAME"], index_name, index_json, "application/json"
    )

    az_blob_service.close()


def create_dataset_index_json(
    context: BDSContext,
    created_time: datetime,
    datasets_in_bds: dict[uuid.UUID, dict],
    index_type: str,
) -> str:

    index = create_index_created_entries(created_time)

    index["datasets"] = get_index_all_datasets(context, datasets_in_bds, index_type)

    return json.dumps(index, default=str, sort_keys=True, indent=True)


def create_reporting_org_index_json(
    context: BDSContext,
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
    context: BDSContext, datasets: dict[uuid.UUID, dict], reporting_orgs: dict[uuid.UUID, dict]
) -> list:
    reporting_org_names_w_datasets = set([dataset["reporting_org_short_name"] for dataset in datasets.values()])

    orgs_w_datasets = [
        convert_reporting_org_to_reporting_org_dto(org)
        for org in reporting_orgs.values()
        if org["short_name"] in reporting_org_names_w_datasets
    ]

    return orgs_w_datasets


def get_index_all_datasets(context: BDSContext, datasets: dict[uuid.UUID, dict], index_type: str) -> list:
    return [get_dataset_index_entry(context, dataset, index_type) for _, dataset in datasets.items()]


def get_dataset_index_entry(context: BDSContext, dataset: dict, index_type: str) -> dict[str, Any]:

    if index_type == "minimal":
        index_entry = get_minimal_dataset_check_result_dto(dataset)
    else:
        index_entry = get_full_dataset_check_result_dto(dataset)

    return index_entry


def get_dataset_index_name(context: BDSContext, index_type: str) -> str:
    if index_type not in ["minimal", "full"]:
        raise ValueError("Unknown type for dataset index")

    return "datasets-{}".format(index_type)


def get_reporting_org_index_name(context: BDSContext) -> str:
    return "reporting-orgs"
