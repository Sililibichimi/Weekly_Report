from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.compute as pc
import pyarrow.dataset as ds

from .cache import CacheManager
from .config import DATASET_PATHS


class FeatureStoreError(RuntimeError):
    pass


class SessionNotFoundError(FeatureStoreError):
    pass


class DuplicateSessionError(FeatureStoreError):
    pass


@dataclass
class FeatureLookupResult:
    dataset: str
    row: dict[str, Any]
    cache_hit: bool


class FeatureStore:
    def __init__(
        self,
        cache_manager: CacheManager,
        feature_columns: list[str],
        meta_columns: list[str] | None = None,
        label_columns: list[str] | None = None,
    ) -> None:
        self.cache_manager = cache_manager
        self.feature_columns = feature_columns
        self.meta_columns = meta_columns or [
            "session_date",
            "visit_start_timestamp",
            "session_year",
            "session_month",
            "has_full_30d_label_window",
        ]
        self.label_columns = label_columns or [
            "future_30d_has_purchase",
            "future_30d_revenue",
        ]
        self.key_columns = ["fullVisitorId", "visit_id"]
        self.columns = self._unique(
            self.key_columns + self.meta_columns + self.feature_columns + self.label_columns
        )

    def lookup(self, visitor_id: str, visit_id: int, dataset: str = "auto") -> FeatureLookupResult:
        dataset = dataset.lower()
        if dataset == "auto":
            for candidate_dataset in ("train", "test"):
                try:
                    return self.lookup(visitor_id, visit_id, candidate_dataset)
                except SessionNotFoundError:
                    continue
            raise SessionNotFoundError(
                f"Session not found in train or test: visitor_id={visitor_id}, visit_id={visit_id}"
            )

        if dataset not in DATASET_PATHS:
            raise FeatureStoreError(f"Unsupported dataset: {dataset}")

        cache_key = (dataset, str(visitor_id), int(visit_id))
        cached = self.cache_manager.feature_cache.get(cache_key)
        if cached is not None:
            return FeatureLookupResult(dataset=dataset, row=cached, cache_hit=True)

        row = self._read_one_row(DATASET_PATHS[dataset], visitor_id, visit_id, dataset)
        self.cache_manager.feature_cache.set(cache_key, row)
        return FeatureLookupResult(dataset=dataset, row=row, cache_hit=False)

    def session_info(self, row: dict[str, Any]) -> dict[str, Any]:
        fields = [
            "session_date",
            "visit_start_timestamp",
            "session_year",
            "session_month",
            "has_full_30d_label_window",
            "visit_number",
            "totals_hits",
            "totals_pageviews",
            "totals_time_on_site",
            "totals_new_visits",
            "is_bounce",
            "session_hour",
            "session_day_of_week",
            "channelGrouping_model",
            "traffic_channel_type_model",
            "device_category_model",
            "geo_country_model",
            "has_gclid",
            "has_traffic_campaign",
            "has_referral_path",
            "is_first_session",
            "has_previous_purchase",
        ]
        return {field: row.get(field) for field in fields if field in row}

    def features(self, row: dict[str, Any]) -> dict[str, Any]:
        return {column: row.get(column) for column in self.feature_columns}

    def ground_truth(self, row: dict[str, Any]) -> dict[str, Any]:
        return {column: row.get(column) for column in self.label_columns if column in row}

    def _read_one_row(
        self, path: Path, visitor_id: str, visit_id: int, dataset_name: str
    ) -> dict[str, Any]:
        if not path.exists():
            raise FeatureStoreError(f"Feature table path does not exist: {path}")

        arrow_dataset = ds.dataset(str(path), format="parquet", partitioning="hive")
        available_columns = set(arrow_dataset.schema.names)
        selected_columns = [column for column in self.columns if column in available_columns]
        missing_columns = sorted(set(self.key_columns + self.feature_columns) - available_columns)
        if missing_columns:
            raise FeatureStoreError(
                f"{dataset_name} feature table missing required columns: {missing_columns}"
            )

        row_filter = (pc.field("fullVisitorId") == str(visitor_id)) & (
            pc.field("visit_id") == int(visit_id)
        )
        table = arrow_dataset.to_table(columns=selected_columns, filter=row_filter)
        if table.num_rows == 0:
            raise SessionNotFoundError(
                f"Session not found in {dataset_name}: visitor_id={visitor_id}, visit_id={visit_id}"
            )
        if table.num_rows > 1:
            raise DuplicateSessionError(
                f"Duplicate session rows in {dataset_name}: visitor_id={visitor_id}, visit_id={visit_id}"
            )

        pdf = table.to_pandas()
        return self._clean_row_dict(pdf.iloc[0].to_dict())

    @staticmethod
    def _clean_row_dict(row: dict[str, Any]) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        for key, value in row.items():
            if pd.isna(value):
                cleaned[key] = None
            elif hasattr(value, "isoformat"):
                cleaned[key] = value.isoformat()
            elif isinstance(value, float) and math.isfinite(value):
                cleaned[key] = float(value)
            elif isinstance(value, (int, str, bool)):
                cleaned[key] = value
            elif hasattr(value, "item"):
                cleaned[key] = value.item()
            else:
                cleaned[key] = value
        return cleaned

    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))
