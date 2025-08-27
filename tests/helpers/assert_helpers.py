from uuid import UUID

from utilities.misc import format_timestamp_as_utc_str


def assert_dataset_db_records_equal(dataset_db_record_1: dict, dataset_db_record_2: dict):
    assert dataset_db_record_1["id"] == dataset_db_record_2["id"]
    assert dataset_db_record_1["short_name"] == dataset_db_record_2["short_name"]
    assert dataset_db_record_1["licence_id"] == dataset_db_record_2["licence_id"]
    assert dataset_db_record_1["source_url"] == dataset_db_record_2["url"]
    assert dataset_db_record_1["reporting_org_id"] == dataset_db_record_2["reporting_org_id"]
    assert dataset_db_record_1["reporting_org_short_name"] == dataset_db_record_2["reporting_org_short_name"]


def assert_dataset_db_record_equal_dataset_mq_object(dataset_db_record: dict, dataset_mq_object: dict[str, str]):
    assert dataset_db_record["id"] == UUID(dataset_mq_object["id"])
    assert dataset_db_record["short_name"] == dataset_mq_object["short_name"]
    assert dataset_db_record["licence_id"] == dataset_mq_object["licence_id"]
    assert dataset_db_record["source_url"] == dataset_mq_object["url"]
    assert dataset_db_record["reporting_org_id"] == UUID(dataset_mq_object["reporting_org_id"])
    assert dataset_db_record["reporting_org_short_name"] == dataset_mq_object["reporting_org_short_name"]


def assert_dataset_db_record_content_differs_dataset_mq_object(
    dataset_db_record: dict, dataset_mq_object: dict[str, str]
):
    assert dataset_db_record["short_name"] != dataset_mq_object["short_name"]
    assert dataset_db_record["licence_id"] != dataset_mq_object["licence_id"]
    assert dataset_db_record["source_url"] != dataset_mq_object["url"]


def assert_reporting_org_plain_record_equal_db_record(
    reporting_org_plain_record: dict[str, str], reporting_org_db_record: dict
):
    assert reporting_org_plain_record["created_date"] == format_timestamp_as_utc_str(
        reporting_org_db_record["created_date"]
    )
    assert reporting_org_plain_record["data_portal_url"] == reporting_org_db_record["data_portal_url"]
    assert reporting_org_plain_record["default_licence_id"] == reporting_org_db_record["default_licence_id"]
    assert reporting_org_plain_record["description"] == reporting_org_db_record["description"]
    assert reporting_org_plain_record["exclusions_policy_url"] == reporting_org_db_record["exclusions_policy_url"]
    assert reporting_org_plain_record["first_publication_date"] == format_timestamp_as_utc_str(
        reporting_org_db_record["first_publication_date"]
    )
    assert reporting_org_plain_record["hq_country"] == reporting_org_db_record["hq_country"]
    assert reporting_org_plain_record["human_readable_name"] == reporting_org_db_record["human_readable_name"]
    assert reporting_org_plain_record["id"] == str(reporting_org_db_record["id"])
    assert reporting_org_plain_record["organisation_identifier"] == reporting_org_db_record["iati_identifier"]
    assert reporting_org_plain_record["organisation_type"] == reporting_org_db_record["organisation_type"]
    assert reporting_org_plain_record["region"] == reporting_org_db_record["region"]
    assert reporting_org_plain_record["reporting_source_type"] == reporting_org_db_record["reporting_source_type"]
    assert reporting_org_plain_record["short_name"] == reporting_org_db_record["short_name"]
    assert reporting_org_plain_record["website"] == reporting_org_db_record["website"]


def assert_reporting_org_db_record_content_differs_reporting_org_mq_object(
    reporting_org_db_record: dict, reporting_org_mq_object: dict[str, str]
):
    assert reporting_org_db_record["short_name"] != reporting_org_mq_object["short_name"]
    assert reporting_org_db_record["human_readable_name"] != reporting_org_mq_object["human_readable_name"]
    assert reporting_org_db_record["iati_identifier"] != reporting_org_mq_object["organisation_identifier"]
