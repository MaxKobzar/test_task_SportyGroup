"""
API Test Suite using Python requests.
Validates the backend REST endpoints for balance, matches, and bet placement.
"""
import allure
import pytest
from framework.api.client import BettingApiClient
from framework.api.models import Balance, PlaceBetResponse


@allure.epic("Backend API")
@allure.feature("Betting REST API")
class TestBettingApi:

    @allure.story("API-01: Retrieve User Balance")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_get_balance(self, api_client: BettingApiClient):
        """Verify GET /api/balance returns 200 with valid balance and currency."""
        balance_obj: Balance = api_client.get_balance()
        assert balance_obj.currency == "EUR", f"Expected currency EUR, got {balance_obj.currency}"
        assert balance_obj.balance >= 0, f"Expected non-negative balance, got {balance_obj.balance}"

    @allure.story("API-02: Retrieve Matches Feed")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_matches(self, api_client: BettingApiClient):
        """Verify GET /api/matches returns an active list of matches with complete odds."""
        matches = api_client.get_matches()
        assert len(matches) > 0, "Matches list should not be empty"

        first_match = matches[0]
        assert first_match.id, "Match must possess an ID"
        assert first_match.home_team, "Match must have a home team"
        assert first_match.away_team, "Match must have an away team"
        assert first_match.odds.home > 1.0, f"Home odds must be > 1.0, got {first_match.odds.home}"
        assert first_match.odds.draw > 1.0, f"Draw odds must be > 1.0, got {first_match.odds.draw}"
        assert first_match.odds.away > 1.0, f"Away odds must be > 1.0, got {first_match.odds.away}"

    @allure.story("API-03: Place Bet via API (Happy Path)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_place_bet_happy_path(self, api_client: BettingApiClient):
        """Verify POST /api/place-bet deducts stake from balance and records bet."""
        initial_balance = api_client.get_balance().balance
        matches = api_client.get_matches()
        target_match = matches[0]
        stake = 10.00

        resp = api_client.place_bet(match_id=target_match.id, selection="HOME", stake=stake)
        assert resp.message == "Bet placed successfully" or resp.new_balance is not None, (
            f"Bet placement failed or missing confirmation: {resp}"
        )

        current_balance = api_client.get_balance().balance
        expected_balance = round(initial_balance - stake, 2)
        assert current_balance == expected_balance, (
            f"Balance not deducted correctly: expected {expected_balance}, got {current_balance}"
        )

    @allure.story("API-04: Bet Placement with Nonexistent Match ID")
    @allure.severity(allure.severity_level.NORMAL)
    def test_place_bet_invalid_match_id(self, api_client: BettingApiClient):
        """Verify placing a bet on an invalid match ID returns an error status code."""
        resp = api_client.place_bet_raw(match_id="non-existent-match-9999", selection="HOME", stake=10.00)
        assert resp.status_code in [400, 404, 422], (
            f"Expected 4xx error for invalid match ID, but received {resp.status_code}"
        )

    @allure.story("API-05: Reset User Balance")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_reset_balance(self, api_client: BettingApiClient):
        """Verify POST /api/reset-balance restores the user balance."""
        # First place a bet to alter balance
        matches = api_client.get_matches()
        api_client.place_bet(match_id=matches[0].id, selection="HOME", stake=15.00)

        # Trigger reset
        reset_resp = api_client.reset_balance()
        assert reset_resp.status_code == 200, f"Reset endpoint failed: {reset_resp.status_code}"

        balance_obj = api_client.get_balance()
        assert balance_obj.balance >= 100.0, f"Expected reset balance >= 100, got {balance_obj.balance}"
