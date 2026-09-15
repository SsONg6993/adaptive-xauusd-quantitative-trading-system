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
from axq.mt5.symbols import (
    BrokerSymbolSelectionMode,
    CanonicalInstrument,
    GoldSymbolConfiguration,
    ResolvedBrokerInstrument,
    resolve_gold_instrument,
)
from axq.mt5.time_normalization import (
    NORMALIZATION_VERSION,
    MT5BrokerEnvironmentIdentity,
    MT5BrokerTimeNormalizer,
    MT5BrokerTimeOffsetResolution,
    MT5BrokerTimePolicy,
    MT5TimeNormalizationError,
    MT5TimestampNormalizationTrace,
    infer_broker_time_offset,
)

__all__ = [
    "MT5ConnectionError",
    "BrokerSymbolSelectionMode",
    "CanonicalInstrument",
    "GoldSymbolConfiguration",
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
    "ResolvedBrokerInstrument",
    "default_mt5_transport_config",
    "resolve_gold_instrument",
    "NORMALIZATION_VERSION",
    "MT5BrokerEnvironmentIdentity",
    "MT5BrokerTimeNormalizer",
    "MT5BrokerTimeOffsetResolution",
    "MT5BrokerTimePolicy",
    "MT5TimeNormalizationError",
    "MT5TimestampNormalizationTrace",
    "infer_broker_time_offset",
]
