import uuid

import pytest

from bulk_data_service.checker import checker_run
from helpers.helpers import get_and_clear_up_context  # noqa: F401


@pytest.mark.parametrize("field,expected", [
    ("name", "test_foundation_a-dataset-001"),
    ("publisher_id", uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")),
    ("publisher_name", "test_foundation_a"),
    ("source_url", "http://localhost:3000/data/test_foundation_a-dataset-404.xml"),
    ("type", "activity")
])
def test_add_new_undownloadable_dataset(get_and_clear_up_context, field, expected):  # noqa: F811

    context = get_and_clear_up_context

    dataset_id = uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")

    # dataset c8a40aa5-9f31-... with 404
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-03"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    assert datasets_in_bds[dataset_id][field] == expected
    assert datasets_in_bds[dataset_id]["download_error_message"] is not None
    assert datasets_in_bds[dataset_id]["last_successful_download"] is None
    assert datasets_in_bds[dataset_id]["last_download_http_status"] != 200


@pytest.mark.parametrize("field,expected", [
    ("name", "test_foundation_a-dataset-001"),
    ("publisher_id", uuid.UUID("ea055d99-f7e9-456f-9f99-963e95493c1b")),
    ("publisher_name", "test_foundation_a"),
    ("source_url", "http://localhost:3000/data/test_foundation_a-dataset-001.xml"),
    ("type", "activity"),
    ("hash", "7703103493edafde0dbce66e507abb642fc7bd52"),
    ("hash_excluding_generated_timestamp", "ef0eead52dfc3bd86311c84327282f607402dfff")
])
def test_add_new_downloadable_dataset(get_and_clear_up_context, field, expected):  # noqa: F811

    context = get_and_clear_up_context

    dataset_id = uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")

    # dataset c8a40aa5-9f31-... with 404
    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01"
    datasets_in_bds = {}
    checker_run(context, datasets_in_bds)

    assert datasets_in_bds[dataset_id][field] == expected
    assert datasets_in_bds[dataset_id]["download_error_message"] is None
    assert datasets_in_bds[dataset_id]["last_successful_download"] is not None
    assert datasets_in_bds[dataset_id]["last_download_http_status"] == 200
