"""
Object Mother: BetMother.
Provides canonical test data fixtures and factory archetypes for wagering scenarios.
Follows Martin Fowler's Object Mother pattern and TEA test data architecture standards.
"""

from dataclasses import dataclass
from typing import Any, Dict

from framework.api.models import OutcomeSelection, PlaceBetRequest


@dataclass(frozen=True)
class BetInput:
    """
    Canonical bettor input parameters for UI workflows and client interactions.
    Encapsulates wager intent (selection & stake) without coupling to static fixture IDs.
    """

    selection: str = "HOME"
    stake: float = 10.00

    def to_request(self, match_id: str, **overrides: Any) -> PlaceBetRequest:
        """Convert bettor input into a concrete API PlaceBetRequest for a specific match fixture."""
        payload: Dict[str, Any] = {
            "matchId": match_id,
            "selection": self.selection,
            "stake": self.stake,
            **overrides,
        }
        return PlaceBetRequest.model_validate(payload)


class BetMother:
    """
    Object Mother for generating domain-compliant PlaceBetRequest test payloads and UI bet inputs.
    Eliminates static match assumptions by requiring dynamic match_id resolution from live feeds.
    """

    DEFAULT_STAKE: float = 10.00

    # --------------------------------------------------------------------------
    # API Request Archetypes (require explicit match_id from active catalog feed)
    # --------------------------------------------------------------------------

    @classmethod
    def home_bet(
        cls,
        match_id: str,
        stake: float = DEFAULT_STAKE,
        **overrides: Any,
    ) -> PlaceBetRequest:
        """Create a standard bet on the HOME team for a specific match fixture."""
        return cls._create(match_id=match_id, selection="HOME", stake=stake, **overrides)

    @classmethod
    def draw_bet(
        cls,
        match_id: str,
        stake: float = DEFAULT_STAKE,
        **overrides: Any,
    ) -> PlaceBetRequest:
        """Create a standard bet on a DRAW outcome for a specific match fixture."""
        return cls._create(match_id=match_id, selection="DRAW", stake=stake, **overrides)

    @classmethod
    def away_bet(
        cls,
        match_id: str,
        stake: float = DEFAULT_STAKE,
        **overrides: Any,
    ) -> PlaceBetRequest:
        """Create a standard bet on the AWAY team for a specific match fixture."""
        return cls._create(match_id=match_id, selection="AWAY", stake=stake, **overrides)

    @classmethod
    def for_outcome(
        cls,
        selection: OutcomeSelection | str,
        match_id: str,
        stake: float = DEFAULT_STAKE,
        **overrides: Any,
    ) -> PlaceBetRequest:
        """Create a bet for any parameterized OutcomeSelection ('HOME', 'DRAW', 'AWAY')."""
        return cls._create(match_id=match_id, selection=selection, stake=stake, **overrides)

    @classmethod
    def minimum_stake_bet(
        cls,
        match_id: str,
        selection: OutcomeSelection | str = "HOME",
        **overrides: Any,
    ) -> PlaceBetRequest:
        """Create a boundary bet with the minimum allowed stake (€1.00)."""
        return cls._create(match_id=match_id, selection=selection, stake=1.00, **overrides)

    @classmethod
    def maximum_stake_bet(
        cls,
        match_id: str,
        selection: OutcomeSelection | str = "HOME",
        **overrides: Any,
    ) -> PlaceBetRequest:
        """Create a boundary bet with the maximum allowed stake (€100.00)."""
        return cls._create(match_id=match_id, selection=selection, stake=100.00, **overrides)

    @classmethod
    def sub_minimum_stake_bet(
        cls,
        match_id: str,
        selection: OutcomeSelection | str = "HOME",
        stake: float = 0.50,
        **overrides: Any,
    ) -> PlaceBetRequest:
        """Create an invalid boundary bet below minimum stake (€0.50) for negative testing."""
        data: Dict[str, Any] = {
            "matchId": match_id,
            "selection": selection,
            "stake": stake,
            **overrides,
        }
        return PlaceBetRequest.model_construct(**data)

    @classmethod
    def exceeding_maximum_stake_bet(
        cls,
        match_id: str,
        selection: OutcomeSelection | str = "HOME",
        stake: float = 150.00,
        **overrides: Any,
    ) -> PlaceBetRequest:
        """Create an invalid boundary bet exceeding maximum stake (€150.00) for negative testing."""
        data: Dict[str, Any] = {
            "matchId": match_id,
            "selection": selection,
            "stake": stake,
            **overrides,
        }
        return PlaceBetRequest.model_construct(**data)

    @classmethod
    def _create(
        cls,
        match_id: str,
        selection: Any,
        stake: float,
        **overrides: Any,
    ) -> PlaceBetRequest:
        """Internal builder producing a schema-validated PlaceBetRequest."""
        payload: Dict[str, Any] = {
            "matchId": match_id,
            "selection": selection,
            "stake": stake,
            **overrides,
        }
        return PlaceBetRequest.model_validate(payload)
