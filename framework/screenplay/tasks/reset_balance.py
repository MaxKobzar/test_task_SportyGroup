"""
Screenplay Task: ResetBalance.
Resets user balance via backend API.
"""
from framework.screenplay.abilities.call_api import CallAPI


class ResetBalanceViaApi:
    """Task to trigger API balance reset."""

    @classmethod
    def now(cls) -> "ResetBalanceViaApi":
        return cls()

    def perform_as(self, actor) -> None:
        api = actor.ability_to(CallAPI)
        api.client.reset_balance()
