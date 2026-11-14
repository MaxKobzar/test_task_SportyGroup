"""
Screenplay Question: DisplayedBalance.
"""

from framework.screenplay.abilities.browse_the_web import BrowseTheWeb


class DisplayedBalance:
    """Question inspecting the UI header balance."""

    @classmethod
    def value(cls) -> "DisplayedBalance":
        return cls()

    def answered_by(self, actor) -> float:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        return page.get_current_balance()
