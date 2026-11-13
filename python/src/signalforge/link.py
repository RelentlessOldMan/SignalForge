"""End-to-end QPSK link: bits, shaping, channel, recovery, EVM and BER, with a JSON report.

Definitions are in docs/conventions.md (QPSK link) and docs/adr/0009-qpsk-link-report.md.
"""

from __future__ import annotations

import dataclasses
import json
import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from ._checks import count
from .channel import awgn, frequency_offset
from .dsp import convolve, pulse_shape, rrc_taps
from .metrics import ErrorCount, Evm, bit_errors, evm, qpsk_ber_theory
from .modulation import qpsk_demap_hard, qpsk_map
from .sync import qpsk_block_phases, qpsk_frequency_offset, timing_offset
from .waveforms import prbs


@dataclass(frozen=True)
class QpskLinkConfig:
    """One link run. ``eb_n0_db=None`` means no noise; ``phase`` is in radians."""

    num_symbols: int
    eb_n0_db: float | None = None
    symbol_rate: float = 1000.0
    samples_per_symbol: int = 4
    rolloff: float = 0.35
    span_symbols: int = 10
    delay_samples: int = 0
    frequency_offset_hz: float = 0.0
    phase: float = 0.0
    preamble_symbols: int = 32
    phase_block_symbols: int = 32
    prbs_order: int = 15
    seed: int = 0


@dataclass(frozen=True)
class QpskLinkReport:
    """What the receiver estimated and measured. ``ber_theory`` is None without noise."""

    config: QpskLinkConfig
    timing_offset: float
    frame_start: int
    frequency_offset_hz: float
    phase_offset: float
    evm: Evm
    bit_errors: ErrorCount
    ber_theory: float | None

    def to_dict(self) -> dict[str, Any]:
        """Plain dictionary with the JSON field names; non-finite numbers as "inf"/"-inf"/"nan"."""
        d: dict[str, Any] = _encode(dataclasses.asdict(self))
        return d

    def to_json(self) -> str:
        """The report as JSON text (conventions: QPSK link)."""
        return json.dumps(self.to_dict(), indent=2, allow_nan=False)


def _encode(v: Any) -> Any:
    if isinstance(v, dict):
        return {k: _encode(x) for k, x in v.items()}
    if isinstance(v, float) and not math.isfinite(v):
        return "nan" if math.isnan(v) else ("inf" if v > 0 else "-inf")
    return v


def _finite(x: float, what: str) -> float:
    if isinstance(x, bool) or not isinstance(x, int | float) or not math.isfinite(x):
        raise ValueError(f"{what} must be a finite number")
    return float(x)


def _wrap(phi: float) -> float:
    """Into ``(-pi, pi]``."""
    phi = math.remainder(phi, 2 * math.pi)
    return math.pi if phi <= -math.pi else phi


def qpsk_link(config: QpskLinkConfig) -> QpskLinkReport:
    """Run one shaped QPSK link through delay, carrier offset and AWGN, then recover it."""
    c = config
    n = count(c.num_symbols, "num_symbols")
    sps = count(c.samples_per_symbol, "samples_per_symbol")
    span = count(c.span_symbols, "span_symbols")
    delay = count(c.delay_samples, "delay_samples")
    pre = count(c.preamble_symbols, "preamble_symbols")
    blk = count(c.phase_block_symbols, "phase_block_symbols")
    seed = count(c.seed, "seed")
    rs = _finite(c.symbol_rate, "symbol_rate")
    df = _finite(c.frequency_offset_hz, "frequency_offset_hz")
    phase = _finite(c.phase, "phase")
    if n < 2:
        raise ValueError("num_symbols must be at least 2")
    if sps < 2:
        raise ValueError("samples_per_symbol must be at least 2")
    if not 1 <= pre <= n:
        raise ValueError("preamble_symbols must be between 1 and num_symbols")
    if blk < 1:
        raise ValueError("phase_block_symbols must be at least 1")
    if rs <= 0:
        raise ValueError("symbol_rate must be positive")
    eb_n0_db = None if c.eb_n0_db is None else _finite(c.eb_n0_db, "eb_n0_db")

    # transmitter
    bits = prbs(c.prbs_order, 2 * n)
    a = qpsk_map(bits)
    h = rrc_taps(c.rolloff, sps, span)
    tx = np.concatenate([np.zeros(delay, dtype=np.complex128), pulse_shape(a, h, sps)])
    # channel
    rx = frequency_offset(tx, df, rs * sps, phase)
    if eb_n0_db is not None:
        rx = awgn(rx, eb_n0_db + 10 * math.log10(2), sps, seed=seed, signal_power=1 / sps)
    # receiver
    y = np.asarray(convolve(rx, h), dtype=np.complex128)
    tau = timing_offset(y, sps)
    z_raw = y[round(tau) % sps :: sps]
    f_hat = qpsk_frequency_offset(z_raw, rs)
    # frame start: the first maximum of the preamble correlation
    ref = np.conj(a[:pre])
    zc = frequency_offset(z_raw, -f_hat, rs)
    k0 = int(
        np.argmax([abs(complex(np.sum(ref * zc[k : k + pre]))) for k in range(zc.size - n + 1)])
    )
    # fine frequency and phase: a line through the unwrapped block phases at each block's middle
    z = frequency_offset(z_raw[k0 : k0 + n], -f_hat, rs)
    ph = qpsk_block_phases(z, blk)
    starts = np.arange(ph.size) * blk
    x = (starts + np.minimum(starts + blk, n) - 1) / 2
    slope, phi = 0.0, float(ph[0])
    if ph.size > 1:
        xm, ym = float(np.mean(x)), float(np.mean(ph))
        slope = float(np.sum((x - xm) * (ph - ym)) / np.sum((x - xm) ** 2))
        phi = ym - slope * xm
    f_hat += slope * rs / (2 * math.pi)
    # the preamble resolves the pi/2 ambiguity
    c_pre = complex(np.sum(ref * frequency_offset(z[:pre], -slope * rs / (2 * math.pi), rs, -phi)))
    phi = _wrap(phi + (math.pi / 2) * round(math.atan2(c_pre.imag, c_pre.real) / (math.pi / 2)))
    z = frequency_offset(z_raw[k0 : k0 + n], -f_hat, rs, -phi)

    return QpskLinkReport(
        config=c,
        timing_offset=tau,
        frame_start=k0,
        frequency_offset_hz=f_hat,
        phase_offset=phi,
        evm=evm(z, a),
        bit_errors=bit_errors(bits, qpsk_demap_hard(z)),
        ber_theory=None if eb_n0_db is None else qpsk_ber_theory(eb_n0_db),
    )
