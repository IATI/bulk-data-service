import datetime
import json
import uuid

from helpers.helpers import get_and_clear_up_context  # noqa: F401
from utilities.db import (
    get_dataset_in_bds,
    get_db_connection,
    get_reporting_org_in_bds,
    insert_or_update_dataset,
    insert_or_update_reporting_org,
)


def test_save_reporting_org_db_record(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    reporting_org_id = uuid.uuid4()

    dt = datetime.datetime(2025, 1, 2, 3, 4, 5, 0, datetime.timezone.utc)

    reporting_org = {
        "created_date": dt,
        "data_portal_url": "http://nautical-goodie.com",
        "default_licence_id": "cc-by",
        "description": "A harum aut.",
        "exclusions_policy_url": "https://quintessential-review.net",
        "first_publication_date": dt,
        "hq_country": "GB",
        "human_readable_name": "Et Et Rerum",
        "id": reporting_org_id,
        "organisation_identifier": "UN-KNOWN-ORG-123123",
        "organisation_type": "70",
        "region": "789",
        "reporting_source_type": "primary-source",
        "registration_service_reporting_org_metadata": "content",
        "registration_service_metadata_refreshed_datetime": dt,
        "short_name": "aidagency",
        "website": "https://little-licensing.name",
    }

    conn = get_db_connection(context)

    insert_or_update_reporting_org(conn, reporting_org)

    conn.close()

    reporting_org_from_db = get_reporting_org_in_bds(context, reporting_org["id"])

    assert reporting_org_from_db == reporting_org


def test_save_dataset_db_record(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    reporting_org_id = uuid.uuid4()
    dataset_id = uuid.uuid4()

    dt = datetime.datetime(2025, 1, 2, 3, 4, 5, 0, datetime.timezone.utc)

    reporting_org = {
        "created_date": dt,
        "data_portal_url": "http://nautical-goodie.com",
        "default_licence_id": "cc-by",
        "description": "A harum aut.",
        "exclusions_policy_url": "https://quintessential-review.net",
        "first_publication_date": dt,
        "hq_country": "GB",
        "human_readable_name": "Et Et Rerum",
        "id": reporting_org_id,
        "organisation_identifier": "UN-KNOWN-ORG-123123",
        "organisation_type": "70",
        "region": "789",
        "reporting_source_type": "primary-source",
        "registration_service_reporting_org_metadata": "content",
        "registration_service_metadata_refreshed_datetime": dt,
        "short_name": "aidagency",
        "website": "https://little-licensing.name",
    }

    dataset = {
        "id": dataset_id,
        "last_known_good_dataset_cached_dataset_xml_etag": '"HYJUHQNQIDID"',
        "last_known_good_dataset_cached_dataset_xml_url": "https://flawed-mozzarella.com",
        "last_known_good_dataset_cached_dataset_zip_etag": '"IQJQHWEWEKID"',
        "last_known_good_dataset_cached_dataset_zip_url": "http://unnatural-slate.org",
        "last_known_good_dataset_content_length": 423423,
        "last_known_good_dataset_downloaded": dt,
        "last_known_good_dataset_hash": "5c5d7e150145f34975485e6a4b862d5f238f7f84",
        "last_known_good_dataset_hash_excluding_generated_timestamp": "da0aaf9ea45e9d1e25880b4afa2b7bf9e4b5c501",
        "last_known_good_dataset_initial_contents": (
            "<?xml version='1.0' encoding='UTF-8'?><iati-activities generated-datetime="
            '"2025-07-21T14:21:48.87+02:00" version="2.03">  <iati-activity xml:lang="EN"'
        ),
        "last_known_good_dataset_server_header_etag": '"13e800-63a6f8654ebaf-gzip"',
        "last_known_good_dataset_server_header_last_modified": dt,
        "last_known_good_dataset_source_url": "http://sympathetic-conga.biz",
        "last_known_good_dataset_verified_on_server": dt,
        "last_update_check": dt,
        "licence_id": "cc-by",
        "most_recent_get_attempt_datetime": dt,
        "most_recent_get_attempt_error_occurred": False,
        "most_recent_get_attempt_http_status": 200,
        "most_recent_get_attempt_error_details": json.dumps({}),
        "most_recent_head_attempt_datetime": dt,
        "most_recent_head_attempt_error_occurred": False,
        "most_recent_head_attempt_http_status": 200,
        "most_recent_head_attempt_error_details": json.dumps({}),
        "short_name": "aidagency-culpa",
        "source_url": "http://jaunty-kick.net",
        "registration_service_dataset_metadata": "",
        "registration_service_metadata_refreshed_datetime": dt,
        "registration_service_name": "ckan-registry",
        "reporting_org_id": reporting_org_id,
        "reporting_org_short_name": "aidagency",
    }

    conn = get_db_connection(context)

    insert_or_update_reporting_org(conn, reporting_org)

    insert_or_update_dataset(conn, dataset)

    conn.close()

    dataset_from_db = get_dataset_in_bds(context, dataset["id"])

    assert dataset_from_db == dataset
