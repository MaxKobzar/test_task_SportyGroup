"""
Data models for the Betting API using Pydantic V2.
Directly aligns with the OpenAPI 3.0.3 specification from /api/docs.
Enforces strict contract validation (extra="forbid") on all response models.
"""

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class SelectionType(str, Enum):
    """Supported bet selection types as defined in OpenAPI components/schemas/Match."""

    HOME = "HOME"
    DRAW = "DRAW"
    AWAY = "AWAY"


OutcomeSelection = SelectionType


class Odds(BaseModel):
    """Odds schema for a match outcome."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    home: float = Field(
        ...,
        gt=1.0,
        description="Decimal odds for home team victory",
    )
    draw: float = Field(
        ...,
        gt=1.0,
        description="Decimal odds for a draw outcome",
    )
    away: float = Field(
        ...,
        gt=1.0,
        description="Decimal odds for away team victory",
    )

    def for_selection(self, selection: str) -> float:
        """Resolve decimal odds dynamically by outcome selection name ('HOME', 'DRAW', 'AWAY')."""
        mapping = {
            "HOME": self.home,
            "DRAW": self.draw,
            "AWAY": self.away,
        }
        key = selection.upper()
        if key not in mapping:
            raise ValueError(
                f"Invalid outcome selection '{selection}'. Expected one of: {list(mapping.keys())}"
            )
        return mapping[key]


class Match(BaseModel):
    """Match schema as defined in OpenAPI components/schemas/Match."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the match fixture",
    )
    competition: str = Field(
        ...,
        min_length=1,
        description="Name of the league or competition",
    )
    home_team: str = Field(
        ...,
        alias="homeTeam",
        min_length=1,
        description="Name of the home team",
    )
    away_team: str = Field(
        ...,
        alias="awayTeam",
        min_length=1,
        description="Name of the away team",
    )
    kickoff_date: date = Field(
        ...,
        alias="kickoffDate",
        description="Kickoff date in ISO format (YYYY-MM-DD)",
    )
    odds: Odds = Field(
        ...,
        description="Decimal odds offered for the three match outcomes (1X2)",
    )


class Balance(BaseModel):
    """User balance schema as defined in OpenAPI components/schemas/Balance."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    balance: float = Field(
        ...,
        ge=0.0,
        description="Available user account balance",
    )
    currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="ISO 4217 three-letter currency code (e.g., EUR)",
    )


class PlaceBetRequest(BaseModel):
    """
    Bet placement request schema as defined in OpenAPI components/schemas/PlaceBetRequest.
    OpenAPI specifies additionalProperties: true (extra fields are ignored by server).
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    match_id: str = Field(
        ...,
        alias="matchId",
        min_length=1,
        description="Target match fixture ID for the wager",
    )
    selection: SelectionType = Field(
        ...,
        description="Bet selection outcome (HOME, DRAW, AWAY)",
    )
    stake: float = Field(
        ...,
        ge=1.0,
        le=100.0,
        description="Wager amount between €1.00 and €100.00",
    )


class PlaceBetResponse(BaseModel):
    """
    Bet placement response schema as defined in OpenAPI components/schemas/PlaceBetResponse.
    Strictly forbids undocumented fields while accepting either 'balance' or 'newBalance'.
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    message: str = Field(
        ...,
        description="Confirmation status message returned by the server",
    )
    match_id: str = Field(
        ...,
        alias="matchId",
        description="Identifier of the match fixture wagered upon",
    )
    selection: str = Field(
        ...,
        description="Selected match outcome string",
    )
    stake: float = Field(
        ...,
        ge=1.0,
        le=100.0,
        description="Wager amount deducted for this bet",
    )
    odds: float = Field(
        ...,
        gt=1.0,
        description="Decimal odds confirmed by the server for this wager",
    )
    payout: float = Field(
        ...,
        gt=0.0,
        description="Calculated potential payout return (stake * odds)",
    )
    balance: float = Field(
        ...,
        validation_alias=AliasChoices("balance", "newBalance"),
        ge=0.0,
        description="User balance immediately following bet placement deduction",
    )
    currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="ISO 4217 three-letter currency code (e.g., EUR)",
    )


class ResetBalanceResponse(BaseModel):
    """Reset balance response schema as defined in OpenAPI /api/reset-balance."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    message: str = Field(
        ...,
        description="Reset operation confirmation message",
    )
    balance: float = Field(
        ...,
        ge=0.0,
        description="Restored user balance value",
    )
    currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="ISO 4217 three-letter currency code (e.g., EUR)",
    )


class Error(BaseModel):
    """Semantic validation and server error schema as defined in OpenAPI components/schemas/Error."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: str = Field(
        ...,
        min_length=1,
        description="Machine-readable error classification code",
    )
    message: str = Field(
        ...,
        min_length=1,
        description="Human-readable explanation of the error",
    )


class AuthError(BaseModel):
    """Authentication failure schema as defined in OpenAPI components/schemas/AuthError."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: Literal["missing_user_id", "invalid_user_id"] = Field(
        ...,
        description="Enumerated authentication error code as defined in OpenAPI",
    )


# ---------------------------------------------------------------------------
# OpenAPI Example Schemas HTTP Error Models
# ---------------------------------------------------------------------------


class Error400(BaseModel):
    """Strict error schema for HTTP 400 Bad Request."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: Literal["invalid_request"] = Field(
        default="invalid_request",
        description="Exact error code for invalid request body",
    )
    message: Literal["Request body must be a JSON object."] = Field(
        default="Request body must be a JSON object.",
        description="Exact error message for non-object JSON body",
    )


class Error401(BaseModel):
    """Strict error schema for HTTP 401 Unauthorized."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: Literal["missing_user_id"] = Field(
        default="missing_user_id",
        description="Exact error code for missing user id header",
    )


class Error405(BaseModel):
    """Strict error schema for HTTP 405 Method Not Allowed."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: Literal["insufficient_balance"] = Field(
        default="insufficient_balance",
        description="Default error code returned in OpenAPI 405 example",
    )
    message: Literal["Insufficient balance"] = Field(
        default="Insufficient balance",
        description="Default error message returned in OpenAPI 405 example",
    )


class Error409(BaseModel):
    """Strict error schema for HTTP 409 Conflict."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: Literal["insufficient_balance"] = Field(
        default="insufficient_balance",
        description="Default error code returned in OpenAPI 409 example",
    )
    message: Literal["Insufficient balance"] = Field(
        default="Insufficient balance",
        description="Default error message returned in OpenAPI 409 example",
    )


class Error422(BaseModel):
    """Strict error schema for HTTP 422 Unprocessable Entity."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: Literal["invalid_match_id"] = Field(
        default="invalid_match_id",
        description="Exact error code for invalid match ID",
    )
    message: Literal["Match id is invalid."] = Field(
        default="Match id is invalid.",
        description="Exact error message for invalid match ID",
    )


class Error500(BaseModel):
    """Strict error schema for HTTP 500 Internal Server Error."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: Literal["insufficient_balance"] = Field(
        default="insufficient_balance",
        description="Default error code returned in OpenAPI 500 example",
    )
    message: Literal["Insufficient balance"] = Field(
        default="Insufficient balance",
        description="Default error message returned in OpenAPI 500 example",
    )
