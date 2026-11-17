"""
HTTP client architecture for REST API interaction.
BaseClient owns the session, timeouts, error mapping and Allure telemetry;
BettingApiClient adds the domain endpoints of the betting backend.
"""

import json
import logging
from decimal import Decimal
from typing import Any

import allure
import requests

from framework.api.exceptions import ApiContractViolationError, raise_for_api_error
from framework.api.models.models import (
    Balance,
    Match,
    PlaceBetRequest,
    PlaceBetResponse,
    ResetBalanceResponse,
    SelectionType,
)

logger = logging.getLogger(__name__)


class BaseClient:
    """Generic REST client: session reuse, default timeout, typed errors, Allure telemetry."""

    def __init__(self, base_url: str, timeout: float):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": "application/json", "User-Agent": "Sporty-QA-Automation-Framework"}
        )
        self.session.hooks["response"].append(self._allure_http_hook)

    def close(self) -> None:
        """Release pooled connections."""
        self.session.close()

    @staticmethod
    def _allure_http_hook(
        response: requests.Response, *args: Any, **kwargs: Any
    ) -> requests.Response:
        """Session hook attaching each request/response pair to the Allure report."""
        req = response.request
        method = req.method or "HTTP"
        elapsed_ms = int(response.elapsed.total_seconds() * 1000)
        with allure.step(f"HTTP {method} {req.path_url} [{response.status_code}] ({elapsed_ms}ms)"):
            if req.body:
                raw = req.body.decode("utf-8") if isinstance(req.body, bytes) else str(req.body)
                _attach_payload(raw, f"Request Body: {method} {req.path_url}")
            if response.text:
                _attach_payload(response.text, f"Response Body: [{response.status_code}]")
        return response

    def _url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> requests.Response:
        url = self._url(endpoint)
        logger.info("%s %s", method, url)
        kwargs.setdefault("timeout", self.timeout)
        return self.session.request(method, url, **kwargs)

    @raise_for_api_error
    def get(self, endpoint: str, **kwargs: Any) -> requests.Response:
        """GET; raises ApiException on a non-2xx response."""
        return self._request("GET", endpoint, **kwargs)

    @raise_for_api_error
    def post(self, endpoint: str, **kwargs: Any) -> requests.Response:
        """POST; raises ApiException on a non-2xx response."""
        return self._request("POST", endpoint, **kwargs)


def _attach_payload(raw: str, name: str) -> None:
    try:
        body = json.dumps(json.loads(raw), indent=2)
        attachment_type = allure.attachment_type.JSON
    except ValueError:
        body = raw
        attachment_type = allure.attachment_type.TEXT
    allure.attach(body, name=name, attachment_type=attachment_type)


def _json(response: requests.Response) -> Any:
    """Decode a JSON body with exact decimals (no float rounding of money)."""
    return response.json(parse_float=Decimal)


class BettingApiClient(BaseClient):
    """REST client for the Sporty betting backend, authenticated by the x-user-id header."""

    def __init__(self, base_url: str, user_id: str, timeout: float):
        super().__init__(base_url=base_url, timeout=timeout)
        self.user_id = user_id
        self.session.headers["x-user-id"] = user_id

    def get_balance(self) -> Balance:
        """GET /api/balance."""
        response = self.get("/api/balance")
        return ApiContractViolationError.parse(Balance, _json(response), response)

    def get_matches(self) -> list[Match]:
        """GET /api/matches."""
        response = self.get("/api/matches")
        return [ApiContractViolationError.parse(Match, m, response) for m in _json(response)]

    def place_bet(self, bet: PlaceBetRequest) -> PlaceBetResponse:
        """
        POST /api/place-bet. Accepts unvalidated requests (BetMother.with_illegal_stake)
        so rejection paths can be exercised; the stake goes on the wire as a JSON number.
        If the API accepts an illegal bet, the response breaks PlaceBetResponse and
        ApiContractViolationError is raised.
        """
        body = {
            "matchId": bet.match_id,
            "selection": SelectionType(bet.selection).value,
            "stake": float(bet.stake),
        }
        response = self.post("/api/place-bet", json=body)
        return ApiContractViolationError.parse(PlaceBetResponse, _json(response), response)

    def reset_balance(self) -> ResetBalanceResponse:
        """POST /api/reset-balance."""
        logger.info("Resetting balance for user-id %s", self.user_id)
        response = self.post("/api/reset-balance")
        return ApiContractViolationError.parse(ResetBalanceResponse, _json(response), response)
