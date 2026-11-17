"""
Screenplay Question: ApiMatchesFeed.
"""

from framework.api.models.betting import Match
from framework.screenplay.abilities.call_api import CallAPI
from framework.screenplay.actor import Actor


class ApiMatchesFeed:
    """The match catalog, read from GET /api/matches."""

    @classmethod
    def all(cls) -> "ApiMatchesFeed":
        return cls()

    def answered_by(self, actor: Actor) -> list[Match]:
        return actor.ability_to(CallAPI).client.get_matches()
