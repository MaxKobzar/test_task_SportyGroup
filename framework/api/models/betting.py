"""
Data models for the Betting API using Pydantic V2, aligned with the OpenAPI 3.0.3 spec at /api/docs.

Design rules:
- Money is Decimal end to end (responses are parsed with parse_float=Decimal), never float.
- Models are the source of truth for valid data: field names, types, no undocumented
  fields (extra="forbid") and the domain rules of the Feature Specification (balance never
  negative, stake €1.00-€100.00 with at most 2 decimals, decimal odds above 1, positive payout).
- A response that breaks any rule is a product defect. The client turns the ValidationError
  into ApiContractViolationError, which keeps the raw response as evidence.
- Request and response share the same constrained types, so test data built through
  PlaceBetRequest is valid by construction (see BetMother).
"""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

NonNegativeMoney = Annotated[Decimal, Field(ge=Decimal("0"))]
"""A stored amount: the balance can never go below zero."""

PositiveMoney = Annotated[Decimal, Field(gt=Decimal("0"))]
"""A payout: stake times odds, always above zero."""

Stake = Annotated[Decimal, Field(ge=Decimal("1.00"), le=Decimal("100.00"), decimal_places=2)]
"""Feature Specification stake limits: €1.00-€100.00, cent precision."""

DecimalOdds = Annotated[Decimal, Field(gt=Decimal("1"))]
"""Decimal odds include the returned stake, so they are always above 1."""


class SelectionType(str, Enum):
    """Supported bet selection types as defined in OpenAPI components/schemas/Match."""

    HOME = "HOME"
    DRAW = "DRAW"
    AWAY = "AWAY"


class _ResponseModel(BaseModel):
    """Strict contract: undocumented fields fail validation."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class Odds(_ResponseModel):
    """Decimal odds for the three match outcomes (1X2)."""

    home: DecimalOdds
    draw: DecimalOdds
    away: DecimalOdds

    def for_selection(self, selection: SelectionType) -> Decimal:
        """Odds for one outcome."""
        return {
            SelectionType.HOME: self.home,
            SelectionType.DRAW: self.draw,
            SelectionType.AWAY: self.away,
        }[SelectionType(selection)]


class Match(_ResponseModel):
    """Match schema as defined in OpenAPI components/schemas/Match."""

    id: str = Field(min_length=1)
    competition: str = Field(min_length=1)
    home_team: str = Field(alias="homeTeam")
    away_team: str = Field(alias="awayTeam")
    kickoff_date: date = Field(alias="kickoffDate")
    odds: Odds


class Balance(_ResponseModel):
    """User balance schema as defined in OpenAPI components/schemas/Balance."""

    balance: NonNegativeMoney
    currency: str = Field(min_length=3, max_length=3, description="ISO 4217 code")


class PlaceBetRequest(BaseModel):
    """
    Bet placement request (OpenAPI components/schemas/PlaceBetRequest).
    The spec allows additional properties. Stake limits are the shared Stake type.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    match_id: str = Field(alias="matchId", min_length=1)
    selection: SelectionType
    stake: Stake


class PlaceBetResponse(_ResponseModel):
    """Bet placement response (OpenAPI components/schemas/PlaceBetResponse)."""

    message: str
    match_id: str = Field(alias="matchId")
    selection: SelectionType
    stake: Stake
    odds: DecimalOdds
    payout: PositiveMoney
    balance: NonNegativeMoney = Field(validation_alias=AliasChoices("balance", "newBalance"))
    currency: str = Field(min_length=3, max_length=3)


class ResetBalanceResponse(_ResponseModel):
    """Reset balance response schema as defined in OpenAPI /api/reset-balance."""

    message: str
    balance: NonNegativeMoney
    currency: str = Field(min_length=3, max_length=3)
