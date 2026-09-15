"""CLI smoke tests for explicit-path dashboard source inspection."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from axq.dashboard.cli import main
from tests.test_dashboard_readers import _reasoning_database


def test_check_reports_real_configured_sources_without_writing(
    tmp_path: Path,
    capsys: object,
) -> None:
    reasoning = tmp_path / "reasoning.sqlite3"
    _reasoning_database(reasoning)
    metrics = tmp_path / "metrics.json"
    metrics.write_text(
        '{"artifact_id":"replay-a","input":{"end":"2026-09-09T00:00:00Z",'
        '"rows":10,"start":"2026-09-08T00:00:00Z"},"trades":{"completed":1}}',
        encoding="utf-8",
    )
    before = sha256(reasoning.read_bytes()).hexdigest()

    assert (
        main(
            [
                "check",
                "--reasoning-db",
                str(reasoning),
                "--metrics-json",
                str(metrics),
            ]
        )
        == 0
    )

    output = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert output["reasoning"]["state"] == "AVAILABLE"
    assert output["reasoning"]["attempt_count"] == 1
    assert output["performance"]["state"] == "AVAILABLE"
    assert output["performance"]["completed_trades"] == 1
    assert output["runtime"]["state"] == "NOT_CONFIGURED"
    assert sha256(reasoning.read_bytes()).hexdigest() == before


def test_check_requires_no_streamlit_import() -> None:
    source = Path("src/axq/dashboard/cli.py").read_text(encoding="utf-8")
    assert "streamlit" not in source
