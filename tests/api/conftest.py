"""
API Test Fixtures.
Provides isolated preconditions and Screenplay actors for REST API test cases.
"""

import pytest

from framework.api.client import BettingApiClient
from framework.api.models import ResetBalanceResponse
from framework.core.logger import get_logger
from framework.screenplay.abilities.call_api import CallAPI
from framework.screenplay.actor import Actor

logger = get_logger()


@pytest.fixture()
def reset_balance_precondition(api_client: BettingApiClient) -> ResetBalanceResponse:
    """Precondition: Ensure candidate user starts each test with a pristine baseline balance."""
    logger.info("Precondition: Resetting user balance via API...")
    return api_client.post_reset_balance()


@pytest.fixture()
def api_actor(api_client: BettingApiClient) -> Actor:
    """Screenplay Actor equipped with API calling ability."""
    return Actor.named("Bettor").can(CallAPI.with_client(api_client))
