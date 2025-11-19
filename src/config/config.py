import os
from pathlib import Path

import toml

_config_variables = [
    "DATA_REGISTRATION",
    "DATA_REGISTRY_BASE_URL",
    "DATA_REGISTRY_PUBLISHER_PLAIN_LIST_URL",
    "DATA_REGISTRY_PUBLISHER_METADATA_URL",
    "DATA_REGISTRY_PUBLISHER_METADATA_BATCH_SIZE",
    "DATA_REGISTRY_SUITECRM_API_URL",
    "DATA_REGISTRY_SUITECRM_CLIENT_ID",
    "DATA_REGISTRY_SUITECRM_CLIENT_SECRET",
    "DATA_REGISTRY_SUITECRM_SECURE",
    "WEB_BASE_URL",
    "NUMBER_DOWNLOADER_THREADS",
    "FORCE_REDOWNLOAD_AFTER_HOURS",
    "REDOWNLOAD_FROM_NON_HEAD_SERVERS_AFTER_HOURS",
    "REMOVE_LAST_GOOD_DOWNLOAD_AFTER_FAILING_HOURS",
    "ZIP_WORKING_DIR",
    "DB_NAME",
    "DB_USER",
    "DB_PASS",
    "DB_HOST",
    "DB_PORT",
    "DB_SSL_MODE",
    "DB_CONNECTION_TIMEOUT",
    "AZURE_STORAGE_CONNECTION_STRING",
    "AZURE_STORAGE_BLOB_CONTAINER_NAME",
    "CHECKER_LOOP_WAIT_MINS",
    "AZURE_SERVICE_BUS_CONNECTION_STRING",
    "AZURE_SERVICE_BUS_REGISTRY_TOPIC_NAME",
    "AZURE_SERVICE_BUS_REGISTRY_SUB_NAME",
    "AZURE_SERVICE_BUS_WAIT_TIME",
    "AZURE_SERVICE_BUS_DATASET_CHECK_RESULTS_TOPIC_NAME",
    "SEND_DATASET_CHECK_RESULT_MESSAGES",
    "DATASET_HEAD_TIMEOUT",
    "DATASET_GET_TIMEOUT",
]


def get_basic_config() -> dict:
    config = {env_var: os.getenv(env_var, "") for env_var in _config_variables}

    config["WEB_BASE_URL"] = config["WEB_BASE_URL"].strip("/")

    config["BULK_DATA_SERVICE_VERSION"] = get_app_version()

    return config


def get_app_version() -> str:
    app_version = "Unknown Version"
    pyproject_file = Path(__file__).parent.parent.parent / "pyproject.toml"
    if pyproject_file.exists():
        pyproject_data = toml.load(pyproject_file)
        if "project" in pyproject_data and "version" in pyproject_data["project"]:
            app_version = pyproject_data["project"]["version"]
    return app_version
