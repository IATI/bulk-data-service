from datetime import datetime


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
        "message_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        f"{record_type}": {
            "id": str(data_record["id"]),
        },
    }


def generate_dataset_created_updated_payload(dataset_db_record: dict, update_type: str) -> dict:
    return {
        "message_type": f"DATASET_{update_type.upper()}",
        "message_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
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
        "message_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reporting_org": {
            "id": str(reporting_org_db_record["id"]),
            "short_name": reporting_org_db_record["short_name"],
            "human_readable_name": reporting_org_db_record["human_readable_name"],
            "hq_country": "London",  # hard coded, BDS doesn't use
            "region": "Europe, regional",  # BDS doesn't use
            "iati_organisation_identifier": reporting_org_db_record["iati_identifier"],
            "iati_organisation_type": "Regional NGO",  # BDS doesn't use
            "data_portal_url": "https://www.example.org/data-portal",  # BDS doesn't use
            "exclusions_policy_url": "https://www.example.org/exclusions-policy",  # BDS doesn't use
            "reporting_source_type": "primary-source",  # BDS doesn't use
            "default_licence_id": "gpl-3.0",  # BDS doesn't use
            "contact_email": "org.admin@example.org",  # BDS doesn't use
            "address": "Fake Address",  # BDS doesn't use
            "phone": "01234 567 890",  # BDS doesn't use
            "first_publication_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),  # BDS doesn't use
            "number_of_published_datasets": 1,  # BDS doesn't use
        },
    }
