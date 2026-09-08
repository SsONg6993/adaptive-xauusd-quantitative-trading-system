"""Conservative local CPU, CUDA, and optional-library capability reporting."""

from __future__ import annotations

import importlib
import importlib.util
import os
import platform
import re
import subprocess
import sys
from collections.abc import Callable
from typing import Any


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _nvidia_probe() -> dict[str, Any] | None:
    result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    name, memory, driver = [part.strip() for part in result.stdout.splitlines()[0].split(",")]
    details: dict[str, Any] = {
        "name": name,
        "vram_mib": int(memory),
        "driver_version": driver,
    }
    summary = subprocess.run(
        ["nvidia-smi"], check=False, capture_output=True, text=True
    )
    match = re.search(r"CUDA Version:\s*([0-9.]+)", summary.stdout)
    if match:
        details["cuda_driver_supported_version"] = match.group(1)
    return details


def _xgboost_build_info() -> dict[str, Any]:
    module = importlib.import_module("xgboost")
    build_info = getattr(module, "build_info", None)
    result = build_info() if callable(build_info) else {}
    return dict(result) if isinstance(result, dict) else {}


def _lightgbm_gpu_probe() -> bool:
    """Run one tiny iteration only to verify the installed LightGBM build."""
    module = importlib.import_module("lightgbm")
    classifier = module.LGBMClassifier(
        n_estimators=1,
        num_leaves=2,
        min_data_in_leaf=1,
        verbosity=-1,
        device_type="gpu",
    )
    classifier.fit([[0.0], [1.0], [0.1], [0.9]], [0, 1, 0, 1])
    return True


def _memory_bytes() -> int | None:
    try:
        psutil = importlib.import_module("psutil")
        return int(psutil.virtual_memory().total)
    except (ImportError, AttributeError):
        if platform.system() == "Windows":
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            return _optional_positive_int(result.stdout) if result.returncode == 0 else None
        return None


def _optional_positive_int(value: str) -> int | None:
    try:
        parsed = int(value.strip())
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _physical_cores() -> int | None:
    try:
        psutil = importlib.import_module("psutil")
        value = psutil.cpu_count(logical=False)
        return int(value) if value is not None else None
    except (ImportError, AttributeError):
        if platform.system() == "Windows":
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "(Get-CimInstance Win32_Processor | Measure-Object NumberOfCores -Sum).Sum",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            return _optional_positive_int(result.stdout) if result.returncode == 0 else None
        return None


def compute_report(
    *,
    module_available: Callable[[str], bool] = _module_available,
    nvidia_probe: Callable[[], dict[str, Any] | None] = _nvidia_probe,
    xgboost_build_info: Callable[[], dict[str, Any]] = _xgboost_build_info,
    lightgbm_gpu_probe: Callable[[], bool] = _lightgbm_gpu_probe,
    memory_probe: Callable[[], int | None] = _memory_bytes,
    physical_cores_probe: Callable[[], int | None] = _physical_cores,
) -> dict[str, Any]:
    gpu = nvidia_probe()
    nvidia_detected = gpu is not None
    xgb_installed = module_available("xgboost")
    xgb_info: dict[str, Any] = {}
    if xgb_installed:
        try:
            xgb_info = xgboost_build_info()
        except (ImportError, RuntimeError, OSError):
            xgb_info = {}
    xgb_built_cuda = bool(
        xgb_info.get("USE_CUDA") or xgb_info.get("USE_NCCL")
    )
    lgb_installed = module_available("lightgbm")
    lgb_gpu = False
    lgb_probe_error: str | None = None
    if lgb_installed and nvidia_detected:
        try:
            lgb_gpu = bool(lightgbm_gpu_probe())
        except Exception as exc:  # optional native library errors vary by build
            lgb_probe_error = f"{type(exc).__name__}: {exc}"
    torch_report: dict[str, Any] = {"installed": module_available("torch")}
    if torch_report["installed"]:
        try:
            torch = importlib.import_module("torch")
            torch_report |= {
                "version": str(torch.__version__),
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_version": getattr(torch.version, "cuda", None),
            }
        except (ImportError, RuntimeError) as exc:
            torch_report["error"] = f"{type(exc).__name__}: {exc}"
    xgb_gpu = bool(nvidia_detected and xgb_built_cuda)
    lgb_gpu = bool(nvidia_detected and lgb_gpu)
    return {
        "python": {"version": sys.version.split()[0], "executable": sys.executable},
        "cpu": {
            "model": platform.processor() or platform.machine(),
            "physical_cores": physical_cores_probe(),
            "logical_cores": os.cpu_count(),
            "ram_bytes": memory_probe(),
        },
        "nvidia": {"detected": nvidia_detected, **(gpu or {})},
        "torch": torch_report,
        "xgboost": {
            "installed": xgb_installed,
            "build_info": xgb_info,
            "gpu_capable": xgb_gpu,
        },
        "lightgbm": {
            "installed": lgb_installed,
            "gpu_capable": lgb_gpu,
            "probe_error": lgb_probe_error,
        },
        "recommendations": {
            "logistic_regression": "cpu",
            "random_forest": "cpu",
            "xgboost": "cuda" if xgb_gpu else "cpu",
            "lightgbm": "cuda" if lgb_gpu else "cpu",
        },
    }
