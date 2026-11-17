"""Page Object Model: base page, page objects and the Page Factory."""

from framework.pages.base_page import BasePage, Locator
from framework.pages.betting_page import BettingPage, Receipt, SlipSelection
from framework.pages.page_factory import PageFactory, PageType

__all__ = [
    "BasePage",
    "BettingPage",
    "Locator",
    "PageFactory",
    "PageType",
    "Receipt",
    "SlipSelection",
]
