from uuid import UUID


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


def assert_reporting_org_db_record_equal_reporting_org_mq_object(
    reporting_org_db_record: dict, reporting_org_mq_object: dict[str, str]
):
    assert reporting_org_db_record["id"] == UUID(reporting_org_mq_object["id"])
    assert reporting_org_db_record["short_name"] == reporting_org_mq_object["short_name"]
    assert reporting_org_db_record["human_readable_name"] == reporting_org_mq_object["human_readable_name"]
    assert reporting_org_db_record["iati_identifier"] == reporting_org_mq_object["iati_organisation_identifier"]


def assert_reporting_org_db_record_content_differs_reporting_org_mq_object(
    reporting_org_db_record: dict, reporting_org_mq_object: dict[str, str]
):
    assert reporting_org_db_record["short_name"] != reporting_org_mq_object["short_name"]
    assert reporting_org_db_record["human_readable_name"] != reporting_org_mq_object["human_readable_name"]
    assert reporting_org_db_record["iati_identifier"] != reporting_org_mq_object["iati_organisation_identifier"]
