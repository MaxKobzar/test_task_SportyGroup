"""
Screenplay Question: PlaceBetButtonStatus & InlineErrorMessage.
"""

from typing import Optional

from framework.screenplay.abilities.browse_the_web import BrowseTheWeb


class IsPlaceBetEnabled:
    """Question inspecting whether the Place Bet button is enabled."""

    @classmethod
    def check(cls) -> "IsPlaceBetEnabled":
        return cls()

    def answered_by(self, actor) -> bool:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        return page.is_place_bet_enabled()


class InlineErrorMessage:
    """Question retrieving inline error text if present."""

    @classmethod
    def text(cls) -> "InlineErrorMessage":
        return cls()

    def answered_by(self, actor) -> Optional[str]:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        return page.get_inline_error()
