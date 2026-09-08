"""Conservative local device discovery with safe CPU fallback."""

from __future__ import annotations

import importlib.util
from typing import Any

from axq.quant.config import Architecture, Device


def resolve_device(requested: Device, architecture: Architecture) -> dict[str, Any]:
    supports_gpu = architecture in {Architecture.XGBOOST, Architecture.LIGHTGBM}
    cuda_available = False
    gpu_name: str | None = None
    if importlib.util.find_spec("torch") is not None:
        try:
            import torch  # type: ignore[import-not-found]

            cuda_available = bool(torch.cuda.is_available())
            if cuda_available:
                gpu_name = str(torch.cuda.get_device_name(0))
        except (ImportError, RuntimeError):
            cuda_available = False
    selected = "cpu"
    reason = "CPU model or CPU requested"
    if requested in {Device.AUTO, Device.CUDA} and supports_gpu and cuda_available:
        selected = "cuda"
        reason = "CUDA-capable optional model and CUDA runtime detected"
    elif requested is Device.CUDA:
        reason = "CUDA unavailable or unsupported; safely fell back to CPU"
    library_available = importlib.util.find_spec(
        "xgboost" if architecture is Architecture.XGBOOST else "lightgbm"
    ) is not None if supports_gpu else True
    return {
        "requested": requested.value,
        "selected": selected,
        "cuda_available": cuda_available,
        "gpu_name": gpu_name,
        "library_available": library_available,
        "library_gpu_support": "runtime-dependent" if supports_gpu else "not_applicable",
        "reason": reason,
    }
