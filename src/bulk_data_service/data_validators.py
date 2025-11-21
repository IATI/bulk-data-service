from .data_validation_values import COUNTRY_CODELIST, LICENCE_LIST, ORGANISATION_TYPE_CODELIST, REGION_CODELIST


def validate_suitecrm_record_structure(record_type: str, suitecrm_record: dict) -> tuple[bool, str | None]:
    """Validate that a SuiteCRM record has all required fields and that they are of the correct length."""

    required_metadata_fields = {
        "dataset": [
            "iati_dataset_url",
            "iati_dataset_owner_org_id",
            "iati_dataset_owner_org_name",
            "iati_licence_id",
            "iati_short_name",
        ],
        "reporting_org": [
            "date_entered",
            "description",
            "iati_data_portal_url",
            "iati_default_licence_id",
            "iati_exclusions_policy_url",
            "iati_first_publish_date",
            "iati_hq_country",
            "iati_identifier",
            "iati_org_type",
            "iati_region",
            "iati_reporting_source_type",
            "iati_short_name",
            "name",
            "website",
        ],
    }

    if "id" not in suitecrm_record:
        return (False, f"SuiteCRM {record_type} without 'id' field: {suitecrm_record}")

    if "attributes" not in suitecrm_record:
        return (False, f"SuiteCRM {record_type} without 'attributes' dictionary: {suitecrm_record['id']}")

    for field in required_metadata_fields[record_type]:
        if field not in suitecrm_record["attributes"]:
            return (False, f"SuiteCRM {record_type} id: {suitecrm_record['id']} missing required field: {field}")

    return (True, None)


def validate_suitecrm_reporting_org_non_free_text_fields(
    suitecrm_reporting_org: dict,
) -> list[tuple[str | None, str | None]]:
    """Performs field-level validation on the non-free text SuiteCRM reporting org fields."""

    validation_errors: list[tuple[str | None, str | None]] = []

    if not _value_is_null_or_in_list(suitecrm_reporting_org["attributes"]["iati_default_licence_id"], LICENCE_LIST):
        validation_errors.append(
            (
                "iati_default_licence_id",
                f"SuiteCRM reporting_org id: {suitecrm_reporting_org['id']} has "
                f"invalid value for field iati_default_licence_id",
            )
        )

    if not _value_is_null_or_in_list(suitecrm_reporting_org["attributes"]["iati_hq_country"], COUNTRY_CODELIST):
        validation_errors.append(
            (
                "iati_hq_country",
                f"SuiteCRM reporting_org id: {suitecrm_reporting_org['id']} has "
                f"invalid value for codelist field iati_hq_country",
            )
        )

    if not _value_is_null_or_in_list(
        suitecrm_reporting_org["attributes"]["iati_org_type"], ORGANISATION_TYPE_CODELIST
    ):
        validation_errors.append(
            (
                "iati_org_type",
                f"SuiteCRM reporting_org id: {suitecrm_reporting_org['id']} has "
                f"invalid value for codelist field iati_org_type",
            )
        )

    if not _value_is_null_or_in_list(suitecrm_reporting_org["attributes"]["iati_region"], REGION_CODELIST):
        validation_errors.append(
            (
                "iati_region",
                f"SuiteCRM reporting_org id: {suitecrm_reporting_org['id']} has "
                f"invalid value for codelist field iati_region",
            )
        )

    if suitecrm_reporting_org["attributes"]["iati_reporting_source_type"] is not None:
        source_type = suitecrm_reporting_org["attributes"]["iati_reporting_source_type"].replace("-", "_")
        if source_type not in ["primary_source", "secondary_source"]:
            validation_errors.append(
                (
                    "iati_reporting_source_type",
                    f"SuiteCRM reporting_org id: {suitecrm_reporting_org['id']} has "
                    f"invalid value for iati_reporting_source_type: {source_type}",
                )
            )

    return validation_errors


def _value_is_null_or_in_list(value: str | None, valid_list: list[str]) -> bool:
    if value is None:
        return True
    return value in valid_list
