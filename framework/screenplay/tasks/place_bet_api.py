"""
Screenplay Task: PlaceBetViaApi.
Places a bet directly against the REST API.
"""

from framework.api.models.models import PlaceBetRequest
from framework.screenplay.abilities.call_api import CallAPI
from framework.screenplay.actor import Actor


class PlaceBetViaApi:
    """Task to place a single bet via POST /api/place-bet."""

    def __init__(self, bet: PlaceBetRequest):
        self.bet = bet

    @classmethod
    def from_request(cls, bet: PlaceBetRequest) -> "PlaceBetViaApi":
        """Place the given bet (e.g. built by BetMother)."""
        return cls(bet)

    def perform_as(self, actor: Actor) -> None:
        actor.ability_to(CallAPI).client.place_bet(self.bet)
