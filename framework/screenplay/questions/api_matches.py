"""
Screenplay Question: ApiMatchesFeed.
Retrieves and validates active matches catalog via the REST API.
"""

from typing import List

from framework.api.models import Match
from framework.screenplay.abilities.call_api import CallAPI
from framework.screenplay.actor import Actor


class ApiMatchesFeed:
    """Question querying the active match catalog from the REST API."""

    @classmethod
    def all(cls) -> "ApiMatchesFeed":
        """Factory constructor for querying all matches."""
        return cls()

    def answered_by(self, actor: Actor) -> List[Match]:
        """Execute GET /api/matches using Actor's CallAPI ability."""
        api = actor.ability_to(CallAPI)
        return api.client.get_matches()
