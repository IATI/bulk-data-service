import logging
import sys
import time


def initialise_logging(config: dict) -> logging.Logger:

    bds_logger = logging.getLogger("bds")

    bds_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    formatter.default_time_format = "%Y-%m-%dT%H:%M:%S"
    formatter.default_msec_format = "%s,%03dZ"

    formatter.converter = time.gmtime

    handler_stdout = logging.StreamHandler(sys.stdout)
    handler_stdout.setFormatter(formatter)

    bds_logger.addHandler(handler_stdout)

    if config["LOGFILE"] != "":
        handler_file = logging.FileHandler(config["LOGFILE"])
        handler_file.setFormatter(formatter)
        bds_logger.addHandler(handler_file)

    return bds_logger
