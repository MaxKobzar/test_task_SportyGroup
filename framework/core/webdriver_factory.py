"""
WebDriver Factory module.
Creates and configures Selenium WebDriver instances according to runtime configuration.
"""
from typing import Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService

from framework.core.logger import get_logger

logger = get_logger("WebDriverFactory")


class WebDriverFactory:
    """Factory for creating configured WebDriver instances."""

    @staticmethod
    def create_driver(
        config: Optional[Any] = None,
        browser: str = "chrome",
        headless: bool = False,
        browser_width: int = 1440,
        browser_height: int = 900,
        timeout: int = 10,
        **kwargs,
    ) -> webdriver.Remote:
        """Create and return a configured WebDriver instance based on parsed options."""
        # Support passing a config object or direct keyword parameters
        if config is not None:
            browser = getattr(config, "browser", browser)
            headless = getattr(config, "headless", headless)
            browser_width = getattr(config, "browser_width", browser_width)
            browser_height = getattr(config, "browser_height", browser_height)
            timeout = getattr(config, "timeout", timeout)

        browser_name = str(browser).lower()
        logger.info(f"Initializing WebDriver for browser: {browser_name} (headless={headless})")

        if browser_name == "chrome":
            options = ChromeOptions()
            if headless:
                options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument(f"--window-size={browser_width},{browser_height}")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-notifications")
            options.add_argument("--remote-allow-origins=*")

            # Selenium 4.x native Selenium Manager automatically resolves matching driver
            service = ChromeService()
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(timeout * 3)
            driver.implicitly_wait(0)  # Favor explicit waits throughout the framework
            return driver

        raise ValueError(f"Unsupported browser: {browser_name}. Only 'chrome' is currently configured.")
