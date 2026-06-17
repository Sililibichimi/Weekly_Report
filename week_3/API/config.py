from __future__ import annotations

from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEEK_3_DIR = PROJECT_ROOT / "week_3"
DATA_DIR = PROJECT_ROOT / "data_pyspark_parquet"
MODELS_DIR = PROJECT_ROOT / "models"

TRAIN_FEATURE_PATH = DATA_DIR / "train_user_session_features_30d"
TEST_FEATURE_PATH = DATA_DIR / "test_user_session_features_30d"
MODELING_METRICS_PATH = DATA_DIR / "modeling_outputs" / "modeling_metrics.json"
MODELING_MANIFEST_PATH = DATA_DIR / "modeling_outputs" / "modeling_manifest.json"

# Standard filenames inside each versioned model folder (models/<version>/...)
CLASSIFIER_FILENAME = "lgbm_purchase_classifier_30d.pkl"
REGRESSOR_FILENAME = "lgbm_revenue_regressor_30d.pkl"
METADATA_FILENAME = "lgbm_modeling_preprocessing_30d.json"

# Model version registry (models/registry.json) listing all versions + the active one.
REGISTRY_PATH = MODELS_DIR / "registry.json"

# Legacy flat artifact paths. Kept for backward-compat and for bootstrapping the
# registry the first time it runs (no registry.json yet).
PURCHASE_CLASSIFIER_PATH = MODELS_DIR / CLASSIFIER_FILENAME
REVENUE_REGRESSOR_PATH = MODELS_DIR / REGRESSOR_FILENAME
PREPROCESSING_METADATA_PATH = MODELS_DIR / METADATA_FILENAME

FEATURE_CACHE_MAXSIZE = 10_000
FEATURE_CACHE_TTL_SECONDS = 3_600
PREDICTION_CACHE_MAXSIZE = 10_000
PREDICTION_CACHE_TTL_SECONDS = 3_600

# Cache backend: "memory" *mặc định, in-process) hoặc "redis" (Dùng chung giữa các worker)
CACHE_BACKEND = os.getenv("CACHE_BACKEND", "memory").lower()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

SUPPORTED_DATASETS = {"auto", "train", "test"}
DATASET_PATHS = {
    "train": TRAIN_FEATURE_PATH,
    "test": TEST_FEATURE_PATH,
}

