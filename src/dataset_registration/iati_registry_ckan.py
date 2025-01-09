import json
import random
import uuid
from logging import Logger
from typing import Any

import requests

from utilities.http import http_get_json
from utilities.misc import is_str_valid_uuid


def fetch_reporting_orgs_metadata(context: dict) -> dict[uuid.UUID, dict]:
    session = requests.Session()

    url = context["DATA_REGISTRY_PUBLISHER_METADATA_URL"]

    reporting_org_metadata = {}

    reporting_orgs_metadata = http_get_json(session, url, 120, True)

    reporting_orgs_w_valid_ids = [org for org in reporting_orgs_metadata["result"] if is_str_valid_uuid(org["id"])]

    reporting_org_metadata = {
        uuid.UUID(org["id"]): convert_ckan_reporting_org_metadata(org) for org in reporting_orgs_w_valid_ids
    }

    return reporting_org_metadata


def convert_ckan_reporting_org_metadata(reporting_org: dict):
    return {
        "id": reporting_org["id"],
        "short_name": reporting_org["name"],
        "iati_identifier": reporting_org["publisher_iati_id"],
        "human_readable_name": reporting_org["title"],
        "registration_service_reporting_org_metadata": json.dumps(reporting_org),
    }


def fetch_datasets_metadata(context: dict, reporting_orgs: dict) -> dict[uuid.UUID, dict]:
    session = requests.Session()

    datasets_list_from_registry = fetch_datasets_metadata_from_iati_registry(context, session)

    random.shuffle(datasets_list_from_registry)

    cleaned_datasets_metadata = clean_datasets_metadata(context["logger"], datasets_list_from_registry)

    add_publisher_metadata(cleaned_datasets_metadata, reporting_orgs)

    datasets_metadata = convert_datasets_metadata(cleaned_datasets_metadata)

    return datasets_metadata


def fetch_datasets_metadata_from_iati_registry(context: dict, session: requests.Session) -> list[dict]:

    api_url = context["DATA_REGISTRY_BASE_URL"]

    number_of_datasets = http_get_json(session, api_url + "?rows=1")["result"]["count"]

    if context["run_for_n_datasets"] is not None:
        number_of_datasets = min(number_of_datasets, int(context["run_for_n_datasets"]))

    batch_size = number_of_datasets if number_of_datasets < 1000 else 1000

    datasets_metadata_downloaded = 0
    datasets_metadata = []

    while datasets_metadata_downloaded < number_of_datasets:
        response = http_get_json(
            session, "{}?rows={}&start={}".format(api_url, batch_size, str(datasets_metadata_downloaded))
        )

        datasets_metadata.extend(response["result"]["results"])

        datasets_metadata_downloaded += len(response["result"]["results"])

    return datasets_metadata


def add_publisher_metadata(datasets_from_registry: list[dict[str, Any]], reporting_orgs: dict[uuid.UUID, dict]):
    for registry_dataset in datasets_from_registry:
        publisher_metadata = ""
        if "organization" in registry_dataset and "id" in registry_dataset["organization"]:
            publisher_metadata = get_publisher_metadata_as_str(reporting_orgs, registry_dataset["organization"]["id"])
        registry_dataset["registration_service_publisher_metadata"] = publisher_metadata


def get_publisher_metadata_as_str(reporting_orgs: dict[uuid.UUID, dict], publisher_id: str) -> str:
    return (
        reporting_orgs[uuid.UUID(publisher_id)]["registration_service_reporting_org_metadata"]
        if uuid.UUID(publisher_id) in reporting_orgs
        else "{}"
    )


def clean_datasets_metadata(logger: Logger, datasets_from_registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cleans the list of datasets from the IATI Registry

    The data from the Registry should never be missing the values below, so if it is, we log an error
    and skip that item. This allows for tidy conversion using dictionary comprehension."""

    cleaned_datasets_metadata = []

    for dataset_metadata in datasets_from_registry:
        if not ckan_dataset_is_valid(logger, dataset_metadata):
            continue

        cleaned_datasets_metadata.append(dataset_metadata)

    return cleaned_datasets_metadata


def ckan_dataset_is_valid(logger: Logger, registry_dataset: dict[str, Any]) -> bool:
    valid = True

    for field in ["id", "name", "organization"]:
        if not ckan_field_is_valid(registry_dataset[field]):
            logger.error(
                "dataset id: {} - Dataset with empty {} received from IATI Registry. "
                "Skipping.".format(registry_dataset["id"], field)
            )
            valid = False

    if ckan_field_is_valid(registry_dataset["organization"]) and not ckan_field_is_valid(
        registry_dataset["organization"]["id"]
    ):  # noqa: E129
        logger.error(
            "dataset id: {} - Dataset with empty organisation.id received from "
            "IATI Registry. Skipping.".format(registry_dataset["id"])
        )
        valid = False

    if ckan_field_is_valid(registry_dataset["organization"]) and not ckan_field_is_valid(
        registry_dataset["organization"]["name"]
    ):  # noqa: E129
        logger.error(
            "dataset id: {} - Dataset with empty organisation.name received from "
            "IATI Registry. Skipping.".format(registry_dataset["id"])
        )
        valid = False

    if (
        not ckan_field_is_valid(registry_dataset["extras"])
        or len([x for x in registry_dataset["extras"] if x["key"] == "filetype"]) == 0
    ):  # noqa: E129
        logger.warning(
            "dataset id: {} - Dataset with no filetype specified "
            "received from IATI Registry. Skipping.".format(registry_dataset["id"])
        )
        valid = False

    return valid


def ckan_field_is_valid(value: Any) -> bool:
    return value is not None and value != "None" and value != ""


def convert_datasets_metadata(datasets_from_registry: list[dict]) -> dict[uuid.UUID, dict]:

    registered_datasets = {
        uuid.UUID(dataset["id"]): {
            "id": uuid.UUID(dataset["id"]),
            "short_name": dataset["name"],
            "reporting_org_id": uuid.UUID(dataset["organization"]["id"]),
            "reporting_org_short_name": dataset["organization"]["name"],
            "source_url": get_source_url(dataset),
            "type": list(filter(lambda x: x["key"] == "filetype", dataset["extras"]))[0]["value"],
            "registration_service_dataset_metadata": json.dumps(
                {k: dataset[k] for k in dataset if k != "registration_service_publisher_metadata"}
            ),
            "registration_service_publisher_metadata": (
                dataset["registration_service_publisher_metadata"]
                if "registration_service_publisher_metadata" in dataset
                else ""
            ),
            "registration_service_name": "ckan-registry",
        }
        for dataset in datasets_from_registry
    }

    return registered_datasets


def get_source_url(ckan_dataset: dict) -> str:
    if (
        "resources" in ckan_dataset
        and isinstance(ckan_dataset["resources"], list)
        and len(ckan_dataset["resources"]) > 0
        and "url" in ckan_dataset["resources"][0]
    ):  # noqa: E129
        return ckan_dataset["resources"][0].get("url", "")
    return ""
