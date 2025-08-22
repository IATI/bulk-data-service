from prometheus_client import Gauge, start_http_server

from config.bds_context import BDSContext
from utilities.db import execute_scalar_db_query_with_conn, get_db_connection


def get_metrics_definitions() -> list[tuple[str, str, str | None]]:
    metrics_defs = [
        ("total_number_of_datasets", "The total number of datasets", None),
        (
            "datasets_with_download",
            "The number of datasets with a last good download",
            "SELECT COUNT(id) FROM iati_datasets WHERE last_known_good_dataset_downloaded IS NOT NULL",
        ),
        ("datasets_added", "The number of datasets removed during last update", None),
        ("datasets_unregistered", "The number of datasets unregistered and so removed during last run", None),
        ("datasets_expired", "The number of datasets that expired in last run", None),
        (
            "datasets_head_request_non_200",
            "The number of HEAD requests that returned non-200 status in the last run",
            "SELECT COUNT(id) FROM iati_datasets WHERE most_recent_head_attempt_http_status != 200",
        ),
        (
            "datasets_downloads_non_200",
            "The number of download attempts that returned non-200 status in the last run",
            "SELECT COUNT(id) FROM iati_datasets WHERE most_recent_get_attempt_http_status != 200",
        ),
        ("checker_run_duration", "The time taken by the last run of the checker (seconds)", None),
        ("zipper_run_duration", "The time taken by the last run of the zipper (seconds)", None),
        ("number_crashes", "The number of crashes since app restart", None),
    ]

    return metrics_defs


def get_metric_definition(metric_name: str) -> tuple[str, str, str | None]:
    return list(filter(lambda m: m[0] == metric_name, get_metrics_definitions()))[0]


def initialise_prometheus_client(context: BDSContext):

    context["prom_metrics"] = {}

    update_prom_metric(context, "number_crashes", 0)

    start_http_server(9090)


def update_metrics_from_db(context: BDSContext):
    metrics_with_sql = list(filter(lambda m: m[2] is not None, get_metrics_definitions()))

    db_conn = get_db_connection(context)

    for metric_with_sql in metrics_with_sql:
        metric_value = execute_scalar_db_query_with_conn(db_conn, metric_with_sql[2])  # type: ignore
        update_prom_metric(context, metric_with_sql[0], metric_value)

    db_conn.close()


def get_prom_metric(context: BDSContext, metric_name: str):

    if metric_name not in context["prom_metrics"]:
        metric_def = get_metric_definition(metric_name)
        context["prom_metrics"][metric_name] = Gauge(metric_name, metric_def[1])

    return context["prom_metrics"][metric_name]


def update_prom_metric(context: BDSContext, metric_name: str, metric_value: int):

    get_prom_metric(context, metric_name).set(metric_value)
