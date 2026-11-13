"""SignalForge: signal generation, processing and measurement. Conventions: docs/conventions.md."""

from .channel import awgn, frequency_offset
from .core import Signal
from .dsp import convolve, pulse_shape, rrc_taps, upsample
from .link import QpskLinkConfig, QpskLinkReport, qpsk_link
from .measurements import PowerStats, power_stats
from .metrics import ErrorCount, Evm, bit_errors, evm, qpsk_ber_theory
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
from .sync import qpsk_block_phases, qpsk_frequency_offset, qpsk_phase_offset, timing_offset
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

__version__ = "2026.11.13.11"  # stamped from VERSION by build.ps1; do not edit

__all__ = [
    "ErrorCount",
    "Evm",
    "OccupiedBandwidth",
    "PowerStats",
    "QpskLinkConfig",
    "QpskLinkReport",
    "Signal",
    "SpectralDensity",
    "WindowStats",
    "amp_to_db",
    "awgn",
    "bit_errors",
    "channel_power",
    "convolve",
    "db_to_amp",
    "db_to_lin",
    "dbm_to_vrms",
    "dbm_to_w",
    "evm",
    "fft",
    "fft_frequencies",
    "frequency_offset",
    "ifft",
    "lin_to_db",
    "occupied_bandwidth",
    "power_stats",
    "prbs",
    "pulse_shape",
    "qpsk_ber_theory",
    "qpsk_block_phases",
    "qpsk_demap_hard",
    "qpsk_frequency_offset",
    "qpsk_link",
    "qpsk_map",
    "qpsk_phase_offset",
    "rrc_taps",
    "timing_offset",
    "tone",
    "upsample",
    "vrms_to_dbm",
    "w_to_dbm",
    "welch_psd",
    "window",
    "window_stats",
]
