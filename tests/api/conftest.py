"""
API Test Fixtures.
Provides Screenplay actors for REST API test cases.
"""

import pytest

from framework.api.client import BettingApiClient
from framework.core.logger import get_logger
from framework.screenplay.abilities.call_api import CallAPI
from framework.screenplay.actor import Actor

logger = get_logger()


@pytest.fixture()
def api_actor(api_client: BettingApiClient) -> Actor:
    """Screenplay Actor equipped with API calling ability."""
    return Actor.named("Bettor").can(CallAPI.with_client(api_client))
