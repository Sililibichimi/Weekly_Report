from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


DatasetName = Literal["auto", "train", "test"]


class SessionLookupRequest(BaseModel):
    visitor_id: str = Field(..., description="Google Analytics fullVisitorId")
    session_id: int = Field(..., description="Clean numeric visit_id/session id")
    dataset: DatasetName = Field(default="auto", description="Dataset lookup policy")


class PredictSessionRequest(SessionLookupRequest):
    include_features: bool = True
    include_ground_truth: bool = True


class SessionKey(BaseModel):
    visitor_id: str
    session_id: int


class ModelInfo(BaseModel):
    model_name: str
    model_version: str
    model_updated_at_utc: str | None
    feature_set: str
    feature_count: int
    selected_threshold: float
    model_paths: dict[str, str]
    metrics: dict[str, Any]


class LookupResponse(BaseModel):
    request_id: str
    found: bool
    cache_hit: bool
    dataset: str
    session_key: SessionKey
    session_info: dict[str, Any]
    features: dict[str, Any] | None
    ground_truth: dict[str, Any] | None
    warnings: list[str] = []


class PredictionResponse(BaseModel):
    request_id: str
    cache_hit: bool
    input: dict[str, Any]
    matched_session: dict[str, Any]
    model: ModelInfo
    session_info: dict[str, Any]
    features: dict[str, Any] | None
    prediction: dict[str, Any]
    ground_truth: dict[str, Any] | None
    warnings: list[str] = []

