"""
Data models for the Betting API using Pydantic V2.
"""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BalanceResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    balance: float
    currency: str = "EUR"


class Odds(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    home: float
    draw: float
    away: float


class Match(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    home_team: str = Field(alias="homeTeam")
    away_team: str = Field(alias="awayTeam")
    kickoff_date: str = Field(alias="kickoffDate")
    odds: Odds
    status: Optional[str] = None


class BetPlacementPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    match_id: str = Field(alias="matchId")
    selection: str  # "HOME", "DRAW", "AWAY"
    stake: float


class BetPlacementResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: Optional[str] = None
    new_balance: Optional[float] = Field(default=None, alias="newBalance")
    currency: Optional[str] = None
    payout: Optional[float] = None
    error: Optional[str] = None
    success: Optional[bool] = None
