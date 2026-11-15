"""
API Test Suite using Python requests.
Validates the backend REST endpoints for balance, matches feed, and bet placement
with strict Pydantic V2 contract models.
"""

import allure
import pytest
from pydantic import ValidationError

from framework.api.client import BettingApiClient
from framework.api.models import (
    AuthError,
    Balance,
    Error,
    Match,
    Odds,
    PlaceBetResponse,
    ResetBalanceResponse,
)


@allure.epic("Backend API")
@allure.feature("Betting REST API")
class TestBettingApi:
    @allure.story("API-01: Retrieve User Balance & Schema Validation")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_get_balance(self, api_client: BettingApiClient):
        """Verify GET /api/balance returns 200 and satisfies Balance schema."""
        balance_obj: Balance = api_client.get_balance()
        assert balance_obj.currency == "EUR", f"Expected currency EUR, got {balance_obj.currency}"
        assert balance_obj.balance >= 0, f"Expected non-negative balance, got {balance_obj.balance}"

    @allure.story("API-02: Retrieve Matches Feed & Schema Validation")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_matches(self, api_client: BettingApiClient):
        """Verify GET /api/matches returns an active list conforming to Match schema."""
        matches = api_client.get_matches()
        assert len(matches) > 0, "Matches list should not be empty"

        first_match = matches[0]
        assert first_match.id, "Match must possess an ID"
        assert first_match.home_team, "Match must have a home team"
        assert first_match.away_team, "Match must have an away team"
        assert first_match.odds.home > 1.0, f"Home odds must be > 1.0, got {first_match.odds.home}"
        assert first_match.odds.draw > 1.0, f"Draw odds must be > 1.0, got {first_match.odds.draw}"
        assert first_match.odds.away > 1.0, f"Away odds must be > 1.0, got {first_match.odds.away}"

    @allure.story("API-03: Place Bet via API (Happy Path & Schema Validation)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_place_bet_happy_path(self, api_client: BettingApiClient):
        """Verify POST /api/place-bet deducts stake, returns 200, and satisfies PlaceBetResponse schema."""
        initial_balance = api_client.get_balance().balance
        matches = api_client.get_matches()
        target_match = matches[0]
        stake = 10.00

        resp: PlaceBetResponse = api_client.place_bet(
            match_id=target_match.id, selection="HOME", stake=stake
        )
        assert resp.message == "Bet placed successfully"
        assert resp.stake == stake
        assert resp.match_id == target_match.id

        current_balance = api_client.get_balance().balance
        expected_balance = round(initial_balance - stake, 2)
        assert (
            current_balance == expected_balance
        ), f"Balance not deducted correctly: expected {expected_balance}, got {current_balance}"

    @allure.story("API-04: Bet Placement with Nonexistent Match ID (Negative Schema Validation)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_place_bet_invalid_match_id(self, api_client: BettingApiClient):
        """Verify placing a bet on an invalid match ID returns 422 and satisfies Error schema."""
        resp = api_client.place_bet_raw(
            match_id="non-existent-match-9999", selection="HOME", stake=10.00
        )
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"

        # Schema validation via strict Pydantic model
        error_model: Error = api_client.parse_error(resp)
        assert error_model.error == "invalid_match"
        assert len(error_model.message) > 0

    @allure.story("API-05: Bet Placement with Invalid Selection (Negative Schema Validation)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_place_bet_invalid_selection(self, api_client: BettingApiClient):
        """Verify invalid selection returns 422 and satisfies Error schema."""
        matches = api_client.get_matches()
        resp = api_client.place_bet_raw(
            match_id=matches[0].id, selection="INVALID_SELECTION", stake=10.00
        )
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"

        error_model: Error = api_client.parse_error(resp)
        assert error_model.error == "invalid_selection"
        assert "HOME, DRAW, AWAY" in error_model.message

    @allure.story("API-06: Bet Placement with Stake Below Minimum (Negative Schema Validation)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_place_bet_stake_below_minimum(self, api_client: BettingApiClient):
        """Verify stake < 1.00 returns 422 and satisfies Error schema."""
        matches = api_client.get_matches()
        resp = api_client.place_bet_raw(match_id=matches[0].id, selection="HOME", stake=0.50)
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"

        error_model: Error = api_client.parse_error(resp)
        assert error_model.error == "invalid_stake_min"
        assert "at least 1.00" in error_model.message

    @allure.story("API-07: Bet Placement with Stake Above Maximum (Negative Schema Validation)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_place_bet_stake_above_maximum(self, api_client: BettingApiClient):
        """Verify stake > 100.00 returns 422 and satisfies Error schema."""
        matches = api_client.get_matches()
        resp = api_client.place_bet_raw(match_id=matches[0].id, selection="HOME", stake=150.00)
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"

        error_model: Error = api_client.parse_error(resp)
        assert error_model.error == "invalid_stake_max"
        assert "at most 100.00" in error_model.message

    @allure.story("API-08: Bet Placement with Invalid Stake Precision (Negative Schema Validation)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_place_bet_stake_invalid_precision(self, api_client: BettingApiClient):
        """Verify stake with >2 decimal places returns 422 and satisfies Error schema."""
        matches = api_client.get_matches()
        resp = api_client.place_bet_raw(match_id=matches[0].id, selection="HOME", stake=10.555)
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"

        error_model: Error = api_client.parse_error(resp)
        assert error_model.error == "invalid_stake_precision"

    @allure.story("API-09: Authentication Failure - Missing User ID (AuthError Schema Validation)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_place_bet_missing_user_id(self, api_client: BettingApiClient):
        """Verify omitting x-user-id header returns 401 and satisfies AuthError schema."""
        matches = api_client.get_matches()
        resp = api_client.place_bet_raw(
            match_id=matches[0].id,
            selection="HOME",
            stake=10.00,
            headers={"x-user-id": None},
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

        auth_error: AuthError = api_client.parse_auth_error(resp)
        assert auth_error.error == "missing_user_id"

    @allure.story("API-10: Authentication Failure - Invalid User ID (AuthError Schema Validation)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_place_bet_invalid_user_id(self, api_client: BettingApiClient):
        """Verify invalid x-user-id token returns 401 and satisfies AuthError schema."""
        matches = api_client.get_matches()
        resp = api_client.place_bet_raw(
            match_id=matches[0].id,
            selection="HOME",
            stake=10.00,
            headers={"x-user-id": "invalid-user-format!!!"},
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

        auth_error: AuthError = api_client.parse_auth_error(resp)
        assert auth_error.error == "invalid_user_id"

    @allure.story("API-11: Malformed Request Body (Error Schema Validation)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_place_bet_malformed_json(self, api_client: BettingApiClient):
        """Verify non-object JSON body returns 400 and satisfies Error schema."""
        resp = api_client.place_bet_raw(custom_payload=[1, 2, 3])
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"

        error_model: Error = api_client.parse_error(resp)
        assert error_model.error == "invalid_request"

    @allure.story("API-12: Reset User Balance & Schema Validation")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_reset_balance(self, api_client: BettingApiClient):
        """Verify POST /api/reset-balance restores balance and satisfies ResetBalanceResponse schema."""
        # Alter balance first
        matches = api_client.get_matches()
        api_client.place_bet(match_id=matches[0].id, selection="HOME", stake=15.00)

        # Trigger reset
        reset_resp = api_client.reset_balance()
        assert reset_resp.status_code == 200, f"Reset endpoint failed: {reset_resp.status_code}"

        reset_model = ResetBalanceResponse.model_validate(reset_resp.json())
        assert reset_model.message == "Balance reset successfully"
        assert reset_model.balance == 125.5
        assert reset_model.currency == "EUR"

        balance_obj = api_client.get_balance()
        assert (
            balance_obj.balance >= 100.0
        ), f"Expected reset balance >= 100, got {balance_obj.balance}"

    @allure.story("API-13: Contract Integrity - Reject Undocumented Extra Fields")
    @allure.severity(allure.severity_level.NORMAL)
    def test_schema_models_reject_unexpected_extra_fields(self):
        """Verify that Pydantic models strictly forbid undocumented attributes."""
        # 1. Balance model rejects extra fields
        with pytest.raises(ValidationError):
            Balance.model_validate({"balance": 100.0, "currency": "EUR", "unexpected_field": True})

        # 2. Match model rejects extra fields
        with pytest.raises(ValidationError):
            Match.model_validate(
                {
                    "id": "match-1",
                    "competition": "League",
                    "homeTeam": "A",
                    "awayTeam": "B",
                    "kickoffDate": "2026-01-01",
                    "odds": {"home": 2.0, "draw": 3.0, "away": 4.0},
                    "undocumented_field": "disallowed",
                }
            )

        # 3. Odds model rejects extra fields
        with pytest.raises(ValidationError):
            Odds.model_validate({"home": 2.0, "draw": 3.0, "away": 4.0, "extra": 1.5})

        # 4. PlaceBetResponse rejects extra fields
        with pytest.raises(ValidationError):
            PlaceBetResponse.model_validate(
                {
                    "message": "Bet placed successfully",
                    "matchId": "match-1",
                    "selection": "HOME",
                    "stake": 10.0,
                    "odds": 2.0,
                    "payout": 20.0,
                    "balance": 100.0,
                    "currency": "EUR",
                    "extra_key": "not_allowed",
                }
            )

        # 5. ResetBalanceResponse rejects extra fields
        with pytest.raises(ValidationError):
            ResetBalanceResponse.model_validate(
                {
                    "message": "Balance reset successfully",
                    "balance": 125.5,
                    "currency": "EUR",
                    "extra_prop": "disallowed",
                }
            )

        # 6. Error model rejects extra fields
        with pytest.raises(ValidationError):
            Error.model_validate({"error": "some_error", "message": "msg", "extra_prop": "illegal"})

        # 7. AuthError model rejects extra fields
        with pytest.raises(ValidationError):
            AuthError.model_validate({"error": "missing_user_id", "extra_prop": "illegal"})
