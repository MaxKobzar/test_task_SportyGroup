"""
Page Factory module.
Implements the Factory Method pattern to instantiate and configure Page Objects.
"""

from enum import Enum
from typing import Type, Union

from selenium import webdriver

from framework.pages.base_page import BasePage
from framework.pages.betting_page import BettingPage


class PageType(str, Enum):
    """Enumeration of supported application page types."""

    BETTING = "betting"


class PageFactory:
    """Factory Method pattern implementation for Page Object creation."""

    @staticmethod
    def get_page(
        page_type: Union[PageType, str, Type[BasePage]],
        driver: webdriver.Remote,
        **kwargs,
    ) -> BasePage:
        """
        Factory Method creating and returning the appropriate BasePage subclass.
        :param page_type: Enum, string identifier, or POM class directly.
        :param driver: Active Selenium WebDriver instance.
        :param kwargs: Optional parameters passed to page constructor.
        :return: An instance of the corresponding Page Object.
        """
        # 1. Direct Page Object Model class support (e.g. BettingPage)
        if isinstance(page_type, type) and issubclass(page_type, BasePage):
            return page_type(driver=driver, **kwargs)

        # 2. String or Enum key resolution
        key = page_type.value if isinstance(page_type, PageType) else str(page_type).lower()

        if key in (PageType.BETTING.value, "betting", "bettingpage"):
            return BettingPage(driver=driver, **kwargs)

        raise ValueError(f"Unrecognized PageType '{page_type}'. Cannot instantiate Page Object.")
