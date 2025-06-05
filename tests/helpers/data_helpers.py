import datetime
import json
import uuid

from bulk_data_service.dataset_indexing import get_object_from_json_str
from utilities.azure import get_azure_blob_public_url
from utilities.misc import dataset_has_iati_xml_download


def check_most_recent_get_attempt_downloaded_but_non_iati(dataset: dict):
    assert dataset["most_recent_get_attempt_datetime"] is not None
    assert dataset["most_recent_get_attempt_http_status"] == 200
    error_details = json.loads(dataset["most_recent_get_attempt_error_details"])
    assert error_details["message"] == "File does not appear to be IATI XML"


def check_most_recent_get_attempt_for_success(dataset: dict):
    assert dataset["most_recent_get_attempt_error_details"] is None
    assert dataset["most_recent_get_attempt_http_status"] == 200


def check_last_known_good_dataset_values_are_set(dataset: dict):
    assert dataset["last_known_good_dataset_downloaded"] is not None
    assert dataset["last_known_good_dataset_downloaded"] == dataset["last_known_good_dataset_verified_on_server"]
    assert dataset["last_known_good_dataset_hash"] is not None
    assert dataset["last_known_good_dataset_hash_excluding_generated_timestamp"] is not None
    assert dataset["last_known_good_dataset_content_length"] > 0
    assert dataset["last_known_good_dataset_initial_contents"] is not None
    assert dataset["last_known_good_dataset_server_header_last_modified"] is not None
    assert dataset["last_known_good_dataset_server_header_etag"] is not None
    assert dataset["last_known_good_dataset_source_url"] is not None


def check_last_known_good_dataset_values_are_unset(dataset: dict):
    assert dataset["last_known_good_dataset_downloaded"] is None
    assert dataset["last_known_good_dataset_verified_on_server"] is None
    assert dataset["last_known_good_dataset_hash"] is None
    assert dataset["last_known_good_dataset_hash_excluding_generated_timestamp"] is None
    assert dataset["last_known_good_dataset_content_length"] is None
    assert dataset["last_known_good_dataset_initial_contents"] is None
    assert dataset["last_known_good_dataset_server_header_last_modified"] is None
    assert dataset["last_known_good_dataset_server_header_etag"] is None
    assert dataset["last_known_good_dataset_source_url"] is None


def check_index_registration_fields(dataset: dict, dataset_index_item: dict):
    assert uuid.UUID(dataset_index_item["id"]) == dataset["id"]
    assert dataset_index_item["short_name"] == dataset["short_name"]
    assert uuid.UUID(dataset_index_item["reporting_org_id"]) == dataset["reporting_org_id"]
    assert dataset_index_item["reporting_org_short_name"] == dataset["reporting_org_short_name"]
    assert dataset_index_item["source_url"] == dataset["source_url"]
    assert dataset_index_item["licence_id"] == dataset["licence_id"]


def check_index_most_recent_fields(context: dict, field_grouping: str, dataset: dict, dataset_index_item: dict):
    field_group = "most_recent_{}_attempt".format(field_grouping)
    assert field_group in dataset_index_item
    assert dataset_index_item[field_group]["datetime"] == get_datetime_as_str_or_none(dataset["{}_datetime".format(field_group)])
    assert dataset_index_item[field_group]["http_status"] == dataset["{}_http_status".format(field_group)]
    assert dataset_index_item[field_group]["error_details"] == get_object_from_json_str(dataset["{}_error_details".format(field_group)])


def check_index_last_known_good_fields(context: dict, dataset: dict, dataset_index_item: dict):
    assert "last_known_good_dataset" in dataset_index_item
    assert dataset_index_item["last_known_good_dataset"]["downloaded"] == get_datetime_as_str_or_none(dataset["last_known_good_dataset_downloaded"])
    assert dataset_index_item["last_known_good_dataset"]["verified_on_server"] == get_datetime_as_str_or_none(dataset["last_known_good_dataset_verified_on_server"])
    assert dataset_index_item["last_known_good_dataset"]["hash"] == dataset["last_known_good_dataset_hash"]
    assert dataset_index_item["last_known_good_dataset"]["hash_excluding_generated_timestamp"] == dataset["last_known_good_dataset_hash_excluding_generated_timestamp"]
    assert dataset_index_item["last_known_good_dataset"]["cached_dataset_url_xml"] == (get_azure_blob_public_url(context, dataset, "xml") if dataset_has_iati_xml_download(dataset) else None)
    assert dataset_index_item["last_known_good_dataset"]["cached_dataset_url_zip"] == (get_azure_blob_public_url(context, dataset, "zip") if dataset_has_iati_xml_download(dataset) else None)


