"""
Data models for the Betting API using Pydantic V2.
Directly aligns with the OpenAPI 3.0.3 specification from /api/docs.
Enforces strict contract validation (extra="forbid") on all response models.
"""

from enum import Enum
from typing import Literal, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class SelectionType(str, Enum):
    """Supported bet selection types as defined in OpenAPI schema."""

    HOME = "HOME"
    DRAW = "DRAW"
    AWAY = "AWAY"


class Odds(BaseModel):
    """Odds schema for a match outcome."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    home: float
    draw: float
    away: float


class Match(BaseModel):
    """Match schema as defined in OpenAPI components/schemas/Match."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str
    competition: Optional[str] = None
    home_team: str = Field(alias="homeTeam")
    away_team: str = Field(alias="awayTeam")
    kickoff_date: str = Field(alias="kickoffDate")
    odds: Odds
    status: Optional[str] = None  # UI match status indicator (UPCOMING / PAST)


class Balance(BaseModel):
    """User balance schema as defined in OpenAPI components/schemas/Balance."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    balance: float
    currency: str = "EUR"


class PlaceBetRequest(BaseModel):
    """
    Bet placement request schema as defined in OpenAPI components/schemas/PlaceBetRequest.
    OpenAPI specifies additionalProperties: true (extra fields are ignored by server).
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    match_id: str = Field(alias="matchId")
    selection: SelectionType
    stake: float = Field(ge=1.0, le=100.0)


class PlaceBetResponse(BaseModel):
    """
    Bet placement response schema as defined in OpenAPI components/schemas/PlaceBetResponse.
    Strictly forbids undocumented fields while accepting either 'balance' or 'newBalance'.
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    message: str
    match_id: str = Field(alias="matchId")
    selection: str
    stake: float
    odds: float
    payout: float
    balance: float = Field(validation_alias=AliasChoices("balance", "newBalance"))
    currency: str = "EUR"

    @property
    def new_balance(self) -> float:
        """Backward-compatible alias for balance / newBalance."""
        return self.balance


class ResetBalanceResponse(BaseModel):
    """Reset balance response schema as defined in OpenAPI /api/reset-balance."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    message: str
    balance: float
    currency: str = "EUR"


class Error(BaseModel):
    """Semantic validation and server error schema as defined in OpenAPI components/schemas/Error."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: str
    message: str


class AuthError(BaseModel):
    """Authentication failure schema as defined in OpenAPI components/schemas/AuthError."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: Literal["missing_user_id", "invalid_user_id"]


# ---------------------------------------------------------------------------
# Strict HTTP Error Models (OpenAPI Example Schemas)
# ---------------------------------------------------------------------------


class Error400(BaseModel):
    """Strict error schema for HTTP 400 Bad Request."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: Literal["invalid_request"] = "invalid_request"
    message: Literal["Request body must be a JSON object."] = "Request body must be a JSON object."


class Error401(BaseModel):
    """Strict error schema for HTTP 401 Unauthorized."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: Literal["missing_user_id"] = "missing_user_id"


class Error405(BaseModel):
    """Strict error schema for HTTP 405 Method Not Allowed."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: Literal["insufficient_balance"] = "insufficient_balance"
    message: Literal["Insufficient balance"] = "Insufficient balance"


class Error409(BaseModel):
    """Strict error schema for HTTP 409 Conflict."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: Literal["insufficient_balance"] = "insufficient_balance"
    message: Literal["Insufficient balance"] = "Insufficient balance"


class Error422(BaseModel):
    """Strict error schema for HTTP 422 Unprocessable Entity."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: Literal["invalid_match_id"] = "invalid_match_id"
    message: Literal["Match id is invalid."] = "Match id is invalid."


class Error500(BaseModel):
    """Strict error schema for HTTP 500 Internal Server Error."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: Literal["insufficient_balance"] = "insufficient_balance"
    message: Literal["Insufficient balance"] = "Insufficient balance"
