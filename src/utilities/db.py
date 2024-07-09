import uuid
from typing import Any

import psycopg
from yoyo import get_backend, read_migrations  # type: ignore


def apply_db_migrations(context: dict):

    backend = get_backend(
        "postgresql+psycopg://{}:{}@{}:{}/{}".format(
            context["DB_USER"], context["DB_PASS"], context["DB_HOST"], context["DB_PORT"], context["DB_NAME"]
        )
    )

    migrations = read_migrations("db-migrations")

    with backend.lock():

        # Apply any outstanding migrations
        backend.apply_migrations(backend.to_apply(migrations))


def get_db_connection(context: dict) -> psycopg.Connection:
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


def get_datasets_in_bds(context: dict) -> dict[uuid.UUID, dict]:

    connection = get_db_connection(context)
    cursor = connection.cursor(row_factory=psycopg.rows.dict_row)
    cursor.execute("""SELECT * FROM iati_datasets""")
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
                        publisher_id = %(publisher_id)s,
                        publisher_name = %(publisher_name)s,
                        type = %(type)s,
                        source_url = %(source_url)s,
                        hash = %(hash)s,
                        hash_excluding_generated_timestamp = %(hash_excluding_generated_timestamp)s,
                        last_update_check = %(last_update_check)s,
                        last_head_attempt = %(last_head_attempt)s,
                        last_head_http_status = %(last_head_http_status)s,
                        head_error_message = %(head_error_message)s,
                        last_download_attempt = %(last_download_attempt)s,
                        last_download_http_status = %(last_download_http_status)s,
                        last_successful_download = %(last_successful_download)s,
                        last_verified_on_server = %(last_verified_on_server)s,
                        download_error_message = %(download_error_message)s,
                        content_modified = %(content_modified)s,
                        content_modified_excluding_generated_timestamp =
                            %(content_modified_excluding_generated_timestamp)s,
                        server_header_last_modified = %(server_header_last_modified)s,
                        server_header_etag = %(server_header_etag)s
                    WHERE
                        iati_datasets.id = %(id)s
        """.format(
        columns, placeholders
    )
    cursor = connection.cursor()
    cursor.execute(add_sql, data)  # type: ignore
    cursor.close()
    connection.commit()


def remove_dataset_from_db(connection: psycopg.Connection, dataset_id):
    add_sql = """DELETE FROM iati_datasets WHERE id = %(dataset_id)s"""
    cursor = connection.cursor()
    cursor.execute(add_sql, {"dataset_id": dataset_id})
    cursor.close()
    connection.commit()


def execute_scalar_db_query(context: dict, sql: str) -> Any:
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
