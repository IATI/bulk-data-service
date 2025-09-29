import json
import uuid
from typing import Any, Callable

from bulk_data_service.dataset import create_empty_dataset
from utilities.misc import format_timestamp_as_utc_str, get_object_from_json_str, get_timestamp_or_none


def get_new_dataset_from_dataset_registration_dto(
    registration_service_name: str,
    dataset_registration_dto: dict[str, str | None],
) -> dict[str, Any]:
    """Gets a new database db record from a dataset registration data transfer object

    Parameters
    ----------
    registration_service_name: str
        The source of the dataset registration info (ckan-registry, suitecrm, suitecrm-message)
    dataset_registration_dto : dict[str, str | None]
        Dict containing the dataset's registration fields. (As comes from the
        IATI MQ service or pulled in from the Registry)

    Returns
    -------
    dict[str, Any]
        Dict represented a BDS's copy of the dataset (all flat fields, with
        datetime and UUIDs as typed values).
    """
    return create_empty_dataset() | get_partial_dataset_from_dataset_registration_dto(
        registration_service_name, dataset_registration_dto
    )


def update_dataset_from_dataset_registration_dto(
    registration_service_name: str, dataset: dict[str, Any], dataset_registration_dto: dict[str, str | None]
):
    """Updates a database record from a dataset registration data transfer object

    Parameters
    ----------
    registration_service_name: str
        The source of the dataset registration info (ckan-registry, suitecrm, suitecrm-message)
    dataset: dict[str, Any]
        The Bulk Data Service dataset record to update
    dataset_registration_dto : dict[str, str | None]
        Dict containing the dataset's registration fields. (As comes from the
        IATI MQ service or pulled in from the Registry)
    """
    dataset.update(
        get_partial_dataset_from_dataset_registration_dto(registration_service_name, dataset_registration_dto)
    )


def get_partial_dataset_from_dataset_registration_dto(
    registration_service_name: str,
    dataset_registration_dto: dict[str, str | None],
) -> dict[str, Any]:
    """Gets a partial dataset with the registration fields populated from a dataset registration data transfer object

    Parameters
    ----------
    registration_service_name: str
        The source of the dataset registration info (ckan-registry, suitecrm, suitecrm-message)
    dataset_registration_dto : dict[str, str | None]
        Dict containing the dataset's registration fields. (As comes from the
        IATI MQ service or pulled in from the Registry)

    Returns
    -------
    dict[str, Any]
        Dict representing a partial dataset record with typed UUIDs.
    """
    return {
        "id": uuid.UUID(dataset_registration_dto["id"]),
        "short_name": dataset_registration_dto["short_name"],
        "reporting_org_id": uuid.UUID(dataset_registration_dto["reporting_org_id"]),
        "reporting_org_short_name": dataset_registration_dto["reporting_org_short_name"],
        "source_url": dataset_registration_dto["url"],
        "licence_id": dataset_registration_dto["licence_id"],
        "registration_service_name": registration_service_name,
        "registration_service_dataset_metadata": json.dumps(dataset_registration_dto),
    }


def convert_reporting_org_to_reporting_org_dto(reporting_org: dict[str, Any]) -> dict[str, str | None]:
    """Converts a reporting org record to a reporting org data transfer object

    The data transfer object is suitable for serialising and sending via the
    IATI MQ or printing to the reporting org index.

    Parameters
    ----------
    reporting_org : dict[str, Any]
        Dict containing a reporting org record as stored by the BDS.

    Returns
    -------
    dict[str, str | None]
        A reporting org data transfer object suitable for serialising.
    """
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
        "iati_identifier": reporting_org["organisation_identifier"],
        "organisation_identifier": reporting_org["organisation_identifier"],
        "organisation_type": reporting_org["organisation_type"],
        "region": reporting_org["region"],
        "reporting_source_type": reporting_org["reporting_source_type"],
        "short_name": reporting_org["short_name"],
        "website": reporting_org["website"],
    }


