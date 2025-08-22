import abc
import logging
from collections import UserDict


class BDSContext(UserDict, metaclass=abc.ABCMeta):
    def __init__(self, dict: dict, logger: logging.Logger):
        self._logger = logger
        UserDict.__init__(self, dict)

    @property
    def logger(self) -> logging.Logger:
        return self._logger
