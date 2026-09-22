import os
from enum import Enum, auto
from pathlib import Path

import toml


class LogPolicy(Enum):
    """Whether a configuration variable's value may be written to the logs when
    the app starts. Anything marked SECRET is not logged at all, not even to
    indicate whether it is set."""

    LOGGABLE = auto()
    SECRET = auto()


_config_variables: dict[str, LogPolicy] = {
    "DATA_REGISTRATION": LogPolicy.LOGGABLE,
    "DATA_REGISTRY_BASE_URL": LogPolicy.LOGGABLE,
    "DATA_REGISTRY_PUBLISHER_PLAIN_LIST_URL": LogPolicy.LOGGABLE,
    "DATA_REGISTRY_PUBLISHER_METADATA_URL": LogPolicy.LOGGABLE,
    "DATA_REGISTRY_PUBLISHER_METADATA_BATCH_SIZE": LogPolicy.LOGGABLE,
    "DATA_REGISTRY_SUITECRM_API_URL": LogPolicy.LOGGABLE,
    "DATA_REGISTRY_SUITECRM_CLIENT_ID": LogPolicy.SECRET,
    "DATA_REGISTRY_SUITECRM_CLIENT_SECRET": LogPolicy.SECRET,
    "DATA_REGISTRY_SUITECRM_SECURE": LogPolicy.LOGGABLE,
    "WEB_BASE_URL": LogPolicy.LOGGABLE,
    "NUMBER_DOWNLOADER_THREADS": LogPolicy.LOGGABLE,
    "FORCE_REDOWNLOAD_AFTER_HOURS": LogPolicy.LOGGABLE,
    "REDOWNLOAD_FROM_NON_HEAD_SERVERS_AFTER_HOURS": LogPolicy.LOGGABLE,
    "REMOVE_LAST_GOOD_DOWNLOAD_AFTER_FAILING_HOURS": LogPolicy.LOGGABLE,
    "ZIP_WORKING_DIR": LogPolicy.LOGGABLE,
    "DB_NAME": LogPolicy.SECRET,
    "DB_USER": LogPolicy.SECRET,
    "DB_PASS": LogPolicy.SECRET,
    "DB_HOST": LogPolicy.SECRET,
    "DB_PORT": LogPolicy.SECRET,
    "DB_SSL_MODE": LogPolicy.SECRET,
    "DB_CONNECTION_TIMEOUT": LogPolicy.LOGGABLE,
    "AZURE_STORAGE_CONNECTION_STRING": LogPolicy.SECRET,
    "AZURE_STORAGE_BLOB_CONTAINER_NAME": LogPolicy.LOGGABLE,
    "CHECKER_LOOP_WAIT_MINS": LogPolicy.LOGGABLE,
    "AZURE_SERVICE_BUS_CONNECTION_STRING": LogPolicy.SECRET,
    "AZURE_SERVICE_BUS_REGISTRY_TOPIC_NAME": LogPolicy.LOGGABLE,
    "AZURE_SERVICE_BUS_REGISTRY_SUB_NAME": LogPolicy.LOGGABLE,
    "AZURE_SERVICE_BUS_WAIT_TIME": LogPolicy.LOGGABLE,
    "AZURE_SERVICE_BUS_DATASET_CHECK_RESULTS_TOPIC_NAME": LogPolicy.LOGGABLE,
    "SEND_DATASET_CHECK_RESULT_MESSAGES": LogPolicy.LOGGABLE,
    "DATASET_HEAD_TIMEOUT": LogPolicy.LOGGABLE,
    "DATASET_GET_TIMEOUT": LogPolicy.LOGGABLE,
    "SENTRY_DSN": LogPolicy.SECRET,
    "SENTRY_ENVIRONMENT": LogPolicy.LOGGABLE,
    "SENTRY_TRACES_SAMPLE_RATE": LogPolicy.LOGGABLE,
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
    only the variables which are marked as LogPolicy.LOGGABLE, plus the settings which
    come from the command line."""

    loggable_variables = [name for name, policy in _config_variables.items() if policy is LogPolicy.LOGGABLE]

    return [f"{name}={config.get(name)}" for name in loggable_variables + _loggable_runtime_settings]


def get_secret_variable_names() -> list[str]:
    """Returns the names of the configuration variables which hold credentials,
    for use by anything which sends data off the machine and so must not pass on
    their values."""

    return [name for name, policy in _config_variables.items() if policy is LogPolicy.SECRET]


def get_app_version() -> str:
    app_version = "Unknown Version"
    pyproject_file = Path(__file__).parent.parent.parent / "pyproject.toml"
    if pyproject_file.exists():
        pyproject_data = toml.load(pyproject_file)
        if "project" in pyproject_data and "version" in pyproject_data["project"]:
            app_version = pyproject_data["project"]["version"]
    return app_version
