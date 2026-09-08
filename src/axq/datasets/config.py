from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from axq.labels import LabelDefinition


class RowPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    drop_before_max_warmup: bool = True
    drop_incomplete_labels: bool = True
    critical_feature_columns: list[str] = Field(default_factory=list)
    retain_optional_nans: bool = True


class SplitPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    train_fraction: float = 0.6
    validation_fraction: float = 0.2
    purge_bars: int = Field(default=0, ge=0)
    embargo_bars: int = Field(default=0, ge=0)


class DatasetBuildConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataset_name: str
    symbol: str = "XAUUSD"
    base_timeframe: str = "M5"
    source_files: dict[str, Path]
    feature_config: Path = Path("configs/base.yaml")
    label: LabelDefinition
    row_policy: RowPolicy = Field(default_factory=RowPolicy)
    split: SplitPolicy | None = Field(default_factory=SplitPolicy)
    storage_format: Literal["parquet", "csv_debug"] = "parquet"
    output_root: Path = Path("datasets/generated")
