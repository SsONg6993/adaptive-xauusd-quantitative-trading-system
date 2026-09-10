"""Optional, demo-safe MetaTrader5 gateway and adapters."""

from axq.mt5.contracts import (
    MT5ConnectionError,
    MT5Constants,
    MT5Gateway,
    MT5PersistedIntentLink,
    MT5SnapshotError,
    MT5SymbolMapping,
)
from axq.mt5.entry import (
    MT5ExecutionAdapter,
    MT5ExecutionTransport,
    MT5TransportConfig,
    default_mt5_transport_config,
)
from axq.mt5.gateway import MetaTrader5Gateway
from axq.mt5.position import MT5PositionActionAdapter
from axq.mt5.snapshot import MT5BrokerSnapshotProvider

__all__ = [
    "MT5ConnectionError",
    "MT5Constants",
    "MT5Gateway",
    "MT5PersistedIntentLink",
    "MT5PositionActionAdapter",
    "MT5BrokerSnapshotProvider",
    "MT5SnapshotError",
    "MT5SymbolMapping",
    "MT5ExecutionAdapter",
    "MT5ExecutionTransport",
    "MT5TransportConfig",
    "MetaTrader5Gateway",
    "default_mt5_transport_config",
]
