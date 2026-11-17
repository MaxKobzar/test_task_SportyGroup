"""
Screenplay Tasks: EnterStakeAmount & SubmitBetPlacement.
"""

from decimal import Decimal

from framework.screenplay.abilities.browse_the_web import BrowseTheWeb
from framework.screenplay.actor import Actor


class EnterStakeAmount:
    """Task to type the stake into the bet slip."""

    def __init__(self, amount: Decimal):
        self.amount = amount

    @classmethod
    def of(cls, amount: Decimal) -> "EnterStakeAmount":
        return cls(amount=amount)

    def perform_as(self, actor: Actor) -> None:
        actor.ability_to(BrowseTheWeb).on_betting_page().enter_stake(self.amount)


class SubmitBetPlacement:
    """Task to click Place Bet and wait for the placement to complete."""

    @classmethod
    def now(cls) -> "SubmitBetPlacement":
        return cls()

    def perform_as(self, actor: Actor) -> None:
        actor.ability_to(BrowseTheWeb).on_betting_page().place_bet()
