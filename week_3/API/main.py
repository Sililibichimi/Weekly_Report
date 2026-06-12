from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, HTTPException

from .cache import CacheManager
from .config import (
    FEATURE_CACHE_MAXSIZE,
    FEATURE_CACHE_TTL_SECONDS,
    PREDICTION_CACHE_MAXSIZE,
    PREDICTION_CACHE_TTL_SECONDS,
)
from .feature_store import (
    DuplicateSessionError,
    FeatureStore,
    FeatureStoreError,
    SessionNotFoundError,
)
from .model_service import ModelService, ModelServiceError
from .schemas import (
    LookupResponse,
    ModelInfo,
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
)
model_service = ModelService()
feature_store: FeatureStore | None = None


@app.on_event("startup")
def startup() -> None:
    global feature_store
    model_service.load()
    feature_store = FeatureStore(
        cache_manager=cache_manager,
        feature_columns=model_service.feature_columns,
    )


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok" if model_service.is_loaded and feature_store is not None else "not_ready",
        "model_loaded": model_service.is_loaded,
        "metadata_loaded": bool(model_service.metadata),
        "feature_store_ready": feature_store is not None,
        "cache": cache_manager.status(),
    }


@app.get("/model/info", response_model=ModelInfo)
def model_info() -> dict:
    _ensure_ready()
    return model_service.info()


@app.post("/sessions/lookup", response_model=LookupResponse)
def lookup_session(request: SessionLookupRequest) -> dict:
    _ensure_ready()
    request_id = str(uuid4())
    lookup = _lookup_or_raise(request.visitor_id, request.session_id, request.dataset)
    row = lookup.row

    return {
        "request_id": request_id,
        "found": True,
        "cache_hit": lookup.cache_hit,
        "dataset": lookup.dataset,
        "session_key": SessionKey(visitor_id=request.visitor_id, session_id=request.session_id),
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
        int(request.session_id),
        bool(request.include_features),
        bool(request.include_ground_truth),
    )
    cached_response = cache_manager.prediction_cache.get(prediction_cache_key)
    if cached_response is not None:
        cached_response = dict(cached_response)
        cached_response["request_id"] = request_id
        cached_response["cache_hit"] = True
        return cached_response

    lookup = _lookup_or_raise(request.visitor_id, request.session_id, request.dataset)
    row = lookup.row
    features = feature_store.features(row)

    try:
        prediction, warnings = model_service.predict(features)
    except ModelServiceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    response = {
        "request_id": request_id,
        "cache_hit": False,
        "input": {
            "visitor_id": request.visitor_id,
            "session_id": request.session_id,
            "dataset": request.dataset,
        },
        "matched_session": {
            "dataset": lookup.dataset,
            "visitor_id": request.visitor_id,
            "session_id": request.session_id,
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


def _lookup_or_raise(visitor_id: str, session_id: int, dataset: str):
    try:
        return feature_store.lookup(visitor_id=visitor_id, session_id=session_id, dataset=dataset)
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DuplicateSessionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except FeatureStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

