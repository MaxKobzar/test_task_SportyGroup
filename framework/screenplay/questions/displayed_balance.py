"""
Screenplay Question: DisplayedBalance.
"""

from decimal import Decimal

from framework.screenplay.abilities.browse_the_web import BrowseTheWeb
from framework.screenplay.actor import Actor


class DisplayedBalance:
    """The balance shown in the UI header."""

    @classmethod
    def value(cls) -> "DisplayedBalance":
        return cls()

    def answered_by(self, actor: Actor) -> Decimal:
        return actor.ability_to(BrowseTheWeb).on_betting_page().get_current_balance()
