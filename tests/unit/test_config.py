from unittest import mock

from dotenv import load_dotenv

from config.bds_context import BDSContext
from config.config import (
    _config_variables,
    _loggable_runtime_settings,
    get_basic_config,
    get_config_for_logging,
)


def test_config_blob_storage_base_url_has_no_trailing_slash_1():

    load_dotenv("tests/artifacts/config-files/env-file-1", override=True)

    config = get_basic_config()

    assert config["WEB_BASE_URL"] == "http://127.0.0.1:10000/devstoreaccount1"


def test_config_blob_storage_base_url_has_no_trailing_slash_2():

    load_dotenv("tests/artifacts/config-files/env-file-2", override=True)

    config = get_basic_config()

    assert config["WEB_BASE_URL"] == "http://127.0.0.1:10000/devstoreaccount1"


def test_config_dataset_timeouts_loaded():
    load_dotenv("tests/artifacts/config-files/env-file-2", override=True)

    config = get_basic_config()

    context = BDSContext(config, mock.Mock(), mock.Mock())

    assert context.DATASET_GET_TIMEOUT == 22

    assert context.DATASET_HEAD_TIMEOUT == 7


def get_config_lines_for_env_file_2() -> list[str]:
    load_dotenv("tests/artifacts/config-files/env-file-2", override=True)

    config = get_basic_config() | {
        "single_run": True,
        "run_for_n_datasets": 3,
        "run_for_single_reporting_org": None,
        "skip_safety": False,
    }

    return get_config_for_logging(config)


def test_config_for_logging_contains_exactly_the_loggable_variables():

    names_logged = [line.split("=", 1)[0] for line in get_config_lines_for_env_file_2()]

    expected_names = [name for name, loggable in _config_variables.items() if loggable] + _loggable_runtime_settings

    assert names_logged == expected_names


def test_config_for_logging_omits_secret_variables():

    config_output = "\n".join(get_config_lines_for_env_file_2())

    secret_names = [name for name, loggable in _config_variables.items() if not loggable]

    for secret_name in secret_names:
        assert secret_name not in config_output


def test_config_for_logging_does_not_contain_secret_values():

    config_output = "\n".join(get_config_lines_for_env_file_2())

    # fragments of the secret values which are set in the env file used above
    for secret_value_fragment in ["AccountKey", "SharedAccessKey", "Eby8vdM02xNOcqFlqUwJPLl"]:
        assert secret_value_fragment not in config_output


def test_get_basic_config_reads_every_config_variable():
    load_dotenv("tests/artifacts/config-files/env-file-2", override=True)

    config = get_basic_config()

    for name in _config_variables:
        assert name in config
