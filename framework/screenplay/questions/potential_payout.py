"""
Screenplay Question: PotentialPayout.
"""

from decimal import Decimal

from framework.screenplay.abilities.browse_the_web import BrowseTheWeb
from framework.screenplay.actor import Actor


class PotentialPayout:
    """The potential payout shown in the bet slip."""

    @classmethod
    def value(cls) -> "PotentialPayout":
        return cls()

    def answered_by(self, actor: Actor) -> Decimal:
        return actor.ability_to(BrowseTheWeb).on_betting_page().get_potential_payout()
