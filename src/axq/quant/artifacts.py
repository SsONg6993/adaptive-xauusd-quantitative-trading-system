"""Trusted-local model artifact persistence and integrity verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import joblib  # type: ignore[import-untyped]

from axq.quant.manifest import ModelManifest, load_model_manifest


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dump_artifact(value: Any, path: Path) -> str:
    joblib.dump(value, path, compress=3)
    return file_hash(path)


def load_artifact(path: Path, expected_hash: str) -> Any:
    if not path.is_file():
        raise FileNotFoundError(f"Model artifact is missing: {path}")
    if file_hash(path) != expected_hash:
        raise ValueError(f"Model artifact hash mismatch: {path.name}")
    # joblib uses pickle internally. Load only locally produced, hash-verified artifacts.
    return joblib.load(path)


def verify_run(run_dir: str | Path) -> ModelManifest:
    directory = Path(run_dir)
    manifest = load_model_manifest(directory / "model.manifest.json")
    for name, relative in manifest.artifact_paths.items():
        if name == "manifest":
            continue
        path = directory / relative
        expected = manifest.artifact_hashes.get(name)
        if expected is None or not path.is_file() or file_hash(path) != expected:
            raise ValueError(f"Missing or corrupted artifact: {name}")
    return manifest


def write_json(value: Any, path: Path) -> str:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return file_hash(path)
