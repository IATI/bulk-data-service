import json
import urllib.parse
import uuid

import pytest

from bulk_data_service.checker import checker_run
from helpers.data_helpers import (
    check_dataset_fields,
    check_dataset_registration_fields,
    check_last_known_good_dataset_values_are_set,
    check_last_known_good_dataset_values_are_unset,
    check_most_recent_get_attempt_downloaded_but_non_iati,
    check_most_recent_get_attempt_http_error,
    check_most_recent_http_attempt_for_success,
    check_registration_service_refreshed_datetime,
)
from helpers.helpers import get_and_clear_up_context  # noqa: F401


@pytest.mark.parametrize(
    "source_url,expected_http_status",
    [
        ("http://localhost:3000/data/test_foundation_a-dataset-001---403.xml", 403),
        ("http://localhost:3000/data/test_foundation_a-dataset-001---404.xml", 404),
        ("http://localhost:3000/data/test_foundation_a-dataset-001---500.xml", 500),
    ],
)
def test_add_new_undownloadable_dataset(get_and_clear_up_context, source_url, expected_http_status):  # noqa: F811

    context = get_and_clear_up_context

    dataset_id = uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-01-1-dataset/{}".format(
        urllib.parse.quote_plus(source_url)
    )

    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    check_dataset_registration_fields(source_url, datasets_in_bds[dataset_id])

    check_registration_service_refreshed_datetime(datasets_in_bds[dataset_id])

    check_last_known_good_dataset_values_are_unset(datasets_in_bds[dataset_id])

    check_most_recent_get_attempt_http_error(datasets_in_bds[dataset_id])

    error_details = json.loads(datasets_in_bds[dataset_id]["most_recent_get_attempt_error_details"])

    assert error_details["http_status"] == expected_http_status


@pytest.mark.parametrize(
    "dataset_url,last_known_good_dataset_hash,last_known_good_dataset_hash_excluding_generated_timestamp,last_known_good_dataset_content_length",
    [
        (
            "http://localhost:3000/data/test_foundation_a-dataset-001.xml",
            "d8776c9e0cf913057c688e140e78cbb10799c158",
            "5bc6f66bef15d6a61c549379c12d8e0d06a2e31c",
            650,
        ),
        (
            "http://localhost:3000/data/test_foundation_a-dataset-001-utf-16-be",
            "0eab5bd008e2f5151c2578b84fda46c054a90c25",
            "d4efc8c57b52463f4b7c181fdd0e778cbe994e84",
            1452,
        ),
        (
            "http://localhost:3000/data/test_foundation_a-dataset-001-utf-16-le",
            "8209b4c54a3c67a143626a176ccddfb9991d2708",
            "d4efc8c57b52463f4b7c181fdd0e778cbe994e84",
            1452,
        ),
    ],
)
def test_add_downloadable_dataset_for_various_encodings(
    get_and_clear_up_context,  # noqa: F811
    dataset_url,
    last_known_good_dataset_hash,
    last_known_good_dataset_hash_excluding_generated_timestamp,
    last_known_good_dataset_content_length,
):

    context = get_and_clear_up_context

    dataset_id = uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")
    context["DATA_REGISTRY_BASE_URL"] = (
        f"http://localhost:3000/ckan-registration/datasets-01-1-dataset/{urllib.parse.quote_plus(dataset_url)}"
    )

    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    check_dataset_registration_fields(dataset_url, datasets_in_bds[dataset_id])

    check_registration_service_refreshed_datetime(datasets_in_bds[dataset_id])

    check_most_recent_http_attempt_for_success("get", datasets_in_bds[dataset_id])

    check_last_known_good_dataset_values_are_set(datasets_in_bds[dataset_id])

    check_dataset_fields(
        [
            ("last_known_good_dataset_hash", last_known_good_dataset_hash),
            (
                "last_known_good_dataset_hash_excluding_generated_timestamp",
                last_known_good_dataset_hash_excluding_generated_timestamp,
            ),
            ("last_known_good_dataset_content_length", last_known_good_dataset_content_length),
            ("last_known_good_dataset_source_url", dataset_url),
        ],
        datasets_in_bds[dataset_id],
    )


@pytest.mark.parametrize(
    "source_url",
    [
        ("http://localhost:3000/data/test_foundation_a-dataset-empty.xml"),
        ("http://localhost:3000/data/test_foundation_a-dataset.pdf"),
    ],
)
def test_add_downloadable_file_that_is_not_iati_dataset(get_and_clear_up_context, source_url):  # noqa: F811

    context = get_and_clear_up_context

    dataset_id = uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/ckan-registration/datasets-01-1-dataset/{}".format(
        urllib.parse.quote_plus(source_url)
    )

    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    check_dataset_registration_fields(source_url, datasets_in_bds[dataset_id])

    check_registration_service_refreshed_datetime(datasets_in_bds[dataset_id])

    check_last_known_good_dataset_values_are_unset(datasets_in_bds[dataset_id])

    check_most_recent_get_attempt_downloaded_but_non_iati(datasets_in_bds[dataset_id])
