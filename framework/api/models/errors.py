from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Error(BaseModel):
    """Semantic validation and server error schema as defined in OpenAPI components/schemas/Error."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: str = Field(
        min_length=1,
        description="Machine-readable error classification code",
    )
    message: str | None = Field(
        default=None,
        min_length=1,
        description="Human-readable explanation of the error (optional)",
    )


class AuthError(BaseModel):
    """Authentication failure schema as defined in OpenAPI components/schemas/AuthError."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    error: Literal["missing_user_id", "invalid_user_id"] = Field(
        description="Enumerated authentication error code as defined in OpenAPI",
    )


class Error400(Error):
    """400 Bad Request."""

    error: Literal["invalid_request"]
    message: Literal["Request body must be a JSON object."] | None = None


class Error401(AuthError):
    """401 Unauthorized."""

    error: Literal["missing_user_id"]


class Error405(Error):
    """405 Method Not Allowed."""

    error: Literal["insufficient_balance"]
    message: Literal["Insufficient balance"] | None = None


class Error409(Error):
    """409 Conflict."""

    error: Literal["insufficient_balance"]
    message: Literal["Insufficient balance"] | None = None


class Error422(Error):
    """422 Unprocessable Entity: one of the documented semantic validation errors."""

    error: Literal[
        "invalid_match_id",
        "invalid_selection",
        "invalid_stake_type",
        "invalid_stake_precision",
        "invalid_stake_min",
        "invalid_stake_max",
        "invalid_match",
    ]
    message: str | None = None


class Error500(Error):
    """500 Internal Server Error."""

    error: Literal["insufficient_balance"]
    message: Literal["Insufficient balance"] | None = None
