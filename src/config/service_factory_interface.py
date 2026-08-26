import abc
from typing import Any

from azure.servicebus import ServiceBusClient
from azure.storage.blob import BlobServiceClient
from libsuitecrm import SuiteCRM  # type: ignore


class IServiceFactory(metaclass=abc.ABCMeta):

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    @abc.abstractmethod
    def get_service_bus_client(self, conn_str: str, enable_logging: bool = False) -> ServiceBusClient:
        raise NotImplementedError

    @abc.abstractmethod
    def get_suitecrm_client(self) -> SuiteCRM:
        raise NotImplementedError

    @abc.abstractmethod
    def get_azure_blob_service_client(self) -> BlobServiceClient:
        raise NotImplementedError
