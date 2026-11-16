"""
Screenplay Task: PlaceBetViaApi.
Executes wager placement directly against the REST API.
"""

from typing import Optional

from framework.api.models import PlaceBetRequest, PlaceBetResponse
from framework.screenplay.abilities.call_api import CallAPI
from framework.screenplay.actor import Actor


class PlaceBetViaApi:
    """Task to place a single bet on a sports event via the REST API."""

    def __init__(self, match_id: str, selection: str, stake: float):
        self.match_id = match_id
        self.selection = selection
        self.stake = stake
        self.response: Optional[PlaceBetResponse] = None

    @classmethod
    def on(cls, match_id: str, selection: str, stake: float) -> "PlaceBetViaApi":
        """Factory constructor for placing a bet with raw parameters."""
        return cls(match_id=match_id, selection=selection, stake=stake)

    @classmethod
    def from_request(cls, request: PlaceBetRequest) -> "PlaceBetViaApi":
        """Factory constructor for placing a bet from a domain model (e.g. from Object Mother)."""
        return cls(match_id=request.match_id, selection=request.selection, stake=request.stake)

    def perform_as(self, actor: Actor) -> None:
        """Execute POST /api/place-bet using Actor's CallAPI ability."""
        api = actor.ability_to(CallAPI)
        self.response = api.client.post_place_bet(
            match_id=self.match_id,
            selection=self.selection,
            stake=self.stake,
        )
