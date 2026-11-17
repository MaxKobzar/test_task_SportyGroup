"""
Screenplay Task: NavigateToApp.
Opens the application (as the configured user) on a Page Object and waits until it is ready.
"""

from framework.pages.base_page import BasePage
from framework.pages.betting_page import BettingPage
from framework.screenplay.abilities.browse_the_web import BrowseTheWeb
from framework.screenplay.actor import Actor


class NavigateToApp:
    """Task to open the application on a given page."""

    def __init__(self, page_cls: type[BasePage]):
        self.page_cls = page_cls

    @classmethod
    def at(cls, page_cls: type[BasePage] = BettingPage) -> "NavigateToApp":
        """Open the application on page_cls."""
        return cls(page_cls)

    def perform_as(self, actor: Actor) -> None:
        browser = actor.ability_to(BrowseTheWeb)
        page = browser.on(self.page_cls)
        page.open(browser.app_url)
        page.wait_until_loaded()
