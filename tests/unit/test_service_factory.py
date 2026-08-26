from typing import Any
from unittest import mock

from azure.storage.blob import BlobServiceClient, ExponentialRetry

from config.service_factory import ServiceFactory

# a syntactically valid connection string: these tests make no connection
AZURE_STORAGE_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=http;"
    "AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
)


def get_blob_service_client_arguments(monkeypatch) -> dict[str, Any]:
    """Returns the keyword arguments which the service factory passes when it builds a
    blob service client. Taken from the call rather than read back off the client, whose
    retry policy is only reachable through private attributes."""

    arguments: dict[str, Any] = {}

    def capture_arguments(conn_str: str, **kwargs: Any) -> Any:
        arguments["connection_string"] = conn_str
        arguments.update(kwargs)
        return mock.Mock()

    monkeypatch.setattr(BlobServiceClient, "from_connection_string", capture_arguments)

    service_factory = ServiceFactory({"AZURE_STORAGE_CONNECTION_STRING": AZURE_STORAGE_CONNECTION_STRING})

    service_factory.get_azure_blob_service_client()

    return arguments


def get_retry_policy(monkeypatch) -> ExponentialRetry:
    retry_policy = get_blob_service_client_arguments(monkeypatch)["retry_policy"]

    assert isinstance(retry_policy, ExponentialRetry)

    return retry_policy


def test_blob_service_client_is_given_the_configured_connection_string(monkeypatch):

    arguments = get_blob_service_client_arguments(monkeypatch)

    assert arguments["connection_string"] == AZURE_STORAGE_CONNECTION_STRING


def test_blob_service_client_is_given_an_explicit_retry_policy(monkeypatch):

    assert "retry_policy" in get_blob_service_client_arguments(monkeypatch)


def test_blob_service_client_retries_with_exponential_backoff(monkeypatch):

    assert isinstance(get_blob_service_client_arguments(monkeypatch)["retry_policy"], ExponentialRetry)


def test_blob_service_client_retry_values_are_set_explicitly(monkeypatch):

    retry_policy = get_retry_policy(monkeypatch)

    assert retry_policy.total_retries == 3
    assert retry_policy.connect_retries == 3
    assert retry_policy.read_retries == 3
    assert retry_policy.status_retries == 3
    assert retry_policy.retry_to_secondary is False
    assert retry_policy.initial_backoff == 15
    assert retry_policy.increment_base == 3
    assert retry_policy.random_jitter_range == 3


def test_blob_service_client_waits_as_documented_before_each_retry(monkeypatch):
    """Checks the backoff values which get_azure_blob_service_client's docstring quotes.
    The SDK raises the retry count before asking for the backoff time, so the first
    retry is calculated with a count of one rather than zero."""

    retry_policy = get_retry_policy(monkeypatch)

    for retry_count, expected_wait in [(1, 18), (2, 24), (3, 42)]:
        wait = retry_policy.get_backoff_time({"count": retry_count})

        assert expected_wait - 3 <= wait <= expected_wait + 3
