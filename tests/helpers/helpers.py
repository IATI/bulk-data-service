import glob
from unittest import mock

import pytest
from dotenv import dotenv_values

from utilities.azure import create_azure_blob_containers, delete_azure_blob_containers
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


@pytest.fixture
def get_and_clear_up_context():
    logger = mock.Mock()
    context = dotenv_values("tests-local-environment/.env") | {
            "logger" : logger,
            "single_run": True,
            "run_for_n_datasets": None,
            "prom_metrics": {}
        }

    for metric in get_metrics_definitions(context):
        context["prom_metrics"][metric[0]] = mock.Mock()

    create_azure_blob_containers(context)
    apply_db_migrations(context)
    yield context
    truncate_db_table(context)
    delete_azure_blob_containers(context)
