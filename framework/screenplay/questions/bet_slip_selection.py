"""
Screenplay Question: BetSlipSelection.
"""

from framework.pages.betting_page import SlipSelection
from framework.screenplay.abilities.browse_the_web import BrowseTheWeb
from framework.screenplay.actor import Actor


class BetSlipSelection:
    """The active selection shown in the bet slip (teams, market, odds)."""

    @classmethod
    def details(cls) -> "BetSlipSelection":
        return cls()

    def answered_by(self, actor: Actor) -> SlipSelection:
        return actor.ability_to(BrowseTheWeb).on_betting_page().get_selection_details()
