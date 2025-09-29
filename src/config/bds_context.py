import abc
import logging
from collections import UserDict

from .service_factory_interface import IServiceFactory


class BDSContext(UserDict, metaclass=abc.ABCMeta):
    def __init__(self, environment: dict, logger: logging.Logger, service_factory: IServiceFactory):
        UserDict.__init__(self, environment)
        self._logger = logger
        self._service_factory = service_factory
        self._SEND_DATASET_CHECK_MESSAGES = self["SEND_DATASET_CHECK_RESULT_MESSAGES"] == "yes"
        self._FORCE_DOWNLOAD_AFTER_HOURS = int(self["FORCE_REDOWNLOAD_AFTER_HOURS"])
        self._REDOWNLOAD_FROM_NON_HEAD_SERVERS_AFTER_HOURS = int(self["REDOWNLOAD_FROM_NON_HEAD_SERVERS_AFTER_HOURS"])
        self._DATASET_GET_TIMEOUT = int(self["DATASET_GET_TIMEOUT"])
        self._DATASET_HEAD_TIMEOUT = int(self["DATASET_HEAD_TIMEOUT"])
        self._AZURE_SERVICE_BUS_WAIT_TIME = float(self["AZURE_SERVICE_BUS_WAIT_TIME"])

    @property
    def AZURE_SERVICE_BUS_WAIT_TIME(self) -> float:
        return self._AZURE_SERVICE_BUS_WAIT_TIME

    @property
    def DATASET_GET_TIMEOUT(self) -> int:
        return self._DATASET_GET_TIMEOUT

    @property
    def DATASET_HEAD_TIMEOUT(self) -> int:
        return self._DATASET_HEAD_TIMEOUT

    @property
    def FORCE_DOWNLOAD_AFTER_HOURS(self) -> int:
        return self._FORCE_DOWNLOAD_AFTER_HOURS

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def REDOWNLOAD_FROM_NON_HEAD_SERVERS_AFTER_HOURS(self) -> int:
        return self._REDOWNLOAD_FROM_NON_HEAD_SERVERS_AFTER_HOURS

    @property
    def SEND_DATASET_CHECK_MESSAGES(self) -> bool:
        return self._SEND_DATASET_CHECK_MESSAGES

    @property
    def service_factory(self) -> IServiceFactory:
        return self._service_factory
