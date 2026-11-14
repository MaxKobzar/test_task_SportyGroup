"""
Screenplay Ability: BrowseTheWeb.
Applies 'The Ideal Synergy':
The Actor's BrowseTheWeb ability delegates all page creation and DOM interactions
to PageFactory.get_page(page_type, driver).
This ensures strict decoupling:
- Tasks & Questions express user behavior and intent (Screenplay).
- Page Objects encapsulate locators, explicit waits, and DOM mechanics (POM).
- PageFactory provides the centralized Factory Method instantiation.
"""
from typing import Dict, Type, TypeVar, Union, cast
from selenium import webdriver

from framework.pages.base_page import BasePage
from framework.pages.betting_page import BettingPage
from framework.pages.page_factory import PageFactory, PageType

TPage = TypeVar("TPage", bound=BasePage)


class BrowseTheWeb:
    """
    Ability enabling an Actor to browse web applications.
    Implements the Screenplay-POM bridge by delegating page instantiation
    to PageFactory.
    """

    def __init__(self, driver: webdriver.Remote):
        self.driver = driver
        self._page_cache: Dict[str, BasePage] = {}

    @classmethod
    def with_driver(cls, driver: webdriver.Remote) -> "BrowseTheWeb":
        return cls(driver=driver)

    def on(self, page_type: Union[PageType, str, Type[BasePage]] = PageType.BETTING) -> BasePage:
        """
        Core delegation method: Obtains a Page Object via PageFactory.
        Maintains an internal cache for performance and state consistency.
        Supports PageType enum, string identifier, or POM class directly.
        """
        if isinstance(page_type, type):
            key = page_type.__name__
        elif isinstance(page_type, PageType):
            key = page_type.value
        else:
            key = str(page_type).lower()

        if key not in self._page_cache:
            self._page_cache[key] = PageFactory.get_page(page_type, self.driver)
        return self._page_cache[key]

    def on_betting_page(self) -> BettingPage:
        """Convenience method delegating to PageFactory for BettingPage."""
        return cast(BettingPage, self.on(BettingPage))
