"""
WebDriver Factory module.
Creates and configures Selenium WebDriver instances from the session Settings.
"""

import logging

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

from framework.config.settings import Settings

logger = logging.getLogger(__name__)

PAGE_LOAD_TIMEOUT_FACTOR = 3  # full page loads get more headroom than element waits


class WebDriverFactory:
    """Factory for creating configured WebDriver instances."""

    @staticmethod
    def create_driver(settings: Settings) -> WebDriver:
        """Create a WebDriver for settings.browser; Selenium Manager resolves the driver binary."""
        browser = settings.browser.lower()
        logger.info("Starting %s (headless=%s)", browser, settings.headless)

        if browser != "chrome":
            raise ValueError(f"Unsupported browser {browser!r}: only 'chrome' is configured.")

        options = webdriver.ChromeOptions()
        options.add_argument(f"--window-size={settings.browser_width},{settings.browser_height}")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        if settings.headless:
            options.add_argument("--headless=new")
            # Container/CI-only flags: shared memory is small and there is no user namespace.
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(settings.timeout * PAGE_LOAD_TIMEOUT_FACTOR)
        driver.implicitly_wait(0)  # explicit waits only; mixing both makes timeouts unpredictable
        return driver
