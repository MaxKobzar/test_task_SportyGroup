"""
Object Mother: BetMother.
Named PlaceBetRequest archetypes for wagering scenarios. The match ID is always passed in
(resolved from the live catalog), never hardcoded.

There are exactly two construction paths:
- `for_outcome` validates the request (`model_validate`), so a "valid" bet is guaranteed to
  respect the spec §3 stake bounds before it reaches the server;
- `with_illegal_stake` skips validation (`model_construct`), so a rejection test can send a
  stake the schema would refuse.
Every other archetype delegates to one of them.
"""

from decimal import Decimal

from framework.api.models.betting import PlaceBetRequest, SelectionType


class BetMother:
    """Object Mother for PlaceBetRequest test data."""

    DEFAULT_STAKE = Decimal("10.00")
    MAX_STAKE = Decimal("100.00")  # spec §3: maximum stake per bet

    @classmethod
    def for_outcome(
        cls,
        selection: SelectionType,
        match_id: str,
        stake: Decimal = DEFAULT_STAKE,
    ) -> PlaceBetRequest:
        """Valid bet on any outcome (HOME, DRAW, AWAY), validated against the request schema."""
        return PlaceBetRequest.model_validate(
            {"matchId": match_id, "selection": selection, "stake": stake}
        )

    @classmethod
    def maximum_stake_bet(
        cls, match_id: str, selection: SelectionType = SelectionType.HOME
    ) -> PlaceBetRequest:
        """Valid bet at the maximum allowed stake."""
        return cls.for_outcome(selection, match_id, cls.MAX_STAKE)

    @classmethod
    def with_illegal_stake(
        cls,
        match_id: str,
        stake: Decimal,
        selection: SelectionType = SelectionType.HOME,
    ) -> PlaceBetRequest:
        """
        Bet whose stake breaks a business rule (overdraft, negative, precision, bounds).
        Built without validation; the caller names the stake so the test states the rule.
        """
        return PlaceBetRequest.model_construct(match_id=match_id, selection=selection, stake=stake)
