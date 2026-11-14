"""
Structured logging module for test execution.
"""

import logging
import sys

_LOGGER_INITIALIZED = False


def get_logger(name: str = "TestAutomation") -> logging.Logger:
    global _LOGGER_INITIALIZED
    logger = logging.getLogger(name)

    if not _LOGGER_INITIALIZED:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        _LOGGER_INITIALIZED = True

    return logger
