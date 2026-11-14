"""
Data models for the Betting API using Pydantic V2.
Directly aligns with the OpenAPI 3.0.3 specification from /api/docs.
"""

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class SelectionType(str, Enum):
    """Supported bet selection types as defined in OpenAPI schema."""

    HOME = "HOME"
    DRAW = "DRAW"
    AWAY = "AWAY"


class Odds(BaseModel):
    """Odds schema for a match outcome."""

    model_config = ConfigDict(populate_by_name=True)

    home: float
    draw: float
    away: float


class Match(BaseModel):
    """Match schema as defined in OpenAPI components/schemas/Match."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    competition: Optional[str] = None
    home_team: str = Field(alias="homeTeam")
    away_team: str = Field(alias="awayTeam")
    kickoff_date: str = Field(alias="kickoffDate")
    odds: Odds
    status: Optional[str] = None  # UI match status indicator (UPCOMING / PAST)


class Balance(BaseModel):
    """User balance schema as defined in OpenAPI components/schemas/Balance."""

    model_config = ConfigDict(populate_by_name=True)

    balance: float
    currency: str = "EUR"


class PlaceBetRequest(BaseModel):
    """Bet placement request schema as defined in OpenAPI components/schemas/PlaceBetRequest."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    match_id: str = Field(alias="matchId")
    selection: SelectionType
    stake: float = Field(ge=1.0, le=100.0)


class PlaceBetResponse(BaseModel):
    """Bet placement response schema as defined in OpenAPI components/schemas/PlaceBetResponse."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    message: Optional[str] = None
    match_id: Optional[str] = Field(default=None, alias="matchId")
    selection: Optional[str] = None
    stake: Optional[float] = None
    odds: Optional[float] = None
    payout: Optional[float] = None
    balance: Optional[float] = Field(
        default=None, alias="newBalance"
    )  # supports both Swagger 'balance' and API 'newBalance'
    currency: Optional[str] = "EUR"
    error: Optional[str] = None
    success: Optional[bool] = None

    @property
    def new_balance(self) -> Optional[float]:
        """Backward-compatible alias for balance / newBalance."""
        return self.balance


class Error(BaseModel):
    """Semantic validation and server error schema as defined in OpenAPI components/schemas/Error."""

    model_config = ConfigDict(populate_by_name=True)

    error: str
    message: str


class AuthError(BaseModel):
    """Authentication failure schema as defined in OpenAPI components/schemas/AuthError."""

    model_config = ConfigDict(populate_by_name=True)

    error: Literal["missing_user_id", "invalid_user_id"]
