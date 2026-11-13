"""SignalForge: signal generation, processing and measurement. Conventions: docs/conventions.md."""

from .core import Signal
from .measurements import PowerStats, power_stats
from .metrics import ErrorCount, bit_errors
from .modulation import qpsk_demap_hard, qpsk_map
from .units import (
    amp_to_db,
    db_to_amp,
    db_to_lin,
    dbm_to_vrms,
    dbm_to_w,
    lin_to_db,
    vrms_to_dbm,
    w_to_dbm,
)
from .waveforms import prbs, tone

__version__ = "0.1.0"

__all__ = [
    "ErrorCount",
    "PowerStats",
    "Signal",
    "amp_to_db",
    "bit_errors",
    "db_to_amp",
    "db_to_lin",
    "dbm_to_vrms",
    "dbm_to_w",
    "lin_to_db",
    "power_stats",
    "prbs",
    "qpsk_demap_hard",
    "qpsk_map",
    "tone",
    "vrms_to_dbm",
    "w_to_dbm",
]
