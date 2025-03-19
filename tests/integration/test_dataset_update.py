import json
import uuid

import pytest

from bulk_data_service.checker import checker_run
from helpers.helpers import check_values_for_download_success, get_and_clear_up_context  # noqa: F401


@pytest.mark.parametrize("field,original,expected", [
    ("source_url", "http://localhost:3000/data/test_foundation_a-dataset-001.xml",
        "http://localhost:3000/not_found"),
    ("license_id", "other-at", "uk-ogl"),
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
                        "url": "http://localhost:3000/data/test_foundation_a-dataset-001.xml",
                        "url_type": None
                    }
                ],
                "tags": [],
                "groups": [],
                "relationships_as_subject": [],
                "relationships_as_object": []
            }
        ),
        json.dumps(
            {
                "author": None,
                "author_email": "publisher@email-here.com",
                "creator_user_id": "4abc4897-94b7-4b0e-84c2-c8778f435ccb",
                "id": "c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159",
                "isopen": True,
                "license_id": "uk-ogl",
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
                        "value": "organisation"
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
                        "url": "http://localhost:3000/not_found",
                        "url_type": None
                    }
                ],
                "tags": [],
                "groups": [],
                "relationships_as_subject": [],
                "relationships_as_object": []
            }
        )
     )
])
def test_update_dataset_publisher_details(get_and_clear_up_context,  # noqa: F811
                                          field,
                                          original,
                                          expected):

    context = get_and_clear_up_context

    dataset_id = uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-01-1-dataset"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    assert len(datasets_in_bds) == 1
    assert datasets_in_bds[dataset_id][field] == original

    # this is same dataset as above, with a different url and license
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-05-1-dataset-updated"
    checker_run(context, datasets_in_bds)

    assert len(datasets_in_bds) == 1
    assert datasets_in_bds[dataset_id][field] == expected


def test_dataset_download_404s_then_successful(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    dataset_id = uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")

    # dataset c8a40aa5-9f31-... with 404
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-03-1-dataset-404"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    assert datasets_in_bds[dataset_id]["most_recent_get_attempt_http_status"] == 404
    assert datasets_in_bds[dataset_id]["most_recent_get_attempt_error_details"] is not None
    assert datasets_in_bds[dataset_id]["last_known_good_dataset_content_length"] is None
    assert datasets_in_bds[dataset_id]["last_known_good_dataset_initial_contents"] is None

    # dataset c8a40aa5-9f31-... with good URL
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-01-1-dataset"
    checker_run(context, datasets_in_bds)

    check_values_for_download_success(datasets_in_bds[dataset_id])


def test_dataset_successful_xml_download_then_pdf(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    dataset_id = uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")

    # dataset c8a40aa5-9f31-... with XML
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-01-1-dataset"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    check_values_for_download_success(datasets_in_bds[dataset_id])
    # extra check, for the actual value of start of XML
    assert (datasets_in_bds[dataset_id]["last_known_good_dataset_initial_contents"] ==
            ('<?xml version="1.0" encoding="UTF-8"?><iati-activities version="2.03" '
            'generated-datetime="2024-05-03T08:47:49+00:00">  <iati-activity>    <iati-identi'))

    # dataset c8a40aa5-9f31-... with source url pointing to PDF
    context["DATA_REGISTRY_BASE_URL"] = ("http://localhost:3000/ckan-registration/datasets-01-1-dataset/"
                                         "http%3A%2F%2Flocalhost%3A3000%2Fdata%2Ftest_foundation_a-dataset.pdf")
    checker_run(context, datasets_in_bds)

    assert datasets_in_bds[dataset_id]["most_recent_get_attempt_http_status"] == 200
    assert datasets_in_bds[dataset_id]["most_recent_get_attempt_error_details"] is not None
    assert datasets_in_bds[dataset_id]["last_known_good_dataset_content_length"] > 0
    assert datasets_in_bds[dataset_id]["last_known_good_dataset_initial_contents"] is None


def test_dataset_pdf_download_then_successful_xml(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    dataset_id = uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")

    # dataset c8a40aa5-9f31-... with source url pointing to PDF
    context["DATA_REGISTRY_BASE_URL"] = ("http://localhost:3000/ckan-registration/datasets-01-1-dataset/"
                                         "http%3A%2F%2Flocalhost%3A3000%2Fdata%2Ftest_foundation_a-dataset.pdf")
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    assert datasets_in_bds[dataset_id]["most_recent_get_attempt_http_status"] == 200
    assert datasets_in_bds[dataset_id]["most_recent_get_attempt_error_details"] is not None
    assert datasets_in_bds[dataset_id]["last_known_good_dataset_content_length"] > 0
    assert datasets_in_bds[dataset_id]["last_known_good_dataset_initial_contents"] is None

    # dataset c8a40aa5-9f31-... with XML
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-01-1-dataset"
    checker_run(context, datasets_in_bds)

    check_values_for_download_success(datasets_in_bds[dataset_id])
    # extra check, for the actual value of start of XML
    assert (datasets_in_bds[dataset_id]["last_known_good_dataset_initial_contents"] ==
            ('<?xml version="1.0" encoding="UTF-8"?><iati-activities version="2.03" '
            'generated-datetime="2024-05-03T08:47:49+00:00">  <iati-activity>    <iati-identi'))


def test_dataset_successful_xml_download_then_empty(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    dataset_id = uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")

    # dataset c8a40aa5-9f31-... with XML
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-01-1-dataset"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    check_values_for_download_success(datasets_in_bds[dataset_id])
    assert (datasets_in_bds[dataset_id]["last_known_good_dataset_initial_contents"] ==
            ('<?xml version="1.0" encoding="UTF-8"?><iati-activities version="2.03" '
            'generated-datetime="2024-05-03T08:47:49+00:00">  <iati-activity>    <iati-identi'))

    # dataset c8a40aa5-9f31-... with source url pointing to empty file
    context["DATA_REGISTRY_BASE_URL"] = ("http://localhost:3000/ckan-registration/datasets-01-1-dataset/"
                                         "http%3A%2F%2Flocalhost%3A3000%2Fdata%2Ftest_foundation_a-dataset-empty.xml")
    checker_run(context, datasets_in_bds)

    assert datasets_in_bds[dataset_id]["most_recent_get_attempt_http_status"] == 200
    assert datasets_in_bds[dataset_id]["most_recent_get_attempt_error_details"] is not None
    assert datasets_in_bds[dataset_id]["last_known_good_dataset_content_length"] == 0
    assert datasets_in_bds[dataset_id]["last_known_good_dataset_initial_contents"] is None