def convert_reporting_org_dto_to_reporting_org(reporting_org_dto: dict[str, str | None]) -> dict[str, Any]:
    """Converts a reporting org data transfer object to a reporting org record

    The data transfer object is suitable for serialising and sending via the
    IATI MQ or printing to the reporting org index.

    Parameters
    ----------
    reporting_org_dto : dict[str, str | None]
        A reporting org data transfer object as received from (e.g.) the IATI MQ.

    Returns
    -------
    dict[str, Any]
        A reporting org record suitable for saving to the DB.
    """
    return {
        "created_date": get_timestamp_or_none(reporting_org_dto["created_date"]),
        "data_portal_url": reporting_org_dto["data_portal_url"],
        "default_licence_id": reporting_org_dto["default_licence_id"],
        "description": reporting_org_dto["description"],
        "exclusions_policy_url": reporting_org_dto["exclusions_policy_url"],
        "first_publication_date": get_timestamp_or_none(reporting_org_dto["first_publication_date"]),
        "hq_country": reporting_org_dto["hq_country"],
        "human_readable_name": reporting_org_dto["human_readable_name"],
        "id": uuid.UUID(reporting_org_dto["id"]),
        "organisation_identifier": reporting_org_dto["organisation_identifier"],
        "organisation_type": reporting_org_dto["organisation_type"],
        "region": reporting_org_dto["region"],
        "reporting_source_type": reporting_org_dto["reporting_source_type"],
        "registration_service_reporting_org_metadata": json.dumps(reporting_org_dto),
        "short_name": reporting_org_dto["short_name"],
        "website": reporting_org_dto["website"],
    }


def get_full_dataset_hierarchical_dto_definition() -> list[tuple[str, str | None, str, Callable | None]]:
    """Gets the definition of the full hierarchical dataset data transfer object

    The definition is a list of 4-element tuples containing the following:
    - the source field in the BDS DB
    - the group / sub object under which this field will be placed in the output dict
    - the name of the field in the output
    - a conversion function

    Parameters
    ----------

    Returns
    -------
    list[tuple[str, str | None, str, Callable | None]]
        The definition of the structure for the full dataset data transfer object
    """
    return [
        ("id", None, "id", str),
        ("last_known_good_dataset_cached_dataset_xml_url", "last_known_good_dataset", "cached_dataset_url_xml", None),
        ("last_known_good_dataset_cached_dataset_xml_url", "last_known_good_dataset", "cached_dataset_xml_url", None),
        (
            "last_known_good_dataset_cached_dataset_zip_etag",
            "last_known_good_dataset",
            "cached_dataset_zip_etag",
            None,
        ),
        ("last_known_good_dataset_cached_dataset_zip_url", "last_known_good_dataset", "cached_dataset_zip_url", None),
        ("last_known_good_dataset_cached_dataset_zip_url", "last_known_good_dataset", "cached_dataset_url_zip", None),
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
        ("last_update_check", None, "last_update_check", None),
        ("licence_id", None, "licence_id", None),
        ("most_recent_head_attempt_datetime", "most_recent_head_attempt", "datetime", None),
        ("most_recent_head_attempt_error_occurred", "most_recent_head_attempt", "error_occurred", None),
        (
            "most_recent_head_attempt_error_details",
            "most_recent_head_attempt",
            "error_details",
            get_object_from_json_str,
        ),
        ("most_recent_head_attempt_http_status", "most_recent_head_attempt", "http_status", None),
        ("most_recent_get_attempt_datetime", "most_recent_get_attempt", "datetime", None),
        ("most_recent_get_attempt_error_occurred", "most_recent_get_attempt", "error_occurred", None),
        (
            "most_recent_get_attempt_error_details",
            "most_recent_get_attempt",
            "error_details",
            get_object_from_json_str,
        ),
        ("most_recent_get_attempt_http_status", "most_recent_get_attempt", "http_status", None),
        (
            "last_known_good_dataset_cached_dataset_xml_etag",
            "last_known_good_dataset",
            "cached_dataset_xml_etag",
            None,
        ),
        ("reporting_org_id", None, "reporting_org_id", str),
        ("reporting_org_short_name", None, "reporting_org_short_name", None),
        ("source_url", None, "source_url", None),
        ("short_name", None, "short_name", None),
    ]


