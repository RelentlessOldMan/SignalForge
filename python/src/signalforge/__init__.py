"""SignalForge: signal generation, processing and measurement. Conventions: docs/conventions.md."""

from .core import Signal
from .measurements import PowerStats, power_stats
from .metrics import ErrorCount, bit_errors
from .modulation import qpsk_demap_hard, qpsk_map
from .spectral import (
    OccupiedBandwidth,
    SpectralDensity,
    WindowStats,
    channel_power,
    fft,
    fft_frequencies,
    ifft,
    occupied_bandwidth,
    welch_psd,
    window,
    window_stats,
)
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

__version__ = "2026.11.13.3"  # stamped from VERSION by build.ps1; do not edit

__all__ = [
    "ErrorCount",
    "OccupiedBandwidth",
    "PowerStats",
    "Signal",
    "SpectralDensity",
    "WindowStats",
    "amp_to_db",
    "bit_errors",
    "channel_power",
    "db_to_amp",
    "db_to_lin",
    "dbm_to_vrms",
    "dbm_to_w",
    "fft",
    "fft_frequencies",
    "ifft",
    "lin_to_db",
    "occupied_bandwidth",
    "power_stats",
    "prbs",
    "qpsk_demap_hard",
    "qpsk_map",
    "tone",
    "vrms_to_dbm",
    "w_to_dbm",
    "welch_psd",
    "window",
    "window_stats",
]
