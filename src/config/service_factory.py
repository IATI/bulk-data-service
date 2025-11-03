from azure.servicebus import ServiceBusClient

from .service_factory_interface import IServiceFactory


class AzureServiceFactory(IServiceFactory):

    def get_service_bus_client(self, conn_str: str, enable_logging: bool = False) -> ServiceBusClient:
        return ServiceBusClient.from_connection_string(conn_str, logging_enable=enable_logging)
