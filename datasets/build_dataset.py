from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path
from typing import Any, cast

import pandas as pd
import yaml

from axq.config import load_config
from axq.datasets import DatasetBuildConfig, assemble_dataset, write_dataset


def _run_git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def _git_identity() -> str | None:
    result = _run_git("rev-parse", "HEAD")
    if result.returncode != 0:
        return None
    commit = result.stdout.strip()
    status = _run_git("status", "--porcelain", "--untracked-files=all")
    if status.returncode != 0 or not status.stdout:
        return commit
    digest = hashlib.sha256()
    digest.update(status.stdout.encode())
    difference = subprocess.run(
        ["git", "diff", "--binary", "HEAD"],
        check=False,
        capture_output=True,
    )
    digest.update(difference.stdout)
    for line in sorted(status.stdout.splitlines()):
        if not line.startswith("?? "):
            continue
        path = Path(line[3:])
        if path.is_file():
            digest.update(path.as_posix().encode())
            digest.update(path.read_bytes())
    return f"{commit}-dirty-{digest.hexdigest()[:12]}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build one immutable Phase 3 dataset")
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    payload = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    config = DatasetBuildConfig.model_validate(cast(dict[str, Any], payload))
    frames = {
        timeframe.upper(): pd.read_csv(path)
        for timeframe, path in config.source_files.items()
    }
    feature_config = load_config(config.feature_config)
    result = assemble_dataset(
        frames,
        dataset_name=config.dataset_name,
        symbol=config.symbol,
        base_timeframe=config.base_timeframe,
        feature_set_version=feature_config.features.version,
        feature_groups=feature_config.features.groups,
        feature_parameters=feature_config.features.parameters,
        label_definition=config.label,
        row_policy=config.row_policy,
        split_policy=config.split,
        storage_format=config.storage_format,
        git_commit=_git_identity(),
    )
    path = write_dataset(result, config.output_root)
    print(f"dataset_id={result.manifest.dataset_id}")
    print(f"rows={result.manifest.row_count} features={result.manifest.feature_count}")
    print(f"path={path}")


if __name__ == "__main__":
    main()
