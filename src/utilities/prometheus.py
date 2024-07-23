from prometheus_client import Gauge, start_http_server

from utilities.db import execute_scalar_db_query_with_conn, get_db_connection


def get_metrics_definitions(context: dict) -> list:
    metrics_defs = [
        ("total_number_of_datasets", "The total number of datasets"),
        ("datasets_with_download", "The number of datasets with a last good download"),
        ("datasets_added", "The number of datasets removed during last update"),
        ("datasets_unregistered", "The number of datasets unregistered and so removed during last run"),
        ("datasets_expired", "The number of datasets that expired in last run"),
        (
            "datasets_head_request_non_200",
            "The number of HEAD requests that returned non-200 status in the last run",
        ),
        (
            "datasets_downloads_non_200",
            "The number of download attempts that returned non-200 status in the last run",
        ),
        (
            "checker_run_duration",
            "The time taken by the last run of the checker (seconds)",
        ),
        (
            "number_crashes",
            "The number of crashes since app restart",
        ),
    ]

    return metrics_defs


def initialise_prometheus_client(context: dict) -> dict:

    metrics = {}

    for metric in get_metrics_definitions(context):
        metrics[metric[0]] = Gauge(metric[0], metric[1])

    metrics["number_crashes"].set(0)

    context["prom_metrics"] = metrics

    start_http_server(9090)

    return context


def update_metrics_from_db(context: dict) -> dict:
    metrics_and_their_sql = [
        (
            "datasets_with_download",
            ("SELECT COUNT(id) FROM iati_datasets WHERE " "last_successful_download IS NOT NULL"),
        ),
        (
            "datasets_head_request_non_200",
            ("SELECT COUNT(id) FROM iati_datasets WHERE " "last_head_http_status != 200"),
        ),
        (
            "datasets_downloads_non_200",
            ("SELECT COUNT(id) FROM iati_datasets WHERE " "last_download_http_status != 200"),
        ),
    ]

    db_conn = get_db_connection(context)

    for metric_from_db in metrics_and_their_sql:
        metric = execute_scalar_db_query_with_conn(db_conn, metric_from_db[1])
        context["prom_metrics"][metric_from_db[0]].set(metric)

    db_conn.close()

    return context
