from __future__ import annotations

from threading import RLock
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from .cache import CacheManager
from .config import (
    FEATURE_CACHE_MAXSIZE,
    FEATURE_CACHE_TTL_SECONDS,
    PREDICTION_CACHE_MAXSIZE,
    PREDICTION_CACHE_TTL_SECONDS,
    REDIS_URL,
    CACHE_BACKEND
)
from .feature_store import (
    DuplicateSessionError,
    FeatureStore,
    FeatureStoreError,
    SessionNotFoundError,
)
from .model_service import ModelService, ModelServiceError
from .registry import ModelRegistry, ModelRegistryError, VersionNotFoundError
from .schemas import (
    ActivateModelRequest,
    LookupResponse,
    ModelInfo,
    ModelVersionsResponse,
    PredictSessionRequest,
    PredictionResponse,
    SessionKey,
    SessionLookupRequest,
)


app = FastAPI(
    title="Future 30D Purchase / Revenue API",
    description="Lookup existing user sessions and serve LightGBM predictions with in-memory cache.",
    version="1.0.0",
)

cache_manager = CacheManager(
    feature_maxsize=FEATURE_CACHE_MAXSIZE,
    feature_ttl_seconds=FEATURE_CACHE_TTL_SECONDS,
    prediction_maxsize=PREDICTION_CACHE_MAXSIZE,
    prediction_ttl_seconds=PREDICTION_CACHE_TTL_SECONDS,
    backend=CACHE_BACKEND,
    redis_url=REDIS_URL,
)
registry = ModelRegistry()
model_service = ModelService()
feature_store: FeatureStore | None = None
# Serializes model hot-swaps so requests never see a half-swapped state.
_swap_lock = RLock()


@app.on_event("startup")
def startup() -> None:
    # First run: create registry.json from the legacy flat model files.
    registry.bootstrap_if_needed()
    _load_version(registry.get_active_version())


def _load_version(version: str) -> None:
    """Load a registry version into a fresh service+store, then swap it in.

    Building the new objects fully *before* swapping means in-flight requests
    keep using the old model until the new one is ready (atomic reference swap).
    """
    global model_service, feature_store

    paths = registry.get_version_paths(version)
    new_service = ModelService(
        classifier_path=paths["classifier"],
        regressor_path=paths["regressor"],
        metadata_path=paths["metadata"],
    )
    new_service.load()
    new_service.registry_version = version
    new_store = FeatureStore(
        cache_manager=cache_manager,
        feature_columns=new_service.feature_columns,
    )

    with _swap_lock:
        model_service = new_service
        feature_store = new_store
        # Predictions from the previous model are no longer valid for reuse.
        cache_manager.prediction_cache.clear()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok" if model_service.is_loaded and feature_store is not None else "not_ready",
        "model_loaded": model_service.is_loaded,
        "metadata_loaded": bool(model_service.metadata),
        "active_model_version": model_service.registry_version,
        "feature_store_ready": feature_store is not None,
        "cache": cache_manager.status(),
    }


@app.get("/model/info", response_model=ModelInfo)
def model_info() -> dict:
    _ensure_ready()
    return model_service.info()


@app.get("/model/versions", response_model=ModelVersionsResponse)
def model_versions() -> dict:
    try:
        return {
            "active_version": registry.get_active_version(),
            "versions": registry.list_versions(),
        }
    except ModelRegistryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/model/activate", response_model=ModelInfo)
def activate_model(request: ActivateModelRequest) -> dict:
    # Validate the version exists before touching anything.
    try:
        registry.get_version_paths(request.version)
    except VersionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        _load_version(request.version)
        registry.set_active(request.version)  # persist only after a successful load
    except (ModelServiceError, ModelRegistryError, OSError) as exc:
        raise HTTPException(status_code=500, detail=f"Failed to activate {request.version}: {exc}") from exc
    return model_service.info()


@app.post("/model/reload", response_model=ModelInfo)
def reload_model() -> dict:
    try:
        _load_version(registry.get_active_version())
    except (ModelServiceError, ModelRegistryError, OSError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return model_service.info()


@app.post("/sessions/lookup", response_model=LookupResponse)
def lookup_session(request: SessionLookupRequest) -> dict:
    _ensure_ready()
    request_id = str(uuid4())
    lookup = _lookup_or_raise(request.visitor_id, request.visit_id, request.dataset)
    row = lookup.row

    return {
        "request_id": request_id,
        "found": True,
        "cache_hit": lookup.cache_hit,
        "dataset": lookup.dataset,
        "session_key": SessionKey(visitor_id=request.visitor_id, visit_id=request.visit_id),
        "session_info": feature_store.session_info(row),
        "features": feature_store.features(row),
        "ground_truth": feature_store.ground_truth(row),
        "warnings": [],
    }


@app.post("/predict/session", response_model=PredictionResponse)
def predict_session(request: PredictSessionRequest) -> dict:
    _ensure_ready()
    request_id = str(uuid4())
    prediction_cache_key = (
        model_service.model_version,
        request.dataset,
        request.visitor_id,
        int(request.visit_id),
        bool(request.include_features),
        bool(request.include_ground_truth),
    )
    cached_response = cache_manager.prediction_cache.get(prediction_cache_key)
    if cached_response is not None:
        cached_response = dict(cached_response)
        cached_response["request_id"] = request_id
        cached_response["cache_hit"] = True
        return cached_response

    lookup = _lookup_or_raise(request.visitor_id, request.visit_id, request.dataset)
    row = lookup.row
    features = feature_store.features(row)

    try:
        prediction, warnings = model_service.predict(features)
    except ModelServiceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    response = {
        "request_id": request_id,
        "cache_hit": False,
        "result_summary": _build_result_summary(request.visitor_id, request.visit_id, prediction),
        "input": {
            "visitor_id": request.visitor_id,
            "visit_id": request.visit_id,
            "session_id": request.visit_id,
            "dataset": request.dataset,
        },
        "matched_session": {
            "dataset": lookup.dataset,
            "visitor_id": request.visitor_id,
            "visit_id": request.visit_id,
            "feature_cache_hit": lookup.cache_hit,
        },
        "model": model_service.info(),
        "session_info": feature_store.session_info(row),
        "features": features if request.include_features else None,
        "prediction": prediction,
        "ground_truth": feature_store.ground_truth(row) if request.include_ground_truth else None,
        "warnings": warnings,
    }
    cache_manager.prediction_cache.set(prediction_cache_key, response)
    return response


@app.get("/cache/status")
def cache_status() -> dict:
    return cache_manager.status()


@app.post("/cache/clear")
def cache_clear() -> dict:
    cache_manager.clear()
    return {"status": "cleared", "cache": cache_manager.status()}


def _ensure_ready() -> None:
    if not model_service.is_loaded:
        raise HTTPException(status_code=503, detail="Model service is not loaded")
    if feature_store is None:
        raise HTTPException(status_code=503, detail="Feature store is not ready")


def _lookup_or_raise(visitor_id: str, visit_id: int, dataset: str):
    try:
        return feature_store.lookup(visitor_id=visitor_id, visit_id=visit_id, dataset=dataset)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DuplicateSessionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except FeatureStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _build_result_summary(visitor_id: str, visit_id: int, prediction: dict) -> dict:
    return {
        "visitor_id": visitor_id,
        "session_id": visit_id,
        "model_version": model_service.model_version,
        "time_update": model_service.model_updated_at_utc or "",
        "xac_suat_mua": prediction.get("purchase_probability_30d"),
        "doanh_thu": prediction.get("expected_revenue_30d"),
    }