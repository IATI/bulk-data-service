import json
from datetime import datetime
from typing import Any

DATASET_NON_REGISTRATION_FIELDS = [
    "last_known_good_dataset_cached_dataset_xml_etag",
    "last_known_good_dataset_cached_dataset_xml_url",
    "last_known_good_dataset_cached_dataset_zip_etag",
    "last_known_good_dataset_cached_dataset_zip_url",
    "last_known_good_dataset_content_length",
    "last_known_good_dataset_downloaded",
    "last_known_good_dataset_hash",
    "last_known_good_dataset_hash_excluding_generated_timestamp",
    "last_known_good_dataset_initial_contents",
    "last_known_good_dataset_server_header_etag",
    "last_known_good_dataset_server_header_last_modified",
    "last_known_good_dataset_source_url",
    "last_known_good_dataset_verified_on_server",
    "last_update_check",
    "most_recent_get_attempt_datetime",
    "most_recent_get_attempt_error_details",
    "most_recent_get_attempt_error_occurred",
    "most_recent_get_attempt_http_status",
    "most_recent_head_attempt_datetime",
    "most_recent_head_attempt_error_details",
    "most_recent_head_attempt_error_occurred",
    "most_recent_head_attempt_http_status",
]

DATASET_REGISTRATION_FIELDS = [
    "id",
    "licence_id",
    "short_name",
    "source_url",
    "registration_service_dataset_metadata",
    "registration_service_metadata_refreshed_datetime",
    "registration_service_name",
    "reporting_org_id",
    "reporting_org_short_name",
]


def create_empty_dataset() -> dict[str, Any]:
    empty_ds = {
        k: None for k in DATASET_REGISTRATION_FIELDS + DATASET_NON_REGISTRATION_FIELDS
    }  # type: dict[str, str | bool | None]
    empty_ds["most_recent_get_attempt_error_details"] = make_http_attempt_error_details()
    empty_ds["most_recent_get_attempt_error_occurred"] = False
    empty_ds["most_recent_head_attempt_error_details"] = make_http_attempt_error_details()
    empty_ds["most_recent_head_attempt_error_occurred"] = False
    return empty_ds


def make_http_attempt_error_details(
    detailed_message: str | None = None,
    error_type: str | None = None,
    http_headers: dict = {},
    http_method: str | None = None,
    http_reason: str | None = None,
    http_status: int | None = None,
    summary_message: str | None = None,
    source_url: str | None = None,
) -> str:
    return json.dumps(
        {
            "detailed_message": detailed_message,
            "error_type": error_type,
            "http_headers": http_headers,
            "http_method": http_method,
            "http_reason": http_reason,
            "http_status": http_status,
            "summary_message": summary_message,
            "source_url": source_url,
        }
    )


def update_dataset_http_attempt_fields_as_error(
    dataset: dict,
    timestamp: datetime,
    http_method: str,
    detailed_message: str | None = None,
    error_type: str | None = None,
    http_headers: dict = {},
    http_reason: str | None = None,
    http_status: int | None = None,
    summary_message: str | None = None,
    source_url: str | None = None,
):
    dataset[f"most_recent_{http_method}_attempt_datetime"] = timestamp
    dataset[f"most_recent_{http_method}_attempt_error_occurred"] = True
    dataset[f"most_recent_{http_method}_attempt_http_status"] = http_status

    dataset[f"most_recent_{http_method}_attempt_error_details"] = make_http_attempt_error_details(
        error_type=error_type,
        detailed_message=detailed_message,
        http_headers=http_headers,
        http_method=http_method.upper(),
        http_reason=http_reason,
        http_status=http_status,
        summary_message=summary_message,
        source_url=source_url,
    )


def update_dataset_http_attempt_fields_as_success(
    dataset: dict, timestamp: datetime, http_method: str, http_status: int
):
    """Updates the set of most recent HEAD/GET attempt fields for success

    Parameters
    ----------
    dataset: dict[str, Any]
        The dataset record to update
    http_method: str
        The HTTP method. GET or HEAD.
    http_status:
        The HTTP status code

    """
    dataset[f"most_recent_{http_method}_attempt_datetime"] = timestamp
    dataset[f"most_recent_{http_method}_attempt_error_occurred"] = False
    dataset[f"most_recent_{http_method}_attempt_http_status"] = http_status

    dataset[f"most_recent_{http_method}_attempt_error_details"] = make_http_attempt_error_details()
