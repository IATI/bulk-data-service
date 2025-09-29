from unittest import mock

from dotenv import load_dotenv

from config.bds_context import BDSContext
from config.config import get_basic_config


def test_config_blob_storage_base_url_has_no_trailing_slash_1():

    load_dotenv("tests/artifacts/config-files/env-file-1", override=True)

    config = get_basic_config()

    assert config["WEB_BASE_URL"] == 'http://127.0.0.1:10000/devstoreaccount1'


def test_config_blob_storage_base_url_has_no_trailing_slash_2():

    load_dotenv("tests/artifacts/config-files/env-file-2", override=True)

    config = get_basic_config()

    assert config["WEB_BASE_URL"] == 'http://127.0.0.1:10000/devstoreaccount1'


def test_config_dataset_timeouts_loaded():
    load_dotenv("tests/artifacts/config-files/env-file-2", override=True)

    config = get_basic_config()

    context = BDSContext(config, mock.Mock(), mock.Mock())

    assert context.DATASET_GET_TIMEOUT == 22

    assert context.DATASET_HEAD_TIMEOUT == 7
