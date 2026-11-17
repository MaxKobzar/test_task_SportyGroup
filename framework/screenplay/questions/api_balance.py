"""
Screenplay Question: ApiBalance.
"""

from framework.api.models.models import Balance
from framework.screenplay.abilities.call_api import CallAPI
from framework.screenplay.actor import Actor


class ApiBalance:
    """The stored balance, read from GET /api/balance."""

    @classmethod
    def value(cls) -> "ApiBalance":
        return cls()

    def answered_by(self, actor: Actor) -> Balance:
        return actor.ability_to(CallAPI).client.get_balance()
