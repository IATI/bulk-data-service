import json
import uuid


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
            ("license_id", "other-at"),
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
