import os

_config_variables = [
    "DATA_REGISTRATION",
    "DATA_REGISTRY_BASE_URL",
    "BLOB_STORAGE_BASE_PUBLIC_URL",
    "NUMBER_DOWNLOADER_THREADS",
    "FORCE_REDOWNLOAD_AFTER_HOURS",
    "REMOVE_LAST_GOOD_DOWNLOAD_AFTER_FAILING_HOURS",
    "LOGFILE",
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
]


def get_config() -> dict[str, str]:
    config = {env_var: os.getenv(env_var, "") for env_var in _config_variables}

    config["BLOB_STORAGE_BASE_PUBLIC_URL"] = config["BLOB_STORAGE_BASE_PUBLIC_URL"].strip("/")

    return config
