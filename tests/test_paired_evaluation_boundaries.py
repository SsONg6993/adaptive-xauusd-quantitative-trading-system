from pathlib import Path


def test_comparison_layer_has_no_replay_broker_mt5_or_tuning_imports() -> None:
    root = Path(__file__).parents[1] / "src" / "axq" / "reflection"
    sources = "\n".join(
        (root / name).read_text(encoding="utf-8")
        for name in (
            "paired_evaluation.py",
            "paired_evaluation_contracts.py",
            "paired_evaluation_service.py",
            "paired_evaluation_store.py",
            "paired_evaluation_cli.py",
        )
    )
    forbidden = (
        "MetaTrader5",
        "axq.mt5",
        "run_system_replay",
        "SharedKernelMasterFusionEngineV1",
        "order_send",
        "optuna",
        "promote",
        "deploy",
    )

    assert all(item not in sources for item in forbidden)
