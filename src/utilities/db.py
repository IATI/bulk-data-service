import uuid
from typing import Any

import psycopg
from psycopg.rows import dict_row
from yoyo import get_backend, read_migrations  # type: ignore

from config.bds_context import BDSContext


def apply_db_migrations(context: BDSContext):

    backend = get_backend(
        "postgresql+psycopg://{}:{}@{}:{}/{}".format(
            context["DB_USER"], context["DB_PASS"], context["DB_HOST"], context["DB_PORT"], context["DB_NAME"]
        )
    )

    migrations = read_migrations("db-migrations")

    with backend.lock():

        # Apply any outstanding migrations
        backend.apply_migrations(backend.to_apply(migrations))


def get_db_connection(context: BDSContext) -> psycopg.Connection:
    connection = psycopg.connect(
        dbname=context["DB_NAME"],
        user=context["DB_USER"],
        password=context["DB_PASS"],
        host=context["DB_HOST"],
        port=context["DB_PORT"],
        sslmode="prefer" if context["DB_SSL_MODE"] is None else context["DB_SSL_MODE"],
        connect_timeout=context["DB_CONNECTION_TIMEOUT"],
    )
    return connection


def get_datasets_in_bds(context: BDSContext) -> dict[uuid.UUID, dict]:

    connection = get_db_connection(context)
    cursor = connection.cursor(row_factory=dict_row)
    cursor.execute("""SELECT * FROM iati_datasets""")
    results_as_list = cursor.fetchall()
    cursor.close()

    results = {result["id"]: result for result in results_as_list}

    return results


def get_dataset_in_bds(context: BDSContext, dataset_id: uuid.UUID) -> dict | None:

    connection = get_db_connection(context)
    cursor = connection.cursor(row_factory=dict_row)
    cursor.execute("""SELECT * FROM iati_datasets WHERE id = %(id)s""", {"id": dataset_id})
    result = cursor.fetchone()
    cursor.close()

    return result


def get_reporting_org_in_bds(context: BDSContext, reporting_org_id: uuid.UUID) -> dict | None:

    connection = get_db_connection(context)
    cursor = connection.cursor(row_factory=dict_row)
    cursor.execute("""SELECT * FROM iati_reporting_orgs WHERE id = %(id)s""", {"id": reporting_org_id})
    result = cursor.fetchone()
    cursor.close()

    return result


def get_reporting_orgs_in_bds(context: BDSContext) -> dict[uuid.UUID, dict]:

    connection = get_db_connection(context)
    cursor = connection.cursor(row_factory=dict_row)
    cursor.execute("""SELECT * FROM iati_reporting_orgs""")
    results_as_list = cursor.fetchall()
    cursor.close()

    results = {result["id"]: result for result in results_as_list}

    return results


def insert_or_update_dataset(connection: psycopg.Connection, data):
    columns = ", ".join([k for k in data])
    placeholders = ", ".join(["%({})s".format(k) for k in data])

    add_sql = """INSERT INTO iati_datasets ({})
                        VALUES ({})
                 ON CONFLICT (id) DO
                    UPDATE SET
                        reporting_org_id = %(reporting_org_id)s,
                        reporting_org_short_name = %(reporting_org_short_name)s,
                        source_url = %(source_url)s,
                        licence_id = %(licence_id)s,
                        registration_service_metadata_refreshed_datetime = %(registration_service_metadata_refreshed_datetime)s,
                        registration_service_dataset_metadata = %(registration_service_dataset_metadata)s,
                        registration_service_name = %(registration_service_name)s,

                        last_update_check = %(last_update_check)s,

                        last_known_good_dataset_hash = %(last_known_good_dataset_hash)s,
                        last_known_good_dataset_hash_excluding_generated_timestamp =
                                                %(last_known_good_dataset_hash_excluding_generated_timestamp)s,
                        last_known_good_dataset_downloaded = %(last_known_good_dataset_downloaded)s,
                        last_known_good_dataset_verified_on_server = %(last_known_good_dataset_verified_on_server)s,
                        last_known_good_dataset_server_header_last_modified =
                                                %(last_known_good_dataset_server_header_last_modified)s,
                        last_known_good_dataset_server_header_etag = %(last_known_good_dataset_server_header_etag)s,
                        last_known_good_dataset_content_length = %(last_known_good_dataset_content_length)s,
                        last_known_good_dataset_initial_contents = %(last_known_good_dataset_initial_contents)s,
                        last_known_good_dataset_source_url = %(last_known_good_dataset_source_url)s,

                        most_recent_head_attempt_datetime = %(most_recent_head_attempt_datetime)s,
                        most_recent_head_attempt_error_details = %(most_recent_head_attempt_error_details)s,
                        most_recent_head_attempt_error_occurred = %(most_recent_head_attempt_error_occurred)s,
                        most_recent_head_attempt_http_status = %(most_recent_head_attempt_http_status)s,

                        most_recent_get_attempt_datetime = %(most_recent_get_attempt_datetime)s,
                        most_recent_get_attempt_error_details = %(most_recent_get_attempt_error_details)s,
                        most_recent_get_attempt_error_occurred = %(most_recent_get_attempt_error_occurred)s,
                        most_recent_get_attempt_http_status = %(most_recent_get_attempt_http_status)s

                    WHERE
                        iati_datasets.id = %(id)s
        """.format(
        columns, placeholders
    )
    cursor = connection.cursor()
    cursor.execute(add_sql, data)  # type: ignore
    cursor.close()
    connection.commit()


