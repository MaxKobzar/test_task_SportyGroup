"""
Screenplay Question: IsBetSlipEmpty.
"""

from framework.screenplay.abilities.browse_the_web import BrowseTheWeb
from framework.screenplay.actor import Actor


class IsBetSlipEmpty:
    """Whether the bet slip shows its empty state."""

    @classmethod
    def check(cls) -> "IsBetSlipEmpty":
        return cls()

    def answered_by(self, actor: Actor) -> bool:
        return actor.ability_to(BrowseTheWeb).on_betting_page().is_bet_slip_empty()
