from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from .config import (
    CLASSIFIER_FILENAME,
    METADATA_FILENAME,
    MODELS_DIR,
    PREPROCESSING_METADATA_PATH,
    PURCHASE_CLASSIFIER_PATH,
    REGISTRY_PATH,
    REGRESSOR_FILENAME,
    REVENUE_REGRESSOR_PATH,
)


class ModelRegistryError(RuntimeError):
    pass


class VersionNotFoundError(ModelRegistryError):
    pass


class ModelRegistry:
    """Lightweight file-based model version registry.

    On disk:

        models/
        |-- registry.json              # active_version + per-version metadata
        |-- v20260615T092320/
        |   |-- lgbm_purchase_classifier_30d.pkl
        |   |-- lgbm_revenue_regressor_30d.pkl
        |   `-- lgbm_modeling_preprocessing_30d.json
        `-- ...

    The registry keeps a list of versions and one ``active_version`` pointer.
    Switching the active version is just rewriting that pointer (cheap + atomic).
    """

    def __init__(
        self,
        models_dir: Path = MODELS_DIR,
        registry_path: Path = REGISTRY_PATH,
    ) -> None:
        self.models_dir = models_dir
        self.registry_path = registry_path
        self._lock = RLock()

    # ------------------------------------------------------------------ #
    # low-level read/write
    # ------------------------------------------------------------------ #
    def _read(self) -> dict[str, Any]:
        if not self.registry_path.exists():
            return {"active_version": None, "versions": {}}
        with self.registry_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        data.setdefault("active_version", None)
        data.setdefault("versions", {})
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self.models_dir.mkdir(parents=True, exist_ok=True)
        # Write to a temp file then atomically replace to avoid a corrupt
        # registry if the process dies mid-write.
        tmp_path = self.registry_path.with_suffix(".json.tmp")
        with tmp_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        tmp_path.replace(self.registry_path)

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #
    def bootstrap_if_needed(self) -> str | None:
        """Create the registry from legacy flat model files, if empty.

        Non-destructive: the legacy files in ``models/`` are copied (not moved)
        into a version folder, so existing setups keep working.
        Returns the bootstrapped version id, or None if nothing to do.
        """
        with self._lock:
            data = self._read()
            if data["versions"]:
                return None

            legacy = [
                PURCHASE_CLASSIFIER_PATH,
                REVENUE_REGRESSOR_PATH,
                PREPROCESSING_METADATA_PATH,
            ]
            if not all(path.exists() for path in legacy):
                return None

            metadata = self._read_metadata(PREPROCESSING_METADATA_PATH)
            version = self._version_id_from_metadata(metadata)
            self._register_into(
                data=data,
                version=version,
                classifier_src=PURCHASE_CLASSIFIER_PATH,
                regressor_src=REVENUE_REGRESSOR_PATH,
                metadata_src=PREPROCESSING_METADATA_PATH,
                metadata=metadata,
                make_active=True,
                notes="bootstrapped from legacy flat model files",
            )
            return version

    def register_version(
        self,
        classifier_src: Path,
        regressor_src: Path,
        metadata_src: Path,
        version: str | None = None,
        make_active: bool = False,
        notes: str = "",
    ) -> str:
        """Copy a freshly trained model set into a version folder + record it."""
        with self._lock:
            data = self._read()
            metadata = self._read_metadata(Path(metadata_src))
            version = version or self._version_id_from_metadata(metadata)
            self._register_into(
                data=data,
                version=version,
                classifier_src=Path(classifier_src),
                regressor_src=Path(regressor_src),
                metadata_src=Path(metadata_src),
                metadata=metadata,
                make_active=make_active,
                notes=notes,
            )
            return version

    def list_versions(self) -> list[dict[str, Any]]:
        data = self._read()
        active = data["active_version"]
        versions = []
        for entry in data["versions"].values():
            item = dict(entry)
            item["status"] = "active" if item["version"] == active else "available"
            versions.append(item)
        versions.sort(key=lambda item: item.get("created_at_utc") or "", reverse=True)
        return versions

    def get_active_version(self) -> str:
        active = self._read()["active_version"]
        if not active:
            raise ModelRegistryError("Registry has no active model version")
        return active

    def set_active(self, version: str) -> None:
        with self._lock:
            data = self._read()
            if version not in data["versions"]:
                raise VersionNotFoundError(f"Unknown model version: {version}")
            data["active_version"] = version
            self._write(data)

    def get_version_paths(self, version: str | None = None) -> dict[str, Path]:
        data = self._read()
        version = version or data["active_version"]
        if not version or version not in data["versions"]:
            raise VersionNotFoundError(f"Unknown model version: {version}")
        paths = data["versions"][version]["paths"]
        return {
            "classifier": self.models_dir / paths["purchase_classifier"],
            "regressor": self.models_dir / paths["revenue_regressor"],
            "metadata": self.models_dir / paths["preprocessing_metadata"],
        }

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    def _register_into(
        self,
        data: dict[str, Any],
        version: str,
        classifier_src: Path,
        regressor_src: Path,
        metadata_src: Path,
        metadata: dict[str, Any],
        make_active: bool,
        notes: str,
    ) -> None:
        version_dir = self.models_dir / version
        version_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(classifier_src, version_dir / CLASSIFIER_FILENAME)
        shutil.copy2(regressor_src, version_dir / REGRESSOR_FILENAME)
        shutil.copy2(metadata_src, version_dir / METADATA_FILENAME)

        data["versions"][version] = {
            "version": version,
            "created_at_utc": metadata.get("created_at_utc"),
            "registered_at_utc": datetime.now(timezone.utc).isoformat(),
            "feature_set": metadata.get("feature_set", "unknown"),
            "feature_count": len(metadata.get("feature_columns", [])),
            "selected_threshold": metadata.get("selected_threshold", 0.5),
            "paths": {
                "purchase_classifier": f"{version}/{CLASSIFIER_FILENAME}",
                "revenue_regressor": f"{version}/{REGRESSOR_FILENAME}",
                "preprocessing_metadata": f"{version}/{METADATA_FILENAME}",
            },
            "notes": notes,
        }
        if make_active or data["active_version"] is None:
            data["active_version"] = version
        self._write(data)

    @staticmethod
    def _read_metadata(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def _version_id_from_metadata(metadata: dict[str, Any]) -> str:
        created_at = metadata.get("created_at_utc")
        if not created_at:
            return "v_unknown"
        compact = (
            created_at.replace("-", "")
            .replace(":", "")
            .replace("+0000", "Z")
            .replace("+00:00", "Z")
            .split(".")[0]
        )
        return f"v{compact}"
