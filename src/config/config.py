import os

_config_variables = [
    "DATA_REGISTRATION",
    "DATA_REGISTRY_BASE_URL",
    "DATA_REGISTRY_PUBLISHER_METADATA_URL",
    "DATA_REGISTRY_PUBLISHER_METADATA_REFRESH_AFTER_HOURS",
    "WEB_BASE_URL",
    "NUMBER_DOWNLOADER_THREADS",
    "FORCE_REDOWNLOAD_AFTER_HOURS",
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
    "AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_XML",
    "AZURE_STORAGE_BLOB_CONTAINER_NAME_IATI_ZIP",
    "CHECKER_LOOP_WAIT_MINS"
]


def get_config() -> dict[str, str]:
    config = {env_var: os.getenv(env_var, "") for env_var in _config_variables}

    config["WEB_BASE_URL"] = config["WEB_BASE_URL"].strip("/")

    return config
