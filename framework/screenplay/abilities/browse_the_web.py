"""
Screenplay Ability: BrowseTheWeb.
The Screenplay-POM bridge: Tasks and Questions express user intent, Page Objects own
locators and waits, and this ability obtains pages through PageFactory with the session
driver, application URL and timeout.
"""

from typing import TypeVar, cast

from selenium.webdriver.remote.webdriver import WebDriver

from framework.config.settings import Settings
from framework.pages.base_page import BasePage
from framework.pages.betting_page import BettingPage
from framework.pages.page_factory import PageFactory

TPage = TypeVar("TPage", bound=BasePage)


class BrowseTheWeb:
    """Ability to use the web application in a browser."""

    def __init__(self, driver: WebDriver, app_url: str, timeout: float):
        self.driver = driver
        self.app_url = app_url
        self.timeout = timeout
        self._pages: dict[type[BasePage], BasePage] = {}

    @classmethod
    def using(cls, driver: WebDriver, settings: Settings) -> "BrowseTheWeb":
        """Create the ability from the session driver and settings."""
        return cls(driver=driver, app_url=settings.app_url, timeout=settings.timeout)

    def on(self, page_cls: type[TPage]) -> TPage:
        """Page Object for page_cls, created once per ability via PageFactory."""
        if page_cls not in self._pages:
            self._pages[page_cls] = PageFactory.get_page(page_cls, self.driver, self.timeout)
        return cast(TPage, self._pages[page_cls])

    def on_betting_page(self) -> BettingPage:
        """Shortcut for the betting page."""
        return self.on(BettingPage)
