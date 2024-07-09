import json
import uuid
from functools import partial
from unittest import mock

import pytest

from dataset_registration.iati_registry_ckan import clean_datasets_metadata, convert_datasets_metadata


def get_level1_field_blanker(key):
    def field_blanker(dict, attribute_value, key=key):
        dict[key] = attribute_value
    return partial(field_blanker, key=key)


def get_level2_field_blanker(key1, key2):
    def field_blanker(dict, attribute_value, key1=key1, key2=key2):
        dict[key1][key2] = attribute_value
    return partial(field_blanker, key1=key1, key2=key2)


@pytest.mark.parametrize("field_blanker", [
    get_level1_field_blanker("id"),
    get_level1_field_blanker("name"),
    get_level1_field_blanker("organization"),
    get_level1_field_blanker("extras"),
    get_level2_field_blanker("organization", "id"),
    get_level2_field_blanker("organization", "name")
    ])
@pytest.mark.parametrize("attribute_value", [None, "None", ""])
def test_incomplete_necessary_data_from_ckan(field_blanker, attribute_value):

    with open("tests/artifacts/ckan-registry-datasets-01-1-dataset.json", "r") as f:
        registry_result_str = f.read()
    ckan_datasets = json.loads(registry_result_str)["result"]["results"]
    field_blanker(ckan_datasets[0], attribute_value)
    logger = mock.Mock()

    ckan_datasets = clean_datasets_metadata(logger, ckan_datasets)

    assert(len(ckan_datasets) == 0)


@pytest.mark.parametrize("resources_value", [None, [], {"url": None}])
def test_missing_url_from_ckan(resources_value):

    with open("tests/artifacts/ckan-registry-datasets-01-1-dataset.json", "r") as f:
        registry_result_str = f.read()
    ckan_datasets = json.loads(registry_result_str)["result"]["results"]
    ckan_datasets[0]["resources"] = resources_value
    logger = mock.Mock()

    ckan_datasets = clean_datasets_metadata(logger, ckan_datasets)
    bds_datasets = convert_datasets_metadata(ckan_datasets)

    assert(len(bds_datasets) == 1)
    assert(bds_datasets[uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")]["source_url"] == "")
