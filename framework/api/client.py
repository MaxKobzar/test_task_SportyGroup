"""
HTTP Client architecture for REST API interaction.
Provides BaseClient for session and telemetry management,
and domain-specific BettingApiClient for betting operations.
"""

import json
from typing import Any, Dict, List, Optional

import allure
import requests

from framework.api.exceptions import validate_rest_error
from framework.api.models import (
    Balance,
    Match,
    PlaceBetResponse,
    ResetBalanceResponse,
)
from framework.core.logger import get_logger

logger = get_logger()


class BaseClient:
    """Generic REST API Client providing session management, HTTP wrappers, and Allure telemetry."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Sporty-QA-Automation-Framework",
            }
        )
        # Register automated Allure reporting hook for all session requests/responses
        self.session.hooks["response"].append(self._allure_http_hook)

    @staticmethod
    def _allure_http_hook(
        response: requests.Response, *args: Any, **kwargs: Any
    ) -> requests.Response:
        """
        Automated Session Hook: Intercepts all outgoing requests and incoming responses,
        attaching formatted wire-level telemetry to Allure reports.
        """
        try:
            req = response.request
            method = req.method or "HTTP"
            status = response.status_code
            elapsed_ms = int(response.elapsed.total_seconds() * 1000)

            step_title = f"HTTP {method} {req.path_url} [{status}] ({elapsed_ms}ms)"
            with allure.step(step_title):
                # 1. Attach Request Payload (if present)
                if req.body:
                    raw_body = (
                        req.body.decode("utf-8") if isinstance(req.body, bytes) else str(req.body)
                    )
                    try:
                        formatted_req = json.dumps(json.loads(raw_body), indent=2)
                        attach_type = allure.attachment_type.JSON
                    except (ValueError, TypeError):
                        formatted_req = raw_body
                        attach_type = allure.attachment_type.TEXT

                    allure.attach(
                        formatted_req,
                        name=f"Request Body: {method} {req.path_url}",
                        attachment_type=attach_type,
                    )

                # 2. Attach Response Payload (if present)
                if response.text:
                    try:
                        formatted_res = json.dumps(response.json(), indent=2)
                        attach_type = allure.attachment_type.JSON
                    except (ValueError, TypeError):
                        formatted_res = response.text
                        attach_type = allure.attachment_type.TEXT

                    allure.attach(
                        formatted_res,
                        name=f"Response Body: [{status}] ({elapsed_ms}ms)",
                        attachment_type=attach_type,
                    )
        except (TypeError, ValueError, AttributeError, OSError) as ex:
            logger.debug(f"Could not attach HTTP telemetry to Allure: {ex}")

        return response

    def _build_url(self, endpoint: str) -> str:
        """Construct full absolute URL from endpoint path."""
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    @validate_rest_error
    def get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Execute GET request with automated telemetry and optional header overrides."""
        url = self._build_url(endpoint)
        logger.info(f"GET {url}")
        return self.session.get(url, params=params, headers=headers, **kwargs)

    @validate_rest_error
    def post(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[dict] = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Execute POST request with automated telemetry and optional header overrides."""
        url = self._build_url(endpoint)
        logger.info(f"POST {url}")
        return self.session.post(url, data=data, json=json, headers=headers, **kwargs)

    @validate_rest_error
    def put(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[dict] = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Execute PUT request with automated telemetry and optional header overrides."""
        url = self._build_url(endpoint)
        logger.info(f"PUT {url}")
        return self.session.put(url, data=data, json=json, headers=headers, **kwargs)

    @validate_rest_error
    def delete(
        self,
        endpoint: str,
        headers: Optional[dict] = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Execute DELETE request with automated telemetry and optional header overrides."""
        url = self._build_url(endpoint)
        logger.info(f"DELETE {url}")
        return self.session.delete(url, headers=headers, **kwargs)


class BettingApiClient(BaseClient):
    """REST API Client for interacting with the Sporty Betting Backend."""

    def __init__(self, base_url: str, user_id: str):
        super().__init__(base_url=base_url)
        self.user_id = user_id
        self.session.headers.update({"x-user-id": self.user_id})

    def get_balance(self, headers: Optional[Dict[str, Any]] = None) -> Balance:
        """Fetch current user balance as defined in OpenAPI Balance schema."""
        logger.info(f"Fetching balance for user-id: {self.user_id}")
        resp = self.get("/api/balance", headers=headers)
        return Balance.model_validate(resp.json())

    def get_matches(self, headers: Optional[Dict[str, Any]] = None) -> List[Match]:
        """Fetch list of available matches and strictly validate schema."""
        resp = self.get("/api/matches", headers=headers)
        return [Match.model_validate(m) for m in resp.json()]

    def post_place_bet(
        self,
        match_id: Optional[str] = None,
        selection: Optional[str] = None,
        stake: Optional[float] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> PlaceBetResponse:
        """Place bet, verify HTTP success, and return validated PlaceBetResponse."""
        body: Dict[str, Any] = {
            "matchId": match_id,
            "selection": selection,
            "stake": stake,
        }
        resp = self.post("/api/place-bet", json=body, headers=headers)
        return PlaceBetResponse.model_validate(resp.json())

    def post_reset_balance(self, headers: Optional[Dict[str, Any]] = None) -> ResetBalanceResponse:
        """Reset balance and return validated ResetBalanceResponse."""
        logger.info(f"Resetting balance for user-id: {self.user_id}")
        resp = self.post("/api/reset-balance", headers=headers)
        return ResetBalanceResponse.model_validate(resp.json())
