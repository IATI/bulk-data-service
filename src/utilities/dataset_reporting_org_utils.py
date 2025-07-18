import json
import uuid
from datetime import datetime
from typing import Any


def get_new_dataset_db_record_from_mq_dataset(mq_dataset: dict[str, Any]) -> dict[str, Any]:
    dataset_db_record = translate_mq_dataset_to_dataset_db_record_metadata(mq_dataset)
    blank_dataset_db_record_non_registration_fields(dataset_db_record)
    return dataset_db_record


def get_updated_dataset_db_record_from_mq_dataset(
    dataset_db_record: dict[str, Any], mq_dataset: dict[str, Any]
) -> dict[str, Any]:
    return dataset_db_record | translate_mq_dataset_to_dataset_db_record_metadata(mq_dataset)


def translate_mq_dataset_to_dataset_db_record_metadata(mq_dataset: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": mq_dataset["id"],
        "short_name": mq_dataset["short_name"],
        "reporting_org_id": mq_dataset["reporting_org_id"],
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
