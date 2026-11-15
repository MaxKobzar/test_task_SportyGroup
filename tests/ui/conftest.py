"""
UI Test Fixtures.
Provides function-level WebDriver instances configurable via parsed pytest_addoption,
Page Objects via Factory, Screenplay Actors, and API-driven test isolation preconditions.
"""

import pytest
from selenium import webdriver

from framework.api.client import BettingApiClient
from framework.core.logger import get_logger
from framework.core.webdriver_factory import WebDriverFactory

logger = get_logger()


@pytest.fixture()
def driver(request: pytest.FixtureRequest) -> webdriver.Remote:
    """
    Function-level WebDriver fixture.
    Configurable depending on parsed pytest_addoption CLI arguments and .env.
    """
    browser = request.config.getoption("--browser")
    headless_raw = request.config.getoption("--headless")
    headless = (
        headless_raw.lower() in ("true", "1", "yes")
        if isinstance(headless_raw, str)
        else bool(headless_raw)
    )
    browser_width = request.config.getoption("--browser-width")
    browser_height = request.config.getoption("--browser-height")
    timeout = request.config.getoption("--timeout")

    logger.info(
        f"Initializing function-level WebDriver from parsed pytest_addoption: "
        f"browser={browser}, headless={headless}, viewport={browser_width}x{browser_height}, timeout={timeout}"
    )

    driver_instance = WebDriverFactory.create_driver(
        browser=browser,
        headless=headless,
        browser_width=browser_width,
        browser_height=browser_height,
        timeout=timeout,
    )
    yield driver_instance
    logger.info("Quitting WebDriver instance...")
    driver_instance.quit()


@pytest.fixture()
def reset_balance_precondition(api_client: BettingApiClient):
    """Precondition: Ensure candidate user starts each test with a clean baseline balance."""
    logger.info("Precondition: Resetting user balance via API...")
    return api_client.reset_balance()
