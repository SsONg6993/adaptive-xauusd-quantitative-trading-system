"""Atomic, hash-verified Phase 5 development reports."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_atomic(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    os.replace(temporary, path)
    return file_hash(path)


def write_text_atomic(path: Path, value: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(value, encoding="utf-8")
    os.replace(temporary, path)
    return file_hash(path)


def write_development_manifest(
    run_dir: Path, payload: dict[str, Any], artifact_names: list[str]
) -> dict[str, Any]:
    hashes = {name: file_hash(run_dir / name) for name in artifact_names}
    manifest = payload | {"artifact_hashes": hashes}
    write_json_atomic(run_dir / "development.manifest.json", manifest)
    return manifest


def verify_development_run(run_dir: str | Path) -> dict[str, Any]:
    root = Path(run_dir)
    path = root / "development.manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("artifact_hashes"), dict):
        raise ValueError("Development manifest is invalid")
    for name, expected in payload["artifact_hashes"].items():
        artifact = root / name
        if not artifact.is_file() or file_hash(artifact) != expected:
            raise ValueError(f"Development artifact hash mismatch: {name}")
    return payload
