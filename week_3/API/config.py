from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEEK_3_DIR = PROJECT_ROOT / "week_3"
DATA_DIR = PROJECT_ROOT / "data_pyspark_parquet"
MODELS_DIR = PROJECT_ROOT / "models"

TRAIN_FEATURE_PATH = DATA_DIR / "train_user_session_features_30d"
TEST_FEATURE_PATH = DATA_DIR / "test_user_session_features_30d"
MODELING_METRICS_PATH = DATA_DIR / "modeling_outputs" / "modeling_metrics.json"
MODELING_MANIFEST_PATH = DATA_DIR / "modeling_outputs" / "modeling_manifest.json"

PURCHASE_CLASSIFIER_PATH = MODELS_DIR / "lgbm_purchase_classifier_30d.pkl"
REVENUE_REGRESSOR_PATH = MODELS_DIR / "lgbm_revenue_regressor_30d.pkl"
PREPROCESSING_METADATA_PATH = MODELS_DIR / "lgbm_modeling_preprocessing_30d.json"

FEATURE_CACHE_MAXSIZE = 10_000
FEATURE_CACHE_TTL_SECONDS = 3_600
PREDICTION_CACHE_MAXSIZE = 10_000
PREDICTION_CACHE_TTL_SECONDS = 3_600

SUPPORTED_DATASETS = {"auto", "train", "test"}
DATASET_PATHS = {
    "train": TRAIN_FEATURE_PATH,
    "test": TEST_FEATURE_PATH,
}

