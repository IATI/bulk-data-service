import uuid

import pytest

from bulk_data_service.checker import checker_run
from helpers.helpers import get_and_clear_up_context  # noqa: F401


@pytest.mark.parametrize("field,original,expected", [
    ("publisher_id", uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b"),
        uuid.UUID("4f0f8498-20d2-4ca5-a20f-f441eedb1d4f")),
    ("publisher_name", "test_foundation_a", "test_org_a"),
    ("source_url", "http://localhost:3000/data/test_foundation_a-dataset-001.xml",
        "http://localhost:3000/not_found"),
    ("type", "activity", "organisation")
])
def test_update_dataset_publisher_details(get_and_clear_up_context,  # noqa: F811
                                          field,
                                          original,
                                          expected):

    context = get_and_clear_up_context

    dataset_id = uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    assert len(datasets_in_bds) == 1
    assert datasets_in_bds[dataset_id][field] == original

    # this is same dataset as above, with a different url
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-05"
    checker_run(context, datasets_in_bds)

    assert len(datasets_in_bds) == 1
    assert datasets_in_bds[dataset_id][field] == expected


def test_get_request_download_error_cleared(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    dataset_id = uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")

    # dataset c8a40aa5-9f31-... with 404
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-03"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    assert datasets_in_bds[dataset_id]["last_download_http_status"] == 404
    assert datasets_in_bds[dataset_id]["download_error_message"] is not None

    # dataset c8a40aa5-9f31-... with good URL
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01"
    checker_run(context, datasets_in_bds)

    assert datasets_in_bds[dataset_id]["last_download_http_status"] == 200
    assert datasets_in_bds[dataset_id]["download_error_message"] is None
