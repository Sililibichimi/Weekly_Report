from __future__ import annotations

import json
import math
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import (
    MODELING_METRICS_PATH,
    PREPROCESSING_METADATA_PATH,
    PURCHASE_CLASSIFIER_PATH,
    REVENUE_REGRESSOR_PATH,
)


class ModelServiceError(RuntimeError):
    pass


class ModelService:
    def __init__(
        self,
        classifier_path: Path = PURCHASE_CLASSIFIER_PATH,
        regressor_path: Path = REVENUE_REGRESSOR_PATH,
        metadata_path: Path = PREPROCESSING_METADATA_PATH,
        metrics_path: Path = MODELING_METRICS_PATH,
    ) -> None:
        self.classifier_path = classifier_path
        self.regressor_path = regressor_path
        self.metadata_path = metadata_path
        self.metrics_path = metrics_path
        self.classifier: Any | None = None
        self.regressor: Any | None = None
        self.metadata: dict[str, Any] = {}
        self.metrics: dict[str, Any] = {}
        # Registry version id this service was loaded from (set by the caller).
        self.registry_version: str | None = None

    def load(self) -> None:
        self._validate_artifacts_exist()

        with self.classifier_path.open("rb") as file:
            self.classifier = pickle.load(file)
        with self.regressor_path.open("rb") as file:
            self.regressor = pickle.load(file)
        with self.metadata_path.open("r", encoding="utf-8") as file:
            self.metadata = json.load(file)
        if self.metrics_path.exists():
            with self.metrics_path.open("r", encoding="utf-8") as file:
                self.metrics = json.load(file)
        else:
            self.metrics = {}

        if not self.feature_columns:
            raise ModelServiceError("Metadata has empty feature_columns")

    @property
    def is_loaded(self) -> bool:
        return self.classifier is not None and self.regressor is not None and bool(self.metadata)

    @property
    def feature_columns(self) -> list[str]:
        return list(self.metadata.get("feature_columns", []))

    @property
    def categorical_features(self) -> list[str]:
        return list(self.metadata.get("categorical_features", []))

    @property
    def numeric_features(self) -> list[str]:
        return list(self.metadata.get("numeric_features", []))

    @property
    def binary_features(self) -> list[str]:
        return list(self.metadata.get("binary_features", []))

    @property
    def category_levels(self) -> dict[str, list[str]]:
        return dict(self.metadata.get("category_levels_fit_from_train_split", {}))

    @property
    def selected_threshold(self) -> float:
        return float(self.metadata.get("selected_threshold", 0.5))

    @property
    def model_updated_at_utc(self) -> str | None:
        return self.metadata.get("created_at_utc")

    @property
    def model_version(self) -> str:
        created_at = self.model_updated_at_utc or "unknown"
        if created_at == "unknown":
            return "lgbm_30d_unknown"
        compact = (
            created_at.replace("-", "")
            .replace(":", "")
            .replace("+0000", "Z")
            .replace("+00:00", "Z")
            .split(".")[0]
        )
        return f"lgbm_30d_{compact}"

    def info(self) -> dict[str, Any]:
        return {
            "model_name": "lgbm_future_30d_purchase_revenue",
            "model_version": self.model_version,
            "registry_version": self.registry_version,
            "model_updated_at_utc": self.model_updated_at_utc,
            "feature_set": self.metadata.get("feature_set", "unknown"),
            "feature_count": len(self.feature_columns),
            "selected_threshold": self.selected_threshold,
            "model_paths": {
                "purchase_classifier": str(self.classifier_path),
                "revenue_regressor": str(self.regressor_path),
                "preprocessing_metadata": str(self.metadata_path),
            },
            "metrics": self._metrics_summary(),
        }

    def predict(self, feature_values: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        if not self.is_loaded:
            raise ModelServiceError("ModelService is not loaded")

        warnings: list[str] = []
        model_input = self._build_model_input(feature_values, warnings)

        purchase_probability = float(self.classifier.predict_proba(model_input)[0, 1])
        predicted_purchase = purchase_probability >= self.selected_threshold
        predicted_log_revenue = float(self.regressor.predict(model_input)[0])
        predicted_revenue = float(np.expm1(predicted_log_revenue))

        if not math.isfinite(predicted_revenue):
            warnings.append("Revenue regressor returned non-finite value; set to 0.0")
            predicted_revenue = 0.0
        elif predicted_revenue < 0:
            warnings.append("Revenue regressor returned negative expm1 value; clipped to 0.0")
            predicted_revenue = 0.0

        expected_revenue = purchase_probability * predicted_revenue
        return (
            {
                "purchase_probability_30d": purchase_probability,
                "selected_threshold": self.selected_threshold,
                "predicted_purchase_30d": bool(predicted_purchase),
                "predicted_log_revenue_if_purchase_30d": predicted_log_revenue,
                "predicted_revenue_if_purchase_30d": predicted_revenue,
                "expected_revenue_30d": expected_revenue,
                "prediction_generated_at_utc": datetime.now(timezone.utc).isoformat(),
            },
            warnings,
        )

    def _build_model_input(
        self, feature_values: dict[str, Any], warnings: list[str]
    ) -> pd.DataFrame:
        missing = [column for column in self.feature_columns if column not in feature_values]
        if missing:
            raise ModelServiceError(f"Missing required feature values: {missing}")

        row = {column: feature_values[column] for column in self.feature_columns}
        pdf = pd.DataFrame([row], columns=self.feature_columns)

        for column in self.numeric_features + self.binary_features:
            pdf[column] = pd.to_numeric(pdf[column], errors="coerce").fillna(0)

        for column in self.categorical_features:
            levels = self.category_levels.get(column, [])
            value = pdf.at[0, column]
            if value is None or pd.isna(value):
                value = "unknown" if "unknown" in levels else (levels[0] if levels else "unknown")
                warnings.append(f"{column} was missing; filled with {value}")
            elif levels and value not in levels:
                fallback = "other" if "other" in levels else "unknown" if "unknown" in levels else levels[0]
                warnings.append(f"{column}={value} not in train categories; mapped to {fallback}")
                value = fallback
            pdf[column] = pd.Categorical([value], categories=levels if levels else None)

        return pdf[self.feature_columns]

    def _metrics_summary(self) -> dict[str, Any]:
        if not self.metrics:
            return {
                "validation": self.metadata.get("classification_metrics_validation", {}),
                "regression_validation": self.metadata.get(
                    "regression_metrics_validation_positive_rows", {}
                ),
            }

        validation = self.metrics.get("validation", {})
        test = self.metrics.get("test", {})
        return {
            "classification_training_summary": self.metrics.get(
                "classification_training_summary", {}
            ),
            "validation": {
                "classification": validation.get("classification", {}),
                "expected_revenue": validation.get("expected_revenue", {}),
            },
            "test": {
                "classification": test.get("classification", {}),
                "expected_revenue": test.get("expected_revenue", {}),
            },
        }

    def _validate_artifacts_exist(self) -> None:
        required_paths = [
            self.classifier_path,
            self.regressor_path,
            self.metadata_path,
        ]
        missing_paths = [str(path) for path in required_paths if not path.exists()]
        if missing_paths:
            raise ModelServiceError(f"Missing model artifacts: {missing_paths}")

