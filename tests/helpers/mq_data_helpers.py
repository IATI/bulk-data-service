from datetime import datetime

from utilities.dataset_reporting_org_utils import convert_reporting_org_bds_record_to_index_record
from utilities.misc import get_current_timestamp_as_str


def get_dataset_message_payload(dataset, update_type) -> dict:
    if update_type == "deleted":
        msg_payload = generate_record_deleted_msg("dataset", dataset)
    else:
        msg_payload = generate_dataset_created_updated_payload(dataset, update_type)

    return msg_payload


def get_reporting_org_message_payload(reporting_org, update_type) -> dict:
    if update_type == "deleted":
        msg_payload = generate_record_deleted_msg("reporting_org", reporting_org)
    else:
        msg_payload = generate_reporting_org_created_updated_payload(reporting_org, update_type)

    return msg_payload


def generate_record_deleted_msg(record_type: str, data_record: dict) -> dict:
    return {
        "message_type": f"{record_type.upper()}_DELETED",
        "message_date": get_current_timestamp_as_str(),
        f"{record_type}": {
            "id": str(data_record["id"]),
        },
    }


def generate_dataset_created_updated_payload(dataset_db_record: dict, update_type: str) -> dict:
    return {
        "message_type": f"DATASET_{update_type.upper()}",
        "message_date": get_current_timestamp_as_str(),
        "dataset": {
            "id": str(dataset_db_record["id"]),
            "short_name": dataset_db_record["short_name"],
            "source_type": "primary-source",  # hard coded because BDS doesn't use it
            "licence_id": dataset_db_record["licence_id"],
            "url": dataset_db_record["source_url"],
            "last_url_update_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "last_metadata_update_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "reporting_org_id": str(dataset_db_record["reporting_org_id"]),
            "reporting_org_short_name": dataset_db_record["reporting_org_short_name"],
        },
    }


def generate_reporting_org_created_updated_payload(reporting_org_db_record: dict, update_type: str) -> dict:
    return {
        "message_type": f"REPORTING_ORG_{update_type.upper()}",
        "message_date": get_current_timestamp_as_str(),
        "reporting_org": convert_reporting_org_bds_record_to_index_record(reporting_org_db_record),
    }
