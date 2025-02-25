import glob
import json
import os
import shutil
from typing import Any
from unittest import mock

import pytest
from azure.storage.blob import BlobServiceClient
from dotenv import dotenv_values

from config.config import get_app_version
from utilities.azure import create_azure_blob_containers, delete_azure_blob_containers, get_azure_container_name
from utilities.db import apply_db_migrations, get_db_connection
from utilities.prometheus import get_metrics_definitions


def get_number_xml_files_in_working_dir(context):
    return len(glob.glob("**/*.xml",
                         root_dir=context["ZIP_WORKING_DIR"],
                         recursive=True))


def truncate_db_table(context: dict):
    connection = get_db_connection(context)
    cursor = connection.cursor()
    cursor.execute("""TRUNCATE table iati_datasets""")
    cursor.close()
    connection.commit()


def download_index_from_azure(context: dict, index_name: str) -> Any:
    blob_service_client = BlobServiceClient.from_connection_string(context["AZURE_STORAGE_CONNECTION_STRING"])
    zip_container_name = get_azure_container_name(context, "zip")
    index_blob = blob_service_client.get_blob_client(zip_container_name, index_name)
    blob_as_str = index_blob.download_blob().readall()
    blob_service_client.close()
    return json.loads(blob_as_str)


@pytest.fixture
def get_and_clear_up_context():
    logger = mock.Mock()
    context = dotenv_values("tests-local-environment/.env") | {
            "logger" : logger,
            "single_run": True,
            "run_for_n_datasets": None,
            "prom_metrics": {}
        }

    context["BULK_DATA_SERVICE_VERSION"] = get_app_version()

    for metric in get_metrics_definitions():
        context["prom_metrics"][metric[0]] = mock.Mock()

    create_azure_blob_containers(context)
    apply_db_migrations(context)
    yield context
    truncate_db_table(context)
    delete_azure_blob_containers(context)
    # this is a sanity check to ensure we don't remove important files on a misconfiguration
    if context["ZIP_WORKING_DIR"].startswith("/tmp"):
        zip_dirs = [context["ZIP_WORKING_DIR"], f"{context['ZIP_WORKING_DIR']}-1", f"{context['ZIP_WORKING_DIR']}-2"]
        for zip_dir in zip_dirs:
            if os.path.exists(zip_dir):
                shutil.rmtree(zip_dir)
