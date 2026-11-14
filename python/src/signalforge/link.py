"""End-to-end link (QPSK, QAM, 8-PSK, FSK): bits, shaping, channel, recovery, EVM and BER, with a
JSON report.

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
from .metrics import (
    ErrorCount,
    Evm,
    bit_errors,
    evm,
    fsk_ber_theory,
    psk8_ber_theory,
    qam16_ber_theory,
    qam64_ber_theory,
    qpsk_ber_theory,
)
from .modulation import (
    fsk_demod_noncoherent,
    fsk_modulate,
    psk8_demap_hard,
    psk8_map,
    qam16_demap_hard,
    qam16_map,
    qam64_demap_hard,
    qam64_map,
    qpsk_demap_hard,
    qpsk_map,
)
from .sync import (
    gardner_timing,
    power_frequency_offset,
    psk8_block_phases,
    psk8_carrier_tracking,
    qam16_carrier_tracking,
    qam64_carrier_tracking,
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
    """What the receiver estimated and measured. ``ber_theory`` is None without noise;
    ``frequency_offset_hz``, ``phase_offset`` and ``evm`` are None for FSK."""

    config: QpskLinkConfig
    timing_offset: float
    frame_start: int
    frequency_offset_hz: float | None
    phase_offset: float | None
    evm: Evm | None
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


def _coarse(power: int) -> Any:
    return lambda r, rs: power_frequency_offset(r, rs, power)


# bits per symbol, mapper, demapper, carrier loop, theory, coarse frequency, block phases,
# phase ambiguity
_MODULATIONS: dict[str, tuple[int, Any, Any, Any, Any, Any, Any, float]] = {
    "qpsk": (
        2,
        qpsk_map,
        qpsk_demap_hard,
        qpsk_carrier_tracking,
        qpsk_ber_theory,
        qpsk_frequency_offset,
        qpsk_block_phases,
        math.pi / 2,
    ),
    "qam16": (
        4,
        qam16_map,
        qam16_demap_hard,
        qam16_carrier_tracking,
        qam16_ber_theory,
        _coarse(4),
        qpsk_block_phases,
        math.pi / 2,
    ),
    "psk8": (
        3,
        psk8_map,
        psk8_demap_hard,
        psk8_carrier_tracking,
        psk8_ber_theory,
        _coarse(8),
        psk8_block_phases,
        math.pi / 4,
    ),
    "qam64": (
        6,
        qam64_map,
        qam64_demap_hard,
        qam64_carrier_tracking,
        qam64_ber_theory,
        _coarse(4),
        qpsk_block_phases,
        math.pi / 2,
    ),
}


_FSK_ORDERS = {"fsk2": 2, "fsk4": 4}


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
    names = sorted([*_MODULATIONS, *_FSK_ORDERS])
    if not isinstance(config.modulation, str) or config.modulation not in names:
        raise ValueError(f"modulation must be one of {names}")
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
    if c.modulation in _FSK_ORDERS:
        return _fsk_link(c)
    bps, mapper, demap, carrier_loop, theory, coarse, block_phases, step = _MODULATIONS[
        c.modulation
    ]
    eb_n0_db = c.eb_n0_db

    # transmitter
    bits = prbs(c.prbs_order, bps * n)
    a = mapper(bits)
    h = rrc_taps(c.rolloff, sps, span)
    tx = np.concatenate([np.zeros(delay, dtype=np.complex128), pulse_shape(a, h, sps)])
    # channel
    rx = _channel(c, tx, bps, 1 / sps)
    # receiver
    y = np.asarray(convolve(rx, h), dtype=np.complex128)
    tau = timing_offset(y, sps)
    if c.timing_loop_gains is None:
        z_raw = y[round(tau) % sps :: sps]
    else:
        z_raw = gardner_timing(y, sps, *c.timing_loop_gains, start=tau).symbols
    f_hat = coarse(z_raw, rs)
    # frame start: the first maximum of the preamble correlation
    ref = np.conj(a[:pre])
    zc = frequency_offset(z_raw, -f_hat, rs)
    k0 = int(
        np.argmax([abs(complex(np.sum(ref * zc[k : k + pre]))) for k in range(zc.size - n + 1)])
    )
    # fine frequency and phase: a line through the unwrapped block phases at each block's middle
    z = frequency_offset(z_raw[k0 : k0 + n], -f_hat, rs)
    ph = block_phases(z, blk)
    starts = np.arange(ph.size) * blk
    x = (starts + np.minimum(starts + blk, n) - 1) / 2
    slope, phi = 0.0, float(ph[0])
    if ph.size > 1:
        xm, ym = float(np.mean(x)), float(np.mean(ph))
        slope = float(np.sum((x - xm) * (ph - ym)) / np.sum((x - xm) ** 2))
        phi = ym - slope * xm
    f_hat += slope * rs / (2 * math.pi)
    # the preamble resolves the pi/2 (8-PSK: pi/4) ambiguity
    c_pre = complex(np.sum(ref * frequency_offset(z[:pre], -slope * rs / (2 * math.pi), rs, -phi)))
    phi = _wrap(phi + step * round(math.atan2(c_pre.imag, c_pre.real) / step))
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


def _channel(c: QpskLinkConfig, tx: Any, bps: int, signal_power: float) -> Any:
    """Carrier offset, phase noise, clock offset and AWGN (conventions: QPSK link, Channel)."""
    fs = c.symbol_rate * c.samples_per_symbol
    rx = frequency_offset(tx, c.frequency_offset_hz, fs, c.phase)
    rng = np.random.default_rng(c.seed)
    if c.phase_noise_linewidth_hz > 0:
        rx = phase_noise(rx, c.phase_noise_linewidth_hz, fs, seed=rng)
    if c.clock_offset_ppm != 0:
        rx = clock_offset(rx, c.clock_offset_ppm)
    if c.eb_n0_db is not None:
        es_n0_db = c.eb_n0_db + 10 * math.log10(bps)
        rx = awgn(rx, es_n0_db, c.samples_per_symbol, seed=rng, signal_power=signal_power)
    return rx


def _fsk_link(c: QpskLinkConfig) -> QpskLinkReport:
    """The FSK link (conventions: QPSK link, FSK; ADR 0057)."""
    m, n, sps, pre = (
        _FSK_ORDERS[c.modulation],
        c.num_symbols,
        c.samples_per_symbol,
        c.preamble_symbols,
    )
    if sps < m:
        raise ValueError(f"{c.modulation} needs samples_per_symbol of at least {m}")
    rrc_taps(c.rolloff, sps, c.span_symbols)  # checked as for the other modulations
    if c.timing_loop_gains is not None or c.carrier_loop_gains is not None:
        raise ValueError(f"{c.modulation} takes no timing_loop_gains or carrier_loop_gains")
    k = 1 if m == 2 else 2
    bits = prbs(c.prbs_order, k * n)
    tx = np.concatenate(
        [np.zeros(c.delay_samples, dtype=np.complex128), fsk_modulate(bits, m, sps, 1)]
    )
    rx = np.asarray(_channel(c, tx, k, 1.0), dtype=np.complex128)
    if rx.size < tx.size + sps:
        rx = np.concatenate([rx, np.zeros(tx.size + sps - rx.size, dtype=np.complex128)])
    psi = np.pi * ((np.arange(-(m - 1), m, 2)[:, None] * np.arange(sps)[None, :]) / sps)
    tones = np.cos(psi) - 1j * np.sin(psi)  # row l is level 2l - (m - 1)

    def energy(x: Any) -> Any:  # E(d, a) of each block of sps samples, one column per level
        corr = x.reshape(-1, sps) @ tones.T
        return corr.real * corr.real + corr.imag * corr.imag

    # timing: the sample phase with the most detector energy over the whole stream
    g = [
        float(np.sum(np.max(energy(rx[t : t + (rx.size - t) // sps * sps]), axis=1)))
        for t in range(sps)
    ]
    tau = int(np.argmax(g))
    # frame: the offset at that phase with the most energy in the preamble's known tones
    labels = bits[: k * pre].reshape(pre, k).astype(np.int64) @ (1 << np.arange(k - 1, -1, -1))
    q = [
        float(np.sum(energy(rx[d : d + pre * sps])[np.arange(pre), labels]))
        for d in range(tau, rx.size - n * sps + 1, sps)
    ]
    d0 = tau + sps * int(np.argmax(q))
    decided = fsk_demod_noncoherent(rx[d0 : d0 + n * sps], m, sps, 1)
    return QpskLinkReport(
        config=c,
        timing_offset=float(d0 % sps),
        frame_start=d0 // sps,
        frequency_offset_hz=None,
        phase_offset=None,
        evm=None,
        bit_errors=bit_errors(bits, decided),
        ber_theory=None if c.eb_n0_db is None else fsk_ber_theory(c.eb_n0_db, m),
    )
