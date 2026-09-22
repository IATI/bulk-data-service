import json
import random
import uuid
from datetime import datetime

from libsuitecrm import Filter, SuiteCRM  # type: ignore

from bulk_data_service.data_validators import (
    validate_suitecrm_record_structure,
    validate_suitecrm_reporting_org_non_free_text_fields,
)
from config.bds_context import BDSContext
from utilities.misc import get_timestamp_or_none, is_str_valid_uuid


def fetch_datasets_metadata(
    context: BDSContext, reporting_orgs: dict, refresh_timestamp: datetime
) -> dict[uuid.UUID, dict]:

    crm: SuiteCRM = context.service_factory.get_suitecrm_client()

    crm.fetch_access_token()

    context.logger.info("Fetching all dataset metadata using the libsuitecrm library...")

    filters = Filter().equal("iati_visibility", "public")

    suitecrm_dataset_records = [r for r in crm.get_all_records("IATI_Datasets", filters=filters)]

    crm.logout()

    if context.RUN_FOR_N_DATASETS is not None:
        suitecrm_dataset_records = suitecrm_dataset_records[: context.RUN_FOR_N_DATASETS]
        context.logger.info(f"--run-for-n-datasets is set so only processing {context.RUN_FOR_N_DATASETS} datasets.")

    random.shuffle(suitecrm_dataset_records)

    results = {}

    for record in suitecrm_dataset_records:

        (is_valid, error_msg) = validate_suitecrm_record_structure("dataset", record)

        if not is_valid:
            context.logger.error(f"{error_msg}", extra={"bds_alert_group": "suitecrm-invalid-dataset-record"})
            continue

        if not is_str_valid_uuid(record["attributes"].get("iati_dataset_owner_org_id", "")):
            context.logger.error(
                f"SuiteCRM dataset id: {record['id']} has invalid reporting org id: "
                f"{record['attributes'].get('iati_dataset_owner_org_id', '')}. Skipping.",
                extra={"bds_alert_group": "suitecrm-invalid-reporting-org-id"},
            )
            continue

        owning_org = reporting_orgs.get(uuid.UUID(record["attributes"]["iati_dataset_owner_org_id"]), None)
        if context.RUN_FOR_SINGLE_REPORTING_ORG is not None and owning_org is None:
            continue
        if owning_org is None:
            context.logger.error(
                f"SuiteCRM dataset id: {record['id']} has reporting org id: "
                f"{record['attributes'].get('iati_dataset_owner_org_id', '')} but that reporting org does not exist "
                "or is not discoverable. Skipping.",
                extra={"bds_alert_group": "suitecrm-orphan-dataset"},
            )
            continue

        results[uuid.UUID(record["id"])] = convert_suitecrm_dataset_to_bds_record(
            record, owning_org, refresh_timestamp
        )

    context.logger.info("Fetched metadata for {} datasets".format(len(results)))

    return results


def fetch_reporting_orgs_metadata(context: BDSContext, refresh_timestamp: datetime) -> dict[uuid.UUID, dict]:

    crm: SuiteCRM = context.service_factory.get_suitecrm_client()

    crm.fetch_access_token()

    context.logger.info("Fetching all reporting org metadata using the libsuitecrm library...")

    filters = Filter().equal("iati_registry_discoverable", "1").equal("iati_registry_approved", 1)
    suitecrm_reporting_org_records = [r for r in crm.get_all_records("Accounts", filters=filters)]

    if context.RUN_FOR_SINGLE_REPORTING_ORG is not None:
        suitecrm_reporting_org_records = [
            o
            for o in suitecrm_reporting_org_records
            if o.get("attributes", {}).get("iati_short_name", "") == context.RUN_FOR_SINGLE_REPORTING_ORG
        ]
        context.logger.info(
            "--run-for-single-reporting-org is set so only "
            f"processing reporting org '{context.RUN_FOR_SINGLE_REPORTING_ORG}'."
        )

    crm.logout()

    results = {}

    for record in suitecrm_reporting_org_records:

        (is_valid_structure, error_msg) = validate_suitecrm_record_structure("reporting_org", record)

        if not is_valid_structure:
            context.logger.error(f"{error_msg}", extra={"bds_alert_group": "suitecrm-invalid-reporting-org-record"})
            continue

        validation_errors = validate_suitecrm_reporting_org_non_free_text_fields(record)

        # If a non-free text field is invalid, log a warning and nullify the field value. We can't skip the
        # reporting_org because then we wouldn't be able to add any datasets linkted to it.
        if len(validation_errors) > 0:
            for field, error_msg in validation_errors:
                context.logger.warning(f"{error_msg}")
                record["attributes"][field] = None  # Nullify invalid field values

        results[uuid.UUID(record["id"])] = convert_suitecrm_reporting_org_to_bds_record(record, refresh_timestamp)

    context.logger.info("Fetched metadata for {} reporting orgs".format(len(results)))

    return results


def convert_suitecrm_dataset_to_bds_record(suitecrm_dataset: dict, owning_org: dict, refresh_timestamp: datetime):

    dataset_metadata = suitecrm_dataset["attributes"]

    return {
        "id": uuid.UUID(suitecrm_dataset["id"]),
        "licence_id": dataset_metadata.get("iati_licence_id", None),
        "reporting_org_id": uuid.UUID(dataset_metadata.get("iati_dataset_owner_org_id", None)),
        "reporting_org_short_name": owning_org["short_name"],
        "registration_service_dataset_metadata": json.dumps(dataset_metadata),
        "registration_service_name": "suitecrm-registry",
        "registration_service_metadata_refreshed_datetime": refresh_timestamp,
        "short_name": dataset_metadata.get("iati_short_name", None),
        "source_url": dataset_metadata.get("iati_dataset_url", None),
    }


def convert_suitecrm_reporting_org_to_bds_record(suitecrm_reporting_org: dict, refresh_timestamp: datetime):

    org_metadata = suitecrm_reporting_org["attributes"]

    return {
        "created_date": get_timestamp_or_none(org_metadata.get("date_entered", None)),
        "data_portal_url": org_metadata.get("iati_data_portal_url", None),
        "default_licence_id": org_metadata.get("iati_default_licence_id", None),
        "description": org_metadata.get("description", None),
        "exclusions_policy_url": org_metadata.get("iati_exclusions_policy_url", None),
        "first_publication_date": get_timestamp_or_none(org_metadata.get("iati_first_publish_date", None)),
        "hq_country": org_metadata.get("iati_hq_country", None),
        "human_readable_name": org_metadata["name"],
        "id": uuid.UUID(suitecrm_reporting_org["id"]),
        "organisation_identifier": org_metadata.get("iati_identifier", None),
        "organisation_type": org_metadata.get("iati_org_type", None),
        "region": org_metadata.get("iati_region", None),
        "registration_service_metadata_refreshed_datetime": refresh_timestamp,
        "registration_service_reporting_org_metadata": json.dumps(suitecrm_reporting_org),
        "reporting_source_type": org_metadata.get("iati_reporting_source_type", None),
        "short_name": org_metadata.get("iati_short_name", None),
        "website": org_metadata.get("website", None),
    }
