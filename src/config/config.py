import os
from pathlib import Path

import toml

# Flags for whether a configuration variable's value may be written to the logs
# when the app starts. Anything marked SECRET is not logged at all, not even to
# indicate whether it is set.
LOGGABLE = True
SECRET = False

_config_variables = {
    "DATA_REGISTRATION": LOGGABLE,
    "DATA_REGISTRY_BASE_URL": LOGGABLE,
    "DATA_REGISTRY_PUBLISHER_PLAIN_LIST_URL": LOGGABLE,
    "DATA_REGISTRY_PUBLISHER_METADATA_URL": LOGGABLE,
    "DATA_REGISTRY_PUBLISHER_METADATA_BATCH_SIZE": LOGGABLE,
    "DATA_REGISTRY_SUITECRM_API_URL": LOGGABLE,
    "DATA_REGISTRY_SUITECRM_CLIENT_ID": SECRET,
    "DATA_REGISTRY_SUITECRM_CLIENT_SECRET": SECRET,
    "DATA_REGISTRY_SUITECRM_SECURE": LOGGABLE,
    "WEB_BASE_URL": LOGGABLE,
    "NUMBER_DOWNLOADER_THREADS": LOGGABLE,
    "FORCE_REDOWNLOAD_AFTER_HOURS": LOGGABLE,
    "REDOWNLOAD_FROM_NON_HEAD_SERVERS_AFTER_HOURS": LOGGABLE,
    "REMOVE_LAST_GOOD_DOWNLOAD_AFTER_FAILING_HOURS": LOGGABLE,
    "ZIP_WORKING_DIR": LOGGABLE,
    "DB_NAME": SECRET,
    "DB_USER": SECRET,
    "DB_PASS": SECRET,
    "DB_HOST": SECRET,
    "DB_PORT": SECRET,
    "DB_SSL_MODE": SECRET,
    "DB_CONNECTION_TIMEOUT": LOGGABLE,
    "AZURE_STORAGE_CONNECTION_STRING": SECRET,
    "AZURE_STORAGE_BLOB_CONTAINER_NAME": LOGGABLE,
    "CHECKER_LOOP_WAIT_MINS": LOGGABLE,
    "AZURE_SERVICE_BUS_CONNECTION_STRING": SECRET,
    "AZURE_SERVICE_BUS_REGISTRY_TOPIC_NAME": LOGGABLE,
    "AZURE_SERVICE_BUS_REGISTRY_SUB_NAME": LOGGABLE,
    "AZURE_SERVICE_BUS_WAIT_TIME": LOGGABLE,
    "AZURE_SERVICE_BUS_DATASET_CHECK_RESULTS_TOPIC_NAME": LOGGABLE,
    "SEND_DATASET_CHECK_RESULT_MESSAGES": LOGGABLE,
    "DATASET_HEAD_TIMEOUT": LOGGABLE,
    "DATASET_GET_TIMEOUT": LOGGABLE,
}

# Settings which come from the command line rather than from the environment.
# These cannot be added to `_config_variables` because `get_basic_config` would
# then read them from the environment and overwrite the values from the command
# line with empty strings.
_loggable_runtime_settings = [
    "single_run",
    "run_for_n_datasets",
    "run_for_single_reporting_org",
    "skip_safety",
]


def get_basic_config() -> dict:
    config = {env_var: os.getenv(env_var, "") for env_var in _config_variables}

    config["WEB_BASE_URL"] = config["WEB_BASE_URL"].strip("/")

    config["BULK_DATA_SERVICE_VERSION"] = get_app_version()

    return config


def get_config_for_logging(config: dict) -> list[str]:
    """Returns the configuration as a list of 'NAME=value' strings, containing
    only the variables which are marked as LOGGABLE, plus the settings which
    come from the command line."""

    loggable_variables = [name for name, loggable in _config_variables.items() if loggable]

    return ["{}={}".format(name, config.get(name)) for name in loggable_variables + _loggable_runtime_settings]


def get_app_version() -> str:
    app_version = "Unknown Version"
    pyproject_file = Path(__file__).parent.parent.parent / "pyproject.toml"
    if pyproject_file.exists():
        pyproject_data = toml.load(pyproject_file)
        if "project" in pyproject_data and "version" in pyproject_data["project"]:
            app_version = pyproject_data["project"]["version"]
    return app_version
