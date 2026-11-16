"""
API Test Fixtures.
Provides Screenplay actors and ledger preconditions for REST API test cases.
"""

import pytest

from framework.api.client import BettingApiClient
from framework.api.models import Match, ResetBalanceResponse
from framework.core.logger import get_logger
from framework.data.bet_mother import BetMother
from framework.screenplay.abilities.call_api import CallAPI
from framework.screenplay.actor import Actor
from framework.screenplay.questions.api_balance import ApiBalance
from framework.screenplay.tasks.place_bet_api import PlaceBetViaApi

logger = get_logger()


@pytest.fixture()
def api_actor(api_client: BettingApiClient) -> Actor:
    """Screenplay Actor equipped with API calling ability."""
    return Actor.named("Bettor").can(CallAPI.with_client(api_client))


@pytest.fixture()
def drained_balance(
    api_actor: Actor,
    reset_balance_precondition: ResetBalanceResponse,
    target_match: Match,
) -> float:
    """
    Precondition: bring the stored balance below the maximum stake with one real bet.

    There is no set-balance endpoint, and the reset value (€120.00 stored, BUG-008) is above
    the €100.00 maximum. Without this, an overdraft stake (balance + €0.01) would be rejected
    by the maximum-stake rule and the balance rule would never be exercised.
    Returns the stored balance from GET /api/balance, never the reset body (BUG-008).
    """
    api_actor.attempts_to(PlaceBetViaApi.from_request(BetMother.maximum_stake_bet(target_match.id)))
    balance = api_actor.asks_for(ApiBalance.value()).balance
    logger.info(f"Precondition: drained balance to €{balance:.2f}")
    if not 0 < balance < BetMother.MAX_STAKE:
        raise RuntimeError(
            f"Drained balance €{balance:.2f} must be in (0, {BetMother.MAX_STAKE}) "
            "so each case breaks exactly one rule."
        )
    return balance
