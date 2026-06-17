from __future__ import annotations

from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


DatasetName = Literal["auto", "train", "test"]


class SessionLookupRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    visitor_id: str = Field(..., description="Google Analytics fullVisitorId")
    visit_id: int = Field(
        ...,
        validation_alias=AliasChoices("visit_id", "session_id"),
        description="Clean numeric visit_id/session_id",
    )
    dataset: DatasetName = Field(default="auto", description="Dataset lookup policy")


class PredictSessionRequest(SessionLookupRequest):
    include_features: bool = True
    include_ground_truth: bool = True


class SessionKey(BaseModel):
    visitor_id: str
    visit_id: int


class ModelInfo(BaseModel):
    model_name: str
    model_version: str
    registry_version: str | None = None
    model_updated_at_utc: str | None
    feature_set: str
    feature_count: int
    selected_threshold: float
    model_paths: dict[str, str]
    metrics: dict[str, Any]


class ActivateModelRequest(BaseModel):
    version: str = Field(..., description="Registry version id to activate")


class ModelVersionSummary(BaseModel):
    version: str
    status: str
    created_at_utc: str | None = None
    registered_at_utc: str | None = None
    feature_set: str | None = None
    feature_count: int | None = None
    selected_threshold: float | None = None
    notes: str | None = None


class ModelVersionsResponse(BaseModel):
    active_version: str
    versions: list[ModelVersionSummary]


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
    result_summary: dict[str, Any]
    input: dict[str, Any]
    matched_session: dict[str, Any]
    model: ModelInfo
    session_info: dict[str, Any]
    features: dict[str, Any] | None
    prediction: dict[str, Any]
    ground_truth: dict[str, Any] | None
    warnings: list[str] = []