def get_minimal_dataset_hierarchical_dto_definition() -> list[tuple[str, str | None, str, Callable | None]]:
    """Gets the definition of the minimal hierarchical dataset data transfer object

    The definition is a list of 4-element tuples containing the following:
    - the source field in the BDS DB
    - the group / sub object under which this field will be placed in the output dict
    - the name of the field in the output
    - a conversion function

    Parameters
    ----------

    Returns
    -------
    list[tuple[str, str | None, str, Callable | None]]
        The definition of the structure for the minimal dataset data transfer object
    """
    return [
        ("id", None, "id", str),
        ("last_update_check", None, "last_update_check", None),
        ("last_known_good_dataset_cached_dataset_xml_url", "last_known_good_dataset", "cached_dataset_url_xml", None),
        ("last_known_good_dataset_cached_dataset_zip_url", "last_known_good_dataset", "cached_dataset_url_zip", None),
        ("last_known_good_dataset_cached_dataset_xml_url", "last_known_good_dataset", "cached_dataset_xml_url", None),
        ("last_known_good_dataset_cached_dataset_zip_url", "last_known_good_dataset", "cached_dataset_zip_url", None),
        ("last_known_good_dataset_downloaded", "last_known_good_dataset", "downloaded", None),
        ("last_known_good_dataset_hash", "last_known_good_dataset", "hash", None),
        (
            "last_known_good_dataset_hash_excluding_generated_timestamp",
            "last_known_good_dataset",
            "hash_excluding_generated_timestamp",
            None,
        ),
        ("last_known_good_dataset_source_url", "last_known_good_dataset", "source_url", None),
        ("last_known_good_dataset_verified_on_server", "last_known_good_dataset", "verified_on_server", None),
        ("licence_id", None, "licence_id", None),
        ("short_name", None, "short_name", None),
        ("reporting_org_id", None, "reporting_org_id", str),
        ("reporting_org_short_name", None, "reporting_org_short_name", None),
        ("source_url", None, "source_url", None),
    ]


def get_full_dataset_check_result_dto(dataset: dict) -> dict[str, str | None]:
    """Get a full dataset check result data transfer object

    Parameters
    ----------
    dataset: dict[str, Any]

    Returns
    -------
    dict[str, str | None]
        A full dataset check result object suitable for Bulk Data Service index
        and for sending to the Dashboard via the MQ
    """

    dto_definition = get_full_dataset_hierarchical_dto_definition()

    return get_hierarhical_dto(dataset, dto_definition)


def get_minimal_dataset_check_result_dto(dataset: dict) -> dict[str, str | None]:
    """Get a minimal dataset check result data transfer object

    Parameters
    ----------
    dataset: dict[str, Any]

    Returns
    -------
    dict[str, str | None]
        A minimal dataset check result object suitable for Bulk Data Service index
    """

    dto_definition = get_minimal_dataset_hierarchical_dto_definition()

    return get_hierarhical_dto(dataset, dto_definition)


def get_hierarhical_dto(
    dataset: dict[str, Any], dto_definition: list[tuple[str, str | None, str, Callable | None]]
) -> dict[str, str | None]:
    """Gets a hierarchical data transfer object from a native Bulk Data Service dataset record

    Parameters
    ----------
    dataset: dict[str, Any]
        The dataset object
    dto_definition: list[tuple[str, str | None, str, Callable | None]]
        The definition to use for the data transfer object

    Returns
    -------
    dict[str, str | None]
        A hierarchical data transfer object
    """

    if dataset is None:
        return None

    full_index_entry = {}  # type: ignore[var-annotated]

    for _, output_group, _, _ in dto_definition:
        if output_group is not None and output_group not in full_index_entry:
            full_index_entry[output_group] = {}

    for source_field, output_group, output_field, conversion_func in dto_definition:
        target = full_index_entry if output_group is None else full_index_entry[output_group]
        target[output_field] = (
            dataset[source_field] if conversion_func is None else conversion_func(dataset[source_field])
        )

    return full_index_entry
