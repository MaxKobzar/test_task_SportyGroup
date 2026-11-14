"""
Screenplay Task: RefreshPage.
"""
from framework.screenplay.abilities.browse_the_web import BrowseTheWeb


class RefreshPage:
    """Task to refresh the current browser page."""

    @classmethod
    def now(cls) -> "RefreshPage":
        return cls()

    def perform_as(self, actor) -> None:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on_betting_page()
        page.refresh()
        page.wait_until_loaded()
