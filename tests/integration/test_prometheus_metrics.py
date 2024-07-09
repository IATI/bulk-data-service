import uuid
from datetime import timedelta

from bulk_data_service.checker import checker_run
from helpers.helpers import get_and_clear_up_context  # noqa: F401
from utilities.misc import get_timestamp


def test_metrics_after_simple_add(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01"
    checker_run(context, {})

    expected_results = [
        ("total_number_of_datasets", 1),
        ("datasets_with_download", 1),
        ("datasets_added", 1),
        ("datasets_unregistered", 0),
        ("datasets_expired", 0),
        ("datasets_head_request_non_200", 0),
        ("datasets_downloads_non_200", 0)
    ]

    for expected_result in expected_results:
        context["prom_metrics"][expected_result[0]].set.assert_called_once_with(expected_result[1])


def test_metrics_after_new_registration(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01"
    bds_datasets = {}
    checker_run(context, bds_datasets)

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-02"
    checker_run(context, bds_datasets)

    expected_results = [
        ("total_number_of_datasets", 2),
        ("datasets_with_download", 2),
        ("datasets_added", 1),
        ("datasets_unregistered", 0),
        ("datasets_expired", 0),
        ("datasets_head_request_non_200", 0),
        ("datasets_downloads_non_200", 0)
    ]

    for expected_result in expected_results:
        context["prom_metrics"][expected_result[0]].set.assert_called_with(expected_result[1])


def test_metrics_after_unregistration(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-02"
    bds_datasets = {}
    checker_run(context, bds_datasets)

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01"
    checker_run(context, bds_datasets)

    expected_results = [
        ("total_number_of_datasets", 1),
        ("datasets_with_download", 1),
        ("datasets_added", 0),
        ("datasets_unregistered", 1),
        ("datasets_expired", 0),
        ("datasets_head_request_non_200", 0),
        ("datasets_downloads_non_200", 0)
    ]

    for expected_result in expected_results:
        context["prom_metrics"][expected_result[0]].set.assert_called_with(expected_result[1])


def test_metrics_with_success_then_immediate_404(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01"
    bds_datasets = {}
    checker_run(context, bds_datasets)

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01-dataset-403"
    checker_run(context, bds_datasets)

    expected_results = [
        ("total_number_of_datasets", 1),
        ("datasets_with_download", 1),
        ("datasets_added", 0),
        ("datasets_unregistered", 0),
        ("datasets_expired", 0),
        ("datasets_head_request_non_200", 1),
        ("datasets_downloads_non_200", 0)  # 0 b/c downloads only retried after 6 hour window
    ]

    for expected in expected_results:
        assert context["prom_metrics"][expected[0]].set.called, \
               "metric name: {}".format(expected[0])
        assert context["prom_metrics"][expected[0]].set.call_args.args == (expected[1],), \
               "metric name: {}".format(expected[0])


def test_metrics_with_success_then_delay_404(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01"
    datasets = {}
    checker_run(context, datasets)

    dataset_id = uuid.UUID("c8a40aa5-9f31-4bcf-a36f-51c1fc2cc159")

    datasets[dataset_id]["last_successful_download"] = get_timestamp() - timedelta(hours=7)

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01-dataset-403"
    checker_run(context, datasets)

    expected_results = [
        ("total_number_of_datasets", 1),
        ("datasets_with_download", 1),
        ("datasets_added", 0),
        ("datasets_unregistered", 0),
        ("datasets_expired", 0),
        ("datasets_head_request_non_200", 1),
        ("datasets_downloads_non_200", 1)
    ]

    for expected in expected_results:
        assert context["prom_metrics"][expected[0]].set.called, \
               "metric name: {}".format(expected[0])
        assert context["prom_metrics"][expected[0]].set.call_args.args == (expected[1],), \
               "metric name: {}".format(expected[0])


def test_metrics_with_only_404(get_and_clear_up_context):  # noqa: F811

    context = get_and_clear_up_context

    context["DATA_REGISTRY_BASE_URL"] = "http://localhost:3000/registration/datasets-01-dataset-403"
    checker_run(context, {})

    expected_results = [
        ("total_number_of_datasets", 1),
        ("datasets_with_download", 0),
        ("datasets_added", 1),
        ("datasets_unregistered", 0),
        ("datasets_expired", 0),
        ("datasets_head_request_non_200", 0),  # 0 b/c HEAD reqs only after successful dl
        ("datasets_downloads_non_200", 1)
    ]

    for expected in expected_results:
        assert context["prom_metrics"][expected[0]].set.called, \
               "metric name: {}".format(expected[0])
        assert context["prom_metrics"][expected[0]].set.call_args.args == (expected[1],), \
               "metric name: {}".format(expected[0])
