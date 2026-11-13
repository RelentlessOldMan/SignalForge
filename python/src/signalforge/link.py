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

from ._checks import count, real
from .channel import awgn, clock_offset, frequency_offset, phase_noise
from .dsp import convolve, pulse_shape, rrc_taps
from .metrics import ErrorCount, Evm, bit_errors, evm, qam16_ber_theory, qpsk_ber_theory
from .modulation import qam16_demap_hard, qam16_map, qpsk_demap_hard, qpsk_map
from .sync import (
    gardner_timing,
    power_frequency_offset,
    qam16_carrier_tracking,
    qpsk_block_phases,
    qpsk_carrier_tracking,
    qpsk_frequency_offset,
    timing_offset,
)
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
    modulation: str = "qpsk"
    phase_noise_linewidth_hz: float = 0.0
    clock_offset_ppm: float = 0.0
    timing_loop_gains: tuple[float, float] | None = None
    carrier_loop_gains: tuple[float, float] | None = None


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


def _wrap(phi: float) -> float:
    """Into ``(-pi, pi]``."""
    phi = math.remainder(phi, 2 * math.pi)
    return math.pi if phi <= -math.pi else phi


# bits per symbol, mapper, demapper, carrier loop, theory
_MODULATIONS: dict[str, tuple[int, Any, Any, Any, Any]] = {
    "qpsk": (2, qpsk_map, qpsk_demap_hard, qpsk_carrier_tracking, qpsk_ber_theory),
    "qam16": (4, qam16_map, qam16_demap_hard, qam16_carrier_tracking, qam16_ber_theory),
}


def _gains(g: Any, what: str) -> tuple[float, float] | None:
    """None, or a pair of finite numbers ``>= 0`` as plain floats."""
    if g is None:
        return None
    if isinstance(g, str | bytes) or len(g) != 2:
        raise ValueError(f"{what} must be None or a pair [kp, ki]")
    kp, ki = real(g[0], what), real(g[1], what)
    if kp < 0 or ki < 0:
        raise ValueError(f"{what} must not be negative")
    return (kp, ki)


def qpsk_link(config: QpskLinkConfig) -> QpskLinkReport:
    """Run one shaped QPSK link through delay, carrier offset, phase noise, clock
    offset and AWGN, then
    recover it."""
    n = count(config.num_symbols, "num_symbols")
    sps = count(config.samples_per_symbol, "samples_per_symbol")
    span = count(config.span_symbols, "span_symbols")
    delay = count(config.delay_samples, "delay_samples")
    pre = count(config.preamble_symbols, "preamble_symbols")
    blk = count(config.phase_block_symbols, "phase_block_symbols")
    if n < 2:
        raise ValueError("num_symbols must be at least 2")
    if sps < 2:
        raise ValueError("samples_per_symbol must be at least 2")
    if not 1 <= pre <= n:
        raise ValueError("preamble_symbols must be between 1 and num_symbols")
    if blk < 1:
        raise ValueError("phase_block_symbols must be at least 1")
    rs = real(config.symbol_rate, "symbol_rate")
    if rs <= 0:
        raise ValueError("symbol_rate must be positive")
    if not isinstance(config.modulation, str) or config.modulation not in _MODULATIONS:
        raise ValueError(f"modulation must be one of {sorted(_MODULATIONS)}")
    bps, mapper, demap, carrier_loop, theory = _MODULATIONS[config.modulation]
    lw = real(config.phase_noise_linewidth_hz, "phase_noise_linewidth_hz")
    if lw < 0:
        raise ValueError("phase_noise_linewidth_hz must not be negative")
    ppm = real(config.clock_offset_ppm, "clock_offset_ppm")
    if abs(ppm) > 1e5:
        raise ValueError("clock_offset_ppm must be within 1e5")
    # the report carries the config with plain int and float values, so it always serializes
    c = QpskLinkConfig(
        num_symbols=n,
        eb_n0_db=None if config.eb_n0_db is None else real(config.eb_n0_db, "eb_n0_db"),
        symbol_rate=rs,
        samples_per_symbol=sps,
        rolloff=real(config.rolloff, "rolloff"),
        span_symbols=span,
        delay_samples=delay,
        frequency_offset_hz=real(config.frequency_offset_hz, "frequency_offset_hz"),
        phase=real(config.phase, "phase"),
        preamble_symbols=pre,
        phase_block_symbols=blk,
        prbs_order=count(config.prbs_order, "prbs_order"),
        seed=count(config.seed, "seed"),
        modulation=config.modulation,
        phase_noise_linewidth_hz=lw,
        clock_offset_ppm=ppm,
        timing_loop_gains=_gains(config.timing_loop_gains, "timing_loop_gains"),
        carrier_loop_gains=_gains(config.carrier_loop_gains, "carrier_loop_gains"),
    )
    df, phase, eb_n0_db, seed = c.frequency_offset_hz, c.phase, c.eb_n0_db, c.seed

    # transmitter
    bits = prbs(c.prbs_order, bps * n)
    a = mapper(bits)
    h = rrc_taps(c.rolloff, sps, span)
    tx = np.concatenate([np.zeros(delay, dtype=np.complex128), pulse_shape(a, h, sps)])
    # channel
    rx = frequency_offset(tx, df, rs * sps, phase)
    rng = np.random.default_rng(seed)
    if lw > 0:
        rx = phase_noise(rx, lw, rs * sps, seed=rng)
    if ppm != 0:
        rx = clock_offset(rx, ppm)
    if eb_n0_db is not None:
        rx = awgn(rx, eb_n0_db + 10 * math.log10(bps), sps, seed=rng, signal_power=1 / sps)
    # receiver
    y = np.asarray(convolve(rx, h), dtype=np.complex128)
    tau = timing_offset(y, sps)
    if c.timing_loop_gains is None:
        z_raw = y[round(tau) % sps :: sps]
    else:
        z_raw = gardner_timing(y, sps, *c.timing_loop_gains, start=tau).symbols
    if c.modulation == "qpsk":
        f_hat = qpsk_frequency_offset(z_raw, rs)
    else:
        f_hat = power_frequency_offset(z_raw, rs, 4)
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
    if c.carrier_loop_gains is None:
        z = frequency_offset(z_raw[k0 : k0 + n], -f_hat, rs, -phi)
    else:
        w = frequency_offset(z_raw[k0 : k0 + n], -f_hat, rs)
        c_w = complex(np.sum(ref * w[:pre]))
        phi_p = math.atan2(c_w.imag, c_w.real)
        z = carrier_loop(w, *c.carrier_loop_gains, phase=phi_p).symbols

    return QpskLinkReport(
        config=c,
        timing_offset=tau,
        frame_start=k0,
        frequency_offset_hz=f_hat,
        phase_offset=phi,
        evm=evm(z, a),
        bit_errors=bit_errors(bits, demap(z)),
        ber_theory=None if eb_n0_db is None else theory(eb_n0_db),
    )
