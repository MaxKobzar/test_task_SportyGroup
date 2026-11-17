"""
Screenplay Task: SubmitBetPlacement.
"""

from framework.screenplay.abilities.browse_the_web import BrowseTheWeb
from framework.screenplay.actor import Actor


class SubmitBetPlacement:
    """Task to click Place Bet and wait for the placement to complete."""

    @classmethod
    def now(cls) -> "SubmitBetPlacement":
        return cls()

    def perform_as(self, actor: Actor) -> None:
        actor.ability_to(BrowseTheWeb).on_betting_page().place_bet()
