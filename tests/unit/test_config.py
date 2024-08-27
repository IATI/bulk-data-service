from dotenv import load_dotenv

from config.config import get_config


def test_config_blob_storage_base_url_has_no_trailing_slash_1():

    load_dotenv("tests/artifacts/config-files/env-file-1", override=True)

    config = get_config()

    assert config["WEB_BASE_URL"] == 'http://127.0.0.1:10000/devstoreaccount1'


def test_config_blob_storage_base_url_has_no_trailing_slash_2():

    load_dotenv("tests/artifacts/config-files/env-file-2", override=True)

    config = get_config()

    assert config["WEB_BASE_URL"] == 'http://127.0.0.1:10000/devstoreaccount1'
