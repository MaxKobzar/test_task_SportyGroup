"""
Shared test suite fixtures.
"""

import pytest

from framework.core.logger import get_logger

logger = get_logger()


@pytest.fixture(autouse=True)
def log_test_lifecycle(request):
    """Log the start and finish of every test case."""
    logger.info(f"=== [START TEST] {request.node.name} ===")
    yield
    logger.info(f"=== [END TEST] {request.node.name} ===")
