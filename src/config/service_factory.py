from azure.servicebus import ServiceBusClient
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
