from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
from pydantic import ValidationError

from axq.config import load_config
from axq.data.cleaning import clean_candles
from axq.data.synchronization import synchronize_completed_bars
from axq.data.validation import validate_candles
from axq.database import Database
from axq.features import default_registry
from axq.risk import RiskContext, RiskLimits, calculate_volume_lots, veto_reasons
from axq.schemas import ExecutionInstruction, Signal
from axq.versioning import DatasetManifest


def candles(rows: int = 240, frequency: str = "5min") -> pd.DataFrame:
    timestamp = pd.date_range("2026-01-05", periods=rows, freq=frequency, tz="UTC")
    close = 2600 + np.arange(rows, dtype=float) * 0.1
    return pd.DataFrame(
        {
            "timestamp": timestamp,
            "open": close - 0.03,
            "high": close + 0.08,
            "low": close - 0.09,
            "close": close,
            "tick_volume": 100 + np.arange(rows) % 20,
            "spread": 20,
        }
    )


class DataTests(unittest.TestCase):
    def test_clean_and_validate(self) -> None:
        source = pd.concat([candles(5).iloc[::-1], candles(5).iloc[[2]]], ignore_index=True)
        cleaned = clean_candles(source)
        report = validate_candles(cleaned, "M5")
        self.assertTrue(report.valid, report.errors)
        self.assertEqual(len(cleaned), 5)

    def test_validation_rejects_impossible_high(self) -> None:
        frame = candles(3)
        frame.loc[1, "high"] = frame.loc[1, "low"]
        self.assertFalse(validate_candles(frame, "M5").valid)

    def test_higher_timeframe_appears_only_after_close(self) -> None:
        m5 = candles(13)
        h1 = candles(1, "1h")
        synced = synchronize_completed_bars({"M5": m5, "H1": h1})
        self.assertTrue(pd.isna(synced.loc[11, "close_h1"]))
        self.assertEqual(synced.loc[12, "close_h1"], h1.loc[0, "close"])


class FeatureTests(unittest.TestCase):
    def test_registry_is_causal_for_prefix(self) -> None:
        registry = default_registry()
        source = candles()
        groups = [
            "price_action",
            "trend",
            "momentum",
            "volatility",
            "volume",
            "breakout",
            "statistical",
            "session",
            "multi_timeframe",
        ]
        full = registry.compute(source, enabled_groups=groups)
        prefix = registry.compute(source.iloc[:220], enabled_groups=groups)
        pd.testing.assert_frame_equal(full.iloc[:220], prefix)

    def test_group_can_be_disabled(self) -> None:
        result = default_registry().compute(candles(10), enabled_groups=["price_action"])
        self.assertIn("pa_body", result)
        self.assertNotIn("momentum_macd", result)


class ContractAndRiskTests(unittest.TestCase):
    def test_hold_never_becomes_instruction(self) -> None:
        now = datetime.now(UTC)
        with self.assertRaises(ValidationError):
            ExecutionInstruction(
                master_decision_id=uuid4(),
                risk_decision_id=uuid4(),
                symbol="XAUUSD",
                signal=Signal.HOLD,
                created_at=now,
                expires_at=now + timedelta(seconds=10),
                confidence=0.8,
                volume_lots=0.1,
                stop_loss=2500,
                take_profit=2700,
            )

    def test_unhealthy_context_is_vetoed(self) -> None:
        context = RiskContext(10_000, 0, 0, 0, 20, 0.8, 1, False, True)
        self.assertIn("python_unhealthy", veto_reasons(context, RiskLimits()))

    def test_position_size_rounds_down(self) -> None:
        volume = calculate_volume_lots(
            equity=10_000,
            risk_fraction=0.005,
            stop_distance_price=10,
            tick_size=0.01,
            tick_value_loss=1,
            volume_min=0.01,
            volume_max=10,
            volume_step=0.01,
        )
        self.assertEqual(volume, 0.05)


class PersistenceAndConfigTests(unittest.TestCase):
    def test_config_json_compatible_yaml_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text(json.dumps({"symbols": ["XAUUSD"]}), encoding="utf-8")
            self.assertEqual(load_config(path).symbols, ["XAUUSD"])

    def test_database_migrations_are_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "test.sqlite3")
            migrations = Path(__file__).parents[1] / "database" / "migrations"
            database.migrate(migrations)
            database.migrate(migrations)
            connection = database.connect()
            try:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
            finally:
                connection.close()
            self.assertIn("agent_predictions", tables)
            self.assertIn("risk_decisions", tables)

    def test_dataset_identity_ignores_creation_time(self) -> None:
        common = dict(
            dataset_name="tiny",
            symbol="XAUUSD",
            timeframes=["M5"],
            source_files={"raw.csv": "sha256"},
            row_counts={"M5": 10},
            period_start=datetime(2026, 1, 1, tzinfo=UTC),
            period_end=datetime(2026, 1, 2, tzinfo=UTC),
            cleaning_version="1",
            config_hash="abc",
        )
        first = DatasetManifest(**common, created_at=datetime(2026, 2, 1, tzinfo=UTC))
        second = DatasetManifest(**common, created_at=datetime(2026, 3, 1, tzinfo=UTC))
        self.assertEqual(first.dataset_version, second.dataset_version)


if __name__ == "__main__":
    unittest.main()
