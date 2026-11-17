"""
UI Test Fixtures.
Provides the function-level WebDriver and the Screenplay actor that browses the app.
"""

import logging
from collections.abc import Generator

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from framework.config import Settings
from framework.core import WebDriverFactory
from framework.screenplay import Actor
from framework.screenplay.abilities import BrowseTheWeb

logger = logging.getLogger(__name__)


@pytest.fixture
def driver(settings: Settings) -> Generator[WebDriver, None, None]:
    """Function-level WebDriver built from the session settings; always quit at teardown."""
    driver_instance = WebDriverFactory.create_driver(settings)
    yield driver_instance
    logger.info("Quitting WebDriver")
    driver_instance.quit()


@pytest.fixture
def bettor_actor(driver: WebDriver, settings: Settings) -> Actor:
    """Precondition: Screenplay Actor able to browse the app as the configured user."""
    return Actor.named("Bettor").can(BrowseTheWeb.using(driver, settings))
