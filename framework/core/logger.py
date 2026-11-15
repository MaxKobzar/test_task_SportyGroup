"""
Structured logging module for test execution.
Automatically determines the caller's module without requiring manual logger names.
Formats log lines starting with: timestamp, filename, log level, log message.
"""

import inspect
import logging
import os
import sys
from pathlib import Path
from typing import Optional

LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(filename)s] : %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_old_factory = logging.getLogRecordFactory()


def _relpath_record_factory(*args, **kwargs) -> logging.LogRecord:
    """
    LogRecord factory that resolves %(filename)s relative to the project content root.
    For example: 'framework/api/client.py' instead of 'client.py'.
    """
    record = _old_factory(*args, **kwargs)
    try:
        rel = os.path.relpath(record.pathname, PROJECT_ROOT)
        if not rel.startswith(".."):
            record.filename = rel
            record.relpath = rel
        else:
            record.relpath = record.filename
    except (ValueError, TypeError, OSError):
        record.relpath = record.filename
    return record


if logging.getLogRecordFactory() != _relpath_record_factory:
    logging.setLogRecordFactory(_relpath_record_factory)


def _configure_standalone_logger() -> None:
    """
    Configures root logger handler for standalone scripts outside of pytest.

    When running tests under pytest, pytest's logging plugin manages handlers and
    live logging to prevent duplicate output.
    """
    if "pytest" in sys.modules or os.environ.get("PYTEST_CURRENT_TEST"):
        return
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT))
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)


_configure_standalone_logger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve or create a logger instance.

    If 'name' is omitted, automatically infers the caller's module name
    via stack inspection so callers do not have to pass hardcoded names like 'ApiClient'.
    Log format strictly starts with:
        <timestamp> [<filename>] [<level>]: <message>
    """
    _configure_standalone_logger()
    if name is None:
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_module = frame.f_back.f_globals.get("__name__")
            if caller_module and caller_module != "__main__":
                name = caller_module
            else:
                caller_file = frame.f_back.f_code.co_filename
                name = Path(caller_file).stem
        if not name:
            name = "TestAutomation"

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger
