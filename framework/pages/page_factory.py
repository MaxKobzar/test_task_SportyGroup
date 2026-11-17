"""
Page Factory module.
Factory Method for Page Objects: callers name a page (PageType or the class itself) and
receive an instance wired with the session driver and timeout.
"""

from enum import Enum
from typing import TypeVar, overload

from selenium.webdriver.remote.webdriver import WebDriver

from framework.pages.base_page import BasePage
from framework.pages.betting_page import BettingPage

TPage = TypeVar("TPage", bound=BasePage)


class PageType(str, Enum):
    """Supported application pages."""

    BETTING = "betting"


_PAGES: dict[PageType, type[BasePage]] = {
    PageType.BETTING: BettingPage,
}


class PageFactory:
    """Factory Method implementation for Page Object creation."""

    @overload
    @staticmethod
    def get_page(page: type[TPage], driver: WebDriver, timeout: float) -> TPage: ...

    @overload
    @staticmethod
    def get_page(page: PageType, driver: WebDriver, timeout: float) -> BasePage: ...

    @staticmethod
    def get_page(page: type[BasePage] | PageType, driver: WebDriver, timeout: float) -> BasePage:
        """Instantiate the Page Object for a PageType or a BasePage subclass."""
        page_cls = _PAGES[page] if isinstance(page, PageType) else page
        return page_cls(driver=driver, timeout=timeout)
