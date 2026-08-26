from azure.servicebus import ServiceBusClient
from azure.storage.blob import BlobServiceClient, ExponentialRetry
from libsuitecrm import SuiteCRM  # type: ignore

from .service_factory_interface import IServiceFactory


class ServiceFactory(IServiceFactory):

    def get_service_bus_client(self, conn_str: str, enable_logging: bool = False) -> ServiceBusClient:
        return ServiceBusClient.from_connection_string(conn_str, logging_enable=enable_logging)

    def get_suitecrm_client(self) -> SuiteCRM:
        return SuiteCRM(
            self._config["DATA_REGISTRY_SUITECRM_API_URL"],
            self._config["DATA_REGISTRY_SUITECRM_CLIENT_ID"],
            self._config["DATA_REGISTRY_SUITECRM_CLIENT_SECRET"],
            secure=self._config["DATA_REGISTRY_SUITECRM_SECURE"] != "false",
        )

    def get_azure_blob_service_client(self) -> BlobServiceClient:
        """Returns a blob service client which retries failed requests. These are the
        values the Azure SDK applies by default, set out here so that the behaviour is
        visible and can be changed deliberately.

        A request is retried on a connection or read error, on an HTTP 408, and on a 5xx
        response other than 501 and 505.

        The wait before each retry is `initial_backoff + increment_base ** retry_count`,
        varied by up to `random_jitter_range` seconds either way. The SDK raises the
        retry count before working out the wait, so the count starts at one and
        `initial_backoff` is the base of every wait rather than the first one: the three
        retries are attempted after roughly 18, 24 and 42 seconds, delaying a request
        which never succeeds by about 84 seconds in total."""

        retry_policy = ExponentialRetry(
            initial_backoff=15,
            increment_base=3,
            retry_total=3,
            retry_to_secondary=False,
            random_jitter_range=3,
        )

        return BlobServiceClient.from_connection_string(
            self._config["AZURE_STORAGE_CONNECTION_STRING"], retry_policy=retry_policy
        )
