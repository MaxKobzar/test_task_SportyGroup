"""
Screenplay Task: ResetBalanceViaApi.
"""

from framework.screenplay.abilities.call_api import CallAPI
from framework.screenplay.actor import Actor


class ResetBalanceViaApi:
    """Task to reset the user's balance via POST /api/reset-balance."""

    @classmethod
    def now(cls) -> "ResetBalanceViaApi":
        return cls()

    def perform_as(self, actor: Actor) -> None:
        actor.ability_to(CallAPI).client.reset_balance()
