"""
HTTP Client for the Betting Application REST API.
"""
import json
from typing import List, Optional
import allure
import requests

from framework.api.models import (
    AuthError,
    Balance,
    BalanceResponse,
    BetPlacementPayload,
    BetPlacementResponse,
    Error,
    Match,
    PlaceBetRequest,
    PlaceBetResponse,
)
from framework.core.logger import get_logger

logger = get_logger("ApiClient")


class BettingApiClient:
    """REST API Client for interacting with the Sporty Betting Backend."""

    def __init__(self, base_url: str, user_id: str):
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        self.session = requests.Session()
        self.session.headers.update({
            "x-user-id": self.user_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Sporty-QA-Automation-Framework"
        })

    def _attach_to_allure(self, name: str, data: str, mime: str = "application/json"):
        try:
            allure.attach(data, name=name, attachment_type=allure.attachment_type.JSON if mime == "application/json" else allure.attachment_type.TEXT)
        except Exception:
            pass

    def get_balance(self) -> Balance:
        """Fetch current user balance as defined in OpenAPI Balance schema."""
        url = f"{self.base_url}/api/balance"
        logger.info(f"GET {url} [user-id: {self.user_id}]")
        resp = self.session.get(url)
        self._attach_to_allure("GET /api/balance response", resp.text)
        resp.raise_for_status()
        return Balance.model_validate(resp.json())

    def get_matches(self) -> List[Match]:
        """Fetch list of available matches."""
        url = f"{self.base_url}/api/matches"
        logger.info(f"GET {url}")
        resp = self.session.get(url)
        self._attach_to_allure("GET /api/matches response", resp.text)
        resp.raise_for_status()
        return [Match.model_validate(m) for m in resp.json()]

    def place_bet_raw(self, match_id: str, selection: str, stake: float) -> requests.Response:
        """Send raw bet placement request to inspect status codes and validation messages."""
        url = f"{self.base_url}/api/place-bet"
        payload = {"matchId": match_id, "selection": selection, "stake": stake}
        logger.info(f"POST {url} with payload {payload}")
        self._attach_to_allure("POST /api/place-bet request", json.dumps(payload, indent=2))
        resp = self.session.post(url, json=payload)
        self._attach_to_allure(f"POST /api/place-bet response ({resp.status_code})", resp.text)
        return resp

    def place_bet(self, match_id: str, selection: str, stake: float) -> PlaceBetResponse:
        """Place bet and parse standard OpenAPI PlaceBetResponse."""
        resp = self.place_bet_raw(match_id=match_id, selection=selection, stake=stake)
        resp.raise_for_status()
        return PlaceBetResponse.model_validate(resp.json())

    def reset_balance(self) -> requests.Response:
        """Reset user balance to default value (125.50)."""
        url = f"{self.base_url}/api/reset-balance"
        logger.info(f"POST {url} [user-id: {self.user_id}]")
        resp = self.session.post(url)
        self._attach_to_allure("POST /api/reset-balance response", resp.text)
        return resp
