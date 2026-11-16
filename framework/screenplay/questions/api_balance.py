"""
Screenplay Question: ApiBalance.
Retrieves and validates current user account balance via the REST API.
"""

from framework.api.models import Balance
from framework.screenplay.abilities.call_api import CallAPI
from framework.screenplay.actor import Actor


class ApiBalance:
    """Question inspecting user balance directly from the backend ledger."""

    @classmethod
    def value(cls) -> "ApiBalance":
        """Factory constructor for querying balance."""
        return cls()

    def answered_by(self, actor: Actor) -> Balance:
        """Execute GET /api/balance using Actor's CallAPI ability."""
        api = actor.ability_to(CallAPI)
        return api.client.get_balance()
