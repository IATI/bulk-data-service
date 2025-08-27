import json
import uuid
from typing import Any

from utilities.misc import format_timestamp_as_utc_str, get_timestamp_or_none


def get_new_dataset_db_record_from_mq_dataset(mq_dataset: dict[str, Any]) -> dict[str, Any]:
    dataset_db_record = translate_mq_dataset_to_dataset_db_record_metadata(mq_dataset)
    blank_dataset_db_record_non_registration_fields(dataset_db_record)
    return dataset_db_record


def get_reporting_org_db_record_from_mq_reporting_org(mq_reporting_org: dict[str, Any]) -> dict[str, Any]:
    return convert_mq_reporting_org_to_reporting_org_bds_record(mq_reporting_org)


def get_updated_dataset_db_record_from_mq_dataset(
    dataset_db_record: dict[str, Any], mq_dataset: dict[str, Any]
) -> dict[str, Any]:
    return dataset_db_record | translate_mq_dataset_to_dataset_db_record_metadata(mq_dataset)


def convert_reporting_org_bds_record_to_index_record(reporting_org: dict[str, Any]) -> dict:
    return {
        "created_date": format_timestamp_as_utc_str(reporting_org["created_date"]),
        "data_portal_url": reporting_org["data_portal_url"],
        "default_licence_id": reporting_org["default_licence_id"],
        "description": reporting_org["description"],
        "exclusions_policy_url": reporting_org["exclusions_policy_url"],
        "first_publication_date": format_timestamp_as_utc_str(reporting_org["first_publication_date"]),
        "hq_country": reporting_org["hq_country"],
        "human_readable_name": reporting_org["human_readable_name"],
        "id": str(reporting_org["id"]),
        "iati_identifier": reporting_org["iati_identifier"],
        "organisation_identifier": reporting_org["iati_identifier"],
        "organisation_type": reporting_org["organisation_type"],
        "region": reporting_org["region"],
        "reporting_source_type": reporting_org["reporting_source_type"],
        "short_name": reporting_org["short_name"],
        "website": reporting_org["website"],
    }


def convert_mq_reporting_org_to_reporting_org_bds_record(mq_reporting_org: dict[str, Any]) -> dict[str, Any]:

    return {
        "created_date": get_timestamp_or_none(mq_reporting_org["created_date"]),
        "data_portal_url": mq_reporting_org["data_portal_url"],
        "default_licence_id": mq_reporting_org["default_licence_id"],
        "description": mq_reporting_org["description"],
        "exclusions_policy_url": mq_reporting_org["exclusions_policy_url"],
        "first_publication_date": get_timestamp_or_none(mq_reporting_org["first_publication_date"]),
        "hq_country": mq_reporting_org["hq_country"],
        "human_readable_name": mq_reporting_org["human_readable_name"],
        "id": uuid.UUID(mq_reporting_org["id"]),
        "iati_identifier": mq_reporting_org["organisation_identifier"],
        "organisation_type": mq_reporting_org["organisation_type"],
        "region": mq_reporting_org["region"],
        "reporting_source_type": mq_reporting_org["reporting_source_type"],
        "registration_service_reporting_org_metadata": json.dumps(mq_reporting_org),
        "short_name": mq_reporting_org["short_name"],
        "website": mq_reporting_org["website"],
    }


def translate_mq_dataset_to_dataset_db_record_metadata(mq_dataset: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": uuid.UUID(mq_dataset["id"]),
        "short_name": mq_dataset["short_name"],
        "reporting_org_id": uuid.UUID(mq_dataset["reporting_org_id"]),
        "reporting_org_short_name": mq_dataset["reporting_org_short_name"],
        "source_url": mq_dataset["url"],
        "licence_id": mq_dataset["licence_id"],
        "registration_service_name": "REGISTRY_CHANGE_MESSAGE",
        "registration_service_dataset_metadata": json.dumps(mq_dataset),
    }


def blank_dataset_db_record_non_registration_fields(dataset: dict[str, Any]):
    non_registration_fields = [
        "last_update_check",
        "last_known_good_dataset_hash",
        "last_known_good_dataset_hash_excluding_generated_timestamp",
        "last_known_good_dataset_verified_on_server",
        "last_known_good_dataset_downloaded",
        "last_known_good_dataset_server_header_last_modified",
        "last_known_good_dataset_server_header_etag",
        "last_known_good_dataset_content_length",
        "last_known_good_dataset_initial_contents",
        "last_known_good_dataset_source_url",
        "most_recent_head_attempt_datetime",
        "most_recent_head_attempt_http_status",
        "most_recent_head_attempt_error_details",
        "most_recent_head_attempt_server_headers",
        "most_recent_get_attempt_datetime",
        "most_recent_get_attempt_http_status",
        "most_recent_get_attempt_error_details",
        "most_recent_get_attempt_server_headers",
    ]
    for field in non_registration_fields:
        dataset[field] = None