def update_dataset_registration_data(connection: psycopg.Connection, data):
    update_sql = """UPDATE iati_datasets SET
                        short_name = %(short_name)s,
                        reporting_org_id = %(reporting_org_id)s,
                        reporting_org_short_name = %(reporting_org_short_name)s,
                        source_url = %(source_url)s,
                        licence_id = %(licence_id)s,
                        registration_service_dataset_metadata = %(registration_service_dataset_metadata)s,
                        registration_service_metadata_refreshed_datetime = %(registration_service_metadata_refreshed_datetime)s,
                        registration_service_name = %(registration_service_name)s
                    WHERE
                        iati_datasets.id = %(id)s
               """
    cursor = connection.cursor()
    cursor.execute(update_sql, data)  # type: ignore
    cursor.close()
    connection.commit()


def insert_or_update_reporting_org(connection: psycopg.Connection, data):
    columns = ", ".join([k for k in data])
    placeholders = ", ".join(["%({})s".format(k) for k in data])

    add_sql = """INSERT INTO iati_reporting_orgs ({})
                        VALUES ({})
                 ON CONFLICT (id) DO
                    UPDATE SET
                        created_date = %(created_date)s,
                        data_portal_url = %(data_portal_url)s,
                        default_licence_id = %(default_licence_id)s,
                        description = %(description)s,
                        exclusions_policy_url = %(exclusions_policy_url)s,
                        first_publication_date = %(first_publication_date)s,
                        hq_country = %(hq_country)s,
                        human_readable_name = %(human_readable_name)s,
                        organisation_identifier = %(organisation_identifier)s,
                        organisation_type = %(organisation_type)s,
                        region = %(region)s,
                        reporting_source_type = %(reporting_source_type)s,
                        registration_service_metadata_refreshed_datetime = %(registration_service_metadata_refreshed_datetime)s,
                        registration_service_reporting_org_metadata = %(registration_service_reporting_org_metadata)s,
                        short_name = %(short_name)s,
                        website = %(website)s
                    WHERE
                        iati_reporting_orgs.id = %(id)s
        """.format(
        columns, placeholders
    )
    cursor = connection.cursor()
    cursor.execute(add_sql, data)  # type: ignore
    cursor.close()
    connection.commit()


def remove_reporting_org_from_db(connection: psycopg.Connection, reporting_org_id: uuid.UUID):
    add_sql = """DELETE FROM iati_reporting_orgs WHERE id = %(reporting_org_id)s"""
    cursor = connection.cursor()
    cursor.execute(add_sql, {"reporting_org_id": reporting_org_id})
    cursor.close()
    connection.commit()


def remove_dataset_from_db(connection: psycopg.Connection, dataset_id):
    add_sql = """DELETE FROM iati_datasets WHERE id = %(dataset_id)s"""
    cursor = connection.cursor()
    cursor.execute(add_sql, {"dataset_id": dataset_id})
    cursor.close()
    connection.commit()


def execute_scalar_db_query(context: BDSContext, sql: str) -> Any:
    connection = get_db_connection(context)
    value = execute_scalar_db_query_with_conn(connection, sql)
    connection.close()
    return value


def execute_scalar_db_query_with_conn(connection: psycopg.Connection, sql: str) -> Any:
    cursor = connection.cursor()
    row = cursor.execute(sql).fetchone()
    value = row[0] if row is not None else -1
    cursor.close()
    return value
