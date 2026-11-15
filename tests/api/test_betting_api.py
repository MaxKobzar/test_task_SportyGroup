"""
API Test Suite using Python requests.
Validates the backend REST endpoints for balance, matches feed, and bet placement
with strict Pydantic V2 contract models.
"""

import allure
import pytest
from pydantic import ValidationError

from framework.api.client import BettingApiClient
from framework.api.exceptions import ApiAuthError, ApiValidationError
from framework.api.models import (
    AuthError,
    Balance,
    Error,
    Error400,
    Error401,
    Error405,
    Error409,
    Error422,
    Error500,
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

        bet_model: PlaceBetResponse = api_client.place_bet(
            match_id=target_match.id, selection="HOME", stake=stake
        )
        assert bet_model.message == "Bet placed successfully"
        assert bet_model.stake == stake
        assert bet_model.match_id == target_match.id

        current_balance = api_client.get_balance().balance
        expected_balance = round(initial_balance - stake, 2)
        assert (
            current_balance == expected_balance
        ), f"Balance not deducted correctly: expected {expected_balance}, got {current_balance}"

    @allure.story("API-04: Bet Placement with Nonexistent Match ID (Negative Schema Validation)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_place_bet_invalid_match_id(self, api_client: BettingApiClient):
        """Verify placing a bet on an invalid match ID raises ApiValidationError with Error schema."""
        with pytest.raises(ApiValidationError) as exc_info:
            api_client.place_bet(match_id="non-existent-match-9999", selection="HOME", stake=10.00)

        assert exc_info.value.status_code == 422
        assert exc_info.value.error.error == "invalid_match"
        assert len(exc_info.value.error.message) > 0

    @allure.story("API-05: Bet Placement with Invalid Selection (Negative Schema Validation)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_place_bet_invalid_selection(self, api_client: BettingApiClient):
        """Verify invalid selection raises ApiValidationError with Error schema."""
        matches = api_client.get_matches()
        with pytest.raises(ApiValidationError) as exc_info:
            api_client.place_bet(match_id=matches[0].id, selection="INVALID_SELECTION", stake=10.00)

        assert exc_info.value.status_code == 422
        assert exc_info.value.error.error == "invalid_selection"
        assert "HOME, DRAW, AWAY" in exc_info.value.error.message

    @allure.story("API-06: Bet Placement with Stake Below Minimum (Negative Schema Validation)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_place_bet_stake_below_minimum(self, api_client: BettingApiClient):
        """Verify stake < 1.00 raises ApiValidationError with Error schema."""
        matches = api_client.get_matches()
        with pytest.raises(ApiValidationError) as exc_info:
            api_client.place_bet(match_id=matches[0].id, selection="HOME", stake=0.50)

        assert exc_info.value.status_code == 422
        assert exc_info.value.error.error == "invalid_stake_min"
        assert "at least 1.00" in exc_info.value.error.message

    @allure.story("API-07: Bet Placement with Stake Above Maximum (Negative Schema Validation)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_place_bet_stake_above_maximum(self, api_client: BettingApiClient):
        """Verify stake > 100.00 raises ApiValidationError with Error schema."""
        matches = api_client.get_matches()
        with pytest.raises(ApiValidationError) as exc_info:
            api_client.place_bet(match_id=matches[0].id, selection="HOME", stake=150.00)

        assert exc_info.value.status_code == 422
        assert exc_info.value.error.error == "invalid_stake_max"
        assert "at most 100.00" in exc_info.value.error.message

    @allure.story("API-08: Bet Placement with Invalid Stake Precision (Negative Schema Validation)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_place_bet_stake_invalid_precision(self, api_client: BettingApiClient):
        """Verify stake with >2 decimal places raises ApiValidationError with Error schema."""
        matches = api_client.get_matches()
        with pytest.raises(ApiValidationError) as exc_info:
            api_client.place_bet(match_id=matches[0].id, selection="HOME", stake=10.555)

        assert exc_info.value.status_code == 422
        assert exc_info.value.error.error == "invalid_stake_precision"

    @allure.story("API-09: Authentication Failure - Missing User ID (AuthError Schema Validation)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_place_bet_missing_user_id(self, api_client: BettingApiClient):
        """Verify omitting x-user-id header raises ApiAuthError with AuthError schema."""
        matches = api_client.get_matches()
        with pytest.raises(ApiAuthError) as exc_info:
            api_client.place_bet(
                match_id=matches[0].id,
                selection="HOME",
                stake=10.00,
                headers={"x-user-id": None},
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.auth_error.error == "missing_user_id"
        assert exc_info.value.strict_model == Error401()

    @allure.story("API-10: Authentication Failure - Invalid User ID (AuthError Schema Validation)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_place_bet_invalid_user_id(self, api_client: BettingApiClient):
        """Verify invalid x-user-id token raises ApiAuthError with AuthError schema."""
        matches = api_client.get_matches()
        with pytest.raises(ApiAuthError) as exc_info:
            api_client.place_bet(
                match_id=matches[0].id,
                selection="HOME",
                stake=10.00,
                headers={"x-user-id": "invalid-user-format!!!"},
            )

        assert exc_info.value.status_code == 401
        assert exc_info.value.auth_error.error == "invalid_user_id"

    @allure.story("API-11: Malformed Request Body (Error Schema Validation)")
    @allure.severity(allure.severity_level.NORMAL)
    def test_place_bet_malformed_json(self, api_client: BettingApiClient):
        """Verify non-object JSON body raises ApiValidationError with Error schema."""
        with pytest.raises(ApiValidationError) as exc_info:
            api_client.post("/api/place-bet", json=[1, 2, 3])

        assert exc_info.value.status_code == 400
        assert exc_info.value.error.error == "invalid_request"
        assert exc_info.value.strict_model == Error400()

    @allure.story("API-12: Reset User Balance & Schema Validation")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_reset_balance(self, api_client: BettingApiClient):
        """Verify POST /api/reset-balance restores balance and satisfies ResetBalanceResponse schema."""
        # Alter balance first
        matches = api_client.get_matches()
        api_client.place_bet(match_id=matches[0].id, selection="HOME", stake=15.00)

        # Trigger reset via typed SDK method
        reset_model: ResetBalanceResponse = api_client.reset_balance()
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

        # 8. Strict Error400 validates exact contract and rejects invalid values
        e400 = Error400.model_validate(
            {"error": "invalid_request", "message": "Request body must be a JSON object."}
        )
        assert e400.error == "invalid_request"
        assert e400.message == "Request body must be a JSON object."
        with pytest.raises(ValidationError):
            Error400.model_validate({"error": "invalid_request", "message": "Wrong message"})
        with pytest.raises(ValidationError):
            Error400.model_validate(
                {
                    "error": "invalid_request",
                    "message": "Request body must be a JSON object.",
                    "extra": "bad",
                }
            )

        # 9. Strict Error401 validates exact contract and rejects invalid values
        e401 = Error401.model_validate({"error": "missing_user_id"})
        assert e401.error == "missing_user_id"
        with pytest.raises(ValidationError):
            Error401.model_validate(
                {"error": "invalid_user_id"}
            )  # Only missing_user_id allowed in Error401
        with pytest.raises(ValidationError):
            Error401.model_validate({"error": "missing_user_id", "extra": "bad"})

        # 10. Strict Error405 validates exact contract and rejects invalid values
        e405 = Error405.model_validate(
            {"error": "insufficient_balance", "message": "Insufficient balance"}
        )
        assert e405.error == "insufficient_balance"
        with pytest.raises(ValidationError):
            Error405.model_validate({"error": "wrong", "message": "Insufficient balance"})

        # 11. Strict Error409 validates exact contract and rejects invalid values
        e409 = Error409.model_validate(
            {"error": "insufficient_balance", "message": "Insufficient balance"}
        )
        assert e409.error == "insufficient_balance"
        with pytest.raises(ValidationError):
            Error409.model_validate({"error": "wrong", "message": "Insufficient balance"})

        # 12. Strict Error422 validates exact contract and rejects invalid values
        e422 = Error422.model_validate(
            {"error": "invalid_match_id", "message": "Match id is invalid."}
        )
        assert e422.error == "invalid_match_id"
        assert e422.message == "Match id is invalid."
        with pytest.raises(ValidationError):
            Error422.model_validate({"error": "wrong", "message": "Match id is invalid."})

        # 13. Strict Error500 validates exact contract and rejects invalid values
        e500 = Error500.model_validate(
            {"error": "insufficient_balance", "message": "Insufficient balance"}
        )
        assert e500.error == "insufficient_balance"
        with pytest.raises(ValidationError):
            Error500.model_validate({"error": "wrong", "message": "Insufficient balance"})