def get_datetime_as_str_or_none(date: datetime.datetime | None) -> str | None:
    return (str(date) if date is not None else None)


def check_dataset_fields(expected_fields: list, dataset: dict):
    for field, expected_value in expected_fields:
        assert dataset[field] == expected_value


def check_dataset_registration_fields(source_url: str, dataset: dict):
    check_dataset_fields(expected_values_for_dataset_registration_fields(source_url), dataset)


def expected_values_for_dataset_registration_fields(source_url: str) -> list:

    dataset_fields_and_expected_values = [
            ("short_name", "test_foundation_a-dataset-001"),
            ("reporting_org_id", uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")),
            ("reporting_org_short_name", "test_foundation_a"),
            ("source_url", source_url),
            ("licence_id", "other-at"),
            ("registration_service_name", "ckan-registry"),
            ("registration_service_dataset_metadata", json.dumps(
                    {
                        "author": None,
                        "author_email": "publisher@email-here.com",
                        "creator_user_id": "4abc4897-94b7-4b0e-84c2-c8778f435ccb",
                        "id": "c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159",
                        "isopen": True,
                        "license_id": "other-at",
                        "license_title": "Other (Attribution)",
                        "maintainer": None,
                        "maintainer_email": None,
                        "metadata_created": "2024-03-04T10:24:11.373108",
                        "metadata_modified": "2024-05-07T15:38:58.740018",
                        "name": "test_foundation_a-dataset-001",
                        "notes": "",
                        "num_resources": 1,
                        "num_tags": 0,
                        "organization": {
                            "id": "ea055d99-f7e9-456f-9f99-963e95493c1b",
                            "name": "test_foundation_a",
                            "title": "Test Foundation A",
                            "type": "organization",
                            "description": "",
                            "image_url": "",
                            "created": "2020-02-24T20:56:01.763851",
                            "is_organization": True,
                            "approval_status": "approved",
                            "state": "active"
                        },
                        "owner_org": "5d04f169-c702-45fe-8162-da7834859d86",
                        "private": False,
                        "state": "active",
                        "title": "040324",
                        "type": "dataset",
                        "url": None,
                        "version": None,
                        "extras": [
                            {
                                "key": "activity_count",
                                "value": "10"
                            },
                            {
                                "key": "country",
                                "value": "GB"
                            },
                            {
                                "key": "data_updated",
                                "value": "2024-03-01 14:24:09"
                            },
                            {
                                "key": "filetype",
                                "value": "activity"
                            },
                            {
                                "key": "iati_version",
                                "value": "2.03"
                            },
                            {
                                "key": "language",
                                "value": ""
                            },
                            {
                                "key": "secondary_publisher",
                                "value": ""
                            },
                            {
                                "key": "validation_status",
                                "value": "Not Found"
                            }
                        ],
                        "resources": [
                            {
                                "cache_last_updated": None,
                                "cache_url": None,
                                "created": "2024-05-07T15:38:57.312249",
                                "description": None,
                                "format": "IATI-XML",
                                "hash": "f6bb14d61bb2652f1014d6ebfee3c4b873241bac",
                                "id": "d1b3d323-c8ba-48c5-89ce-6e745241d7fe",
                                "last_modified": None,
                                "metadata_modified": "2024-05-07T15:38:58.757860",
                                "mimetype": "",
                                "mimetype_inner": None,
                                "name": None,
                                "package_id": "b83ebe89-d522-4d3b-87e9-53aa9ac8eee9",
                                "position": 0,
                                "resource_type": None,
                                "size": 399382,
                                "state": "active",
                                "url": source_url,
                                "url_type": None
                            }
                        ],
                        "tags": [],
                        "groups": [],
                        "relationships_as_subject": [],
                        "relationships_as_object": []
                    }
            ))
        ]

    return dataset_fields_and_expected_values
