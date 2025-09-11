import abc

from azure.servicebus import ServiceBusClient


class IServiceFactory(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def get_service_bus_client(self, conn_str: str, enable_logging: bool = False) -> ServiceBusClient:
        raise NotImplementedError
