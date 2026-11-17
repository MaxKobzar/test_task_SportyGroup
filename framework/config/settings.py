"""
Strongly-typed runtime configuration.

Built once per session from the pytest CLI options (which take their defaults from the
environment / .env) and injected into the API client and the browser ability. Nothing in
the framework reads os.environ directly, so a CLI override always wins.
"""

from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass(frozen=True)
class Settings:
    """Immutable runtime configuration for one test session."""

    base_url: str
    user_id: str
    browser: str
    headless: bool
    browser_width: int
    browser_height: int
    timeout: int

    @property
    def app_url(self) -> str:
        """Application URL that opens the UI as the configured user."""
        separator = "&" if "?" in self.base_url else "?"
        return f"{self.base_url}{separator}{urlencode({'user-id': self.user_id})}"
