"""End-to-end link (QPSK, QAM, 8-PSK, FSK, OFDM): bits, shaping, channel, recovery, EVM and BER,
with a JSON report.

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
from .channel import awgn, clock_offset, frequency_offset, multipath, phase_noise
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
    _ofdm_args,
    fsk_demod_noncoherent,
    fsk_modulate,
    ofdm_demodulate,
    ofdm_modulate,
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
    dfe_equalizer,
    dfe_least_squares,
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
    ofdm_nfft: int = 64
    ofdm_cp_len: int = 16
    ofdm_subcarriers: tuple[int, ...] | None = None
    multipath_delays: tuple[int, ...] | None = None
    multipath_gains: tuple[tuple[float, float], ...] | None = None
    equalizer_taps: int | None = None
    equalizer_step: float = 0.1
    equalizer_feedback: int = 0
    equalizer_start: str = "impulse"
    equalizer_loop_gains: tuple[float, float] | None = None
    pilot_interval: int | None = None
    equalizer_forgetting: float | None = None


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
    names = sorted([*_MODULATIONS, *_FSK_ORDERS, "ofdm"])
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
        **_ofdm_fields(config),
        **_multipath_fields(config),
        equalizer_taps=None
        if config.equalizer_taps is None
        else count(config.equalizer_taps, "equalizer_taps"),
        equalizer_step=real(config.equalizer_step, "equalizer_step"),
        equalizer_feedback=count(config.equalizer_feedback, "equalizer_feedback"),
        equalizer_start=config.equalizer_start,
        equalizer_loop_gains=_gains(config.equalizer_loop_gains, "equalizer_loop_gains"),
        pilot_interval=None
        if config.pilot_interval is None
        else count(config.pilot_interval, "pilot_interval"),
        equalizer_forgetting=None
        if config.equalizer_forgetting is None
        else real(config.equalizer_forgetting, "equalizer_forgetting"),
    )
    if c.equalizer_taps is not None and c.equalizer_taps < 1:
        raise ValueError("equalizer_taps must be at least 1")
    if not 0 <= c.equalizer_step <= 2:
        raise ValueError("equalizer_step must be between 0 and 2")
    if c.equalizer_feedback < 0:
        raise ValueError("equalizer_feedback must not be negative")
    if c.equalizer_feedback and c.equalizer_taps is None:
        raise ValueError("equalizer_feedback needs equalizer_taps")
    if c.equalizer_start not in ("impulse", "least_squares"):
        raise ValueError("equalizer_start must be 'impulse' or 'least_squares'")
    if c.equalizer_start != "impulse" and c.equalizer_taps is None:
        raise ValueError("equalizer_start needs equalizer_taps")
    if c.equalizer_loop_gains is not None and c.equalizer_taps is None:
        raise ValueError("equalizer_loop_gains needs equalizer_taps")
    if c.pilot_interval is not None and c.pilot_interval < 1:
        raise ValueError("pilot_interval must be at least 1")
    if c.pilot_interval is not None and c.equalizer_loop_gains is None:
        raise ValueError("pilot_interval needs equalizer_loop_gains")
    if c.equalizer_forgetting is not None and not 0 < c.equalizer_forgetting <= 1:
        raise ValueError("equalizer_forgetting must be in (0, 1]")
    if c.equalizer_forgetting is not None and c.equalizer_taps is None:
        raise ValueError("equalizer_forgetting needs equalizer_taps")
    if (
        c.equalizer_start == "least_squares"
        and c.equalizer_taps is not None
        and c.preamble_symbols < c.equalizer_taps + c.equalizer_feedback
    ):
        raise ValueError(
            "equalizer_start 'least_squares' needs preamble_symbols of at least "
            "equalizer_taps + equalizer_feedback"
        )
    if c.equalizer_taps is not None:
        if c.modulation not in _MODULATIONS:
            raise ValueError("equalizer_taps is for the single-carrier modulations only")
        if sps % 2:
            raise ValueError("the equalizer needs an even samples_per_symbol")
        if pre >= n:
            raise ValueError("the equalizer needs preamble_symbols below num_symbols")
        if c.timing_loop_gains is not None or c.carrier_loop_gains is not None:
            raise ValueError("the equalizer takes no timing_loop_gains or carrier_loop_gains")
    elif c.multipath_delays is not None and c.modulation != "ofdm":
        raise ValueError("multipath_delays and multipath_gains need ofdm or equalizer_taps")
    if c.modulation in _FSK_ORDERS:
        return _fsk_link(c)
    if c.modulation == "ofdm":
        return _ofdm_link(c)
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
    if c.multipath_delays is not None:
        tx = np.concatenate([tx, np.zeros(max(c.multipath_delays), dtype=np.complex128)])
        tx = multipath(tx, list(c.multipath_delays), [complex(*g) for g in c.multipath_gains or ()])
    rx = _channel(c, tx, bps, 1 / sps)
    # receiver
    y = np.asarray(convolve(rx, h), dtype=np.complex128)
    tau = timing_offset(y, sps)
    if c.timing_loop_gains is None:
        z_raw = y[round(tau) % sps :: sps]
    else:
        z_raw = gardner_timing(y, sps, *c.timing_loop_gains, start=tau).symbols
    if c.equalizer_taps is None or pre < 2:
        f_hat = coarse(z_raw, rs)
    else:
        # data-aided: the preamble's symbol-to-symbol phase steps, whose peak over the start does
        # not depend on the frequency (ADR 0071)
        e = np.conj(a[1:pre] * np.conj(a[: pre - 1]))
        d = z_raw[1:] * np.conj(z_raw[:-1])
        dk = [complex(np.sum(e * d[k : k + pre - 1])) for k in range(z_raw.size - n + 1)]
        q1 = dk[int(np.argmax(np.abs(dk)))]
        f_hat = math.atan2(q1.imag, q1.real) * rs / (2 * math.pi)
    f_1 = f_hat
    # frame start: the first maximum of the preamble correlation, its blocks' magnitudes added so
    # a residual frequency error cannot turn a long preamble through a cycle (ADR 0068)
    ref = np.conj(a[:pre])
    zc = frequency_offset(z_raw, -f_hat, rs)
    edges = np.arange(0, pre, blk)
    k0 = int(
        np.argmax(
            [
                float(np.sum(np.abs(np.add.reduceat(ref * zc[k : k + pre], edges))))
                for k in range(zc.size - n + 1)
            ]
        )
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
    if c.equalizer_taps is not None:
        nb = pre // blk
        if nb >= 2:
            # the frequency from the preamble's known symbols: a line through its full blocks'
            # phases, far less hurt by interference than the blind estimators (ADR 0070)
            q = np.add.reduceat(ref[: nb * blk] * zc[k0 : k0 + nb * blk], edges[:nb])
            th = [math.atan2(q[0].imag, q[0].real)]
            for b in range(1, nb):
                t = complex(q[b] * np.conj(q[b - 1]))
                th.append(th[-1] + math.atan2(t.imag, t.real))
            xb = np.arange(nb, dtype=np.float64) * blk
            thb = np.array(th)
            xm, ym = float(np.mean(xb)), float(np.mean(thb))
            s_q = float(np.sum((xb - xm) * (thb - ym)) / np.sum((xb - xm) ** 2))
            f_hat = f_1 + s_q * rs / (2 * math.pi)
        # fractionally spaced at 2 per symbol, its center on the sample the chain takes (ADR 0067)
        v = frequency_offset(y, -f_hat, rs * sps)
        s0 = round(tau) % sps + k0 * sps
        xe = np.zeros(2 * n, dtype=np.complex128)
        tail = v[s0 :: sps // 2][: 2 * n]
        xe[: tail.size] = tail
        start = (
            dfe_least_squares(
                xe, a[:pre], c.equalizer_taps, c.equalizer_feedback, samples_per_symbol=2
            )
            if c.equalizer_start == "least_squares"
            else None
        )
        k_p = c.pilot_interval
        at = None if k_p is None else np.arange(pre + k_p - 1, n, k_p)
        z = dfe_equalizer(
            xe,
            a[:pre],
            c.equalizer_taps,
            c.equalizer_feedback,
            c.equalizer_step,
            samples_per_symbol=2,
            decision=c.modulation,
            initial_taps=None if start is None else start.taps,
            initial_feedback=None if start is None else start.feedback_taps,
            phase_loop_gains=c.equalizer_loop_gains,
            pilots=None if at is None else a[at],
            pilot_interval=k_p,
            forgetting=c.equalizer_forgetting,
        ).symbols
        # the preamble is the equalizer's training and the pilots are known, so neither counts
        keep = np.ones(n, dtype=bool)
        keep[:pre] = False
        if at is not None:
            keep[at] = False
        z, a, bits = z[keep], a[keep], bits.reshape(n, bps)[keep].reshape(-1)
    elif c.carrier_loop_gains is None:
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
        ber_theory=None if eb_n0_db is None else _theory(theory, eb_n0_db, _pulse_energy(c)),
    )


def _theory(theory: Any, eb_n0_db: float, e_h: float) -> float:
    """The chain's theory, at Eb/N0 scaled by the pulse energy ``e_h`` (1/2 if it is 0)."""
    return 0.5 if e_h <= 0 else float(theory(eb_n0_db + 10 * math.log10(e_h)))


def _pulse_energy(c: QpskLinkConfig) -> float:
    """E_h, the energy the multipath paths give one pulse, 1 without multipath: with it the theory
    is the matched-filter bound (conventions: QPSK link, Report)."""
    if c.multipath_delays is None:
        return 1.0
    beta, sps = c.rolloff, c.samples_per_symbol

    def rho(t: float) -> float:  # raised cosine at t symbols
        sinc = 1.0 if t == 0 else math.sin(math.pi * t) / (math.pi * t)
        if beta > 0 and abs(t) == 1 / (2 * beta):
            return (math.pi / 4) * math.sin(math.pi / (2 * beta)) / (math.pi / (2 * beta))
        return sinc * math.cos(math.pi * beta * t) / (1 - (2 * beta * t) ** 2)

    paths = [
        (d, complex(*g)) for d, g in zip(c.multipath_delays, c.multipath_gains or (), strict=True)
    ]
    e = 0.0
    for di, gi in paths:
        for dj, gj in paths:
            e += (gi * gj.conjugate()).real * rho((dj - di) / sps)
    return e


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


def _ofdm_fields(config: QpskLinkConfig) -> dict[str, Any]:
    """The OFDM fields as plain ints, checked for every modulation (conventions: QPSK link)."""
    sc = config.ofdm_subcarriers
    if isinstance(sc, str | bytes) or (isinstance(sc, np.ndarray) and sc.ndim != 1):
        raise ValueError("ofdm_subcarriers must be None or a list of integers")
    if sc is not None and any(isinstance(v, bool | np.bool_) for v in sc):
        raise ValueError("ofdm_subcarriers must be None or a list of integers")
    n, cp, k = _ofdm_args(
        count(config.ofdm_nfft, "ofdm_nfft"), count(config.ofdm_cp_len, "ofdm_cp_len"), sc
    )
    if n < 2:
        raise ValueError("ofdm_nfft must be at least 2")
    if cp < 1:
        raise ValueError("ofdm_cp_len must be at least 1")
    return {
        "ofdm_nfft": n,
        "ofdm_cp_len": cp,
        "ofdm_subcarriers": None if sc is None else tuple(int(v) for v in k),
    }


def _multipath_fields(config: QpskLinkConfig) -> dict[str, Any]:
    """The multipath fields as plain values, checked for every modulation (ADR 0064)."""
    dl, gl = config.multipath_delays, config.multipath_gains
    if dl is None and gl is None:
        return {"multipath_delays": None, "multipath_gains": None}
    what = "multipath_delays and multipath_gains"
    if dl is None or gl is None or isinstance(dl, str | bytes) or isinstance(gl, str | bytes):
        raise ValueError(f"{what} must both be None or lists of equal non-zero length")
    if len(dl) != len(gl) or len(dl) == 0:
        raise ValueError(f"{what} must both be None or lists of equal non-zero length")
    if any(isinstance(v, bool | np.bool_) for v in dl):
        raise ValueError("multipath_delays must be integers")
    delays = tuple(count(v, "multipath_delays") for v in dl)
    gains = []
    for g in gl:
        if isinstance(g, str | bytes) or len(g) != 2:
            raise ValueError("multipath_gains must be pairs [re, im]")
        gains.append((real(g[0], "multipath_gains"), real(g[1], "multipath_gains")))
    return {"multipath_delays": delays, "multipath_gains": tuple(gains)}


def _ofdm_link(c: QpskLinkConfig) -> QpskLinkReport:
    """The OFDM link (conventions: QPSK link, OFDM; ADR 0063, 0064)."""
    n_fft, cp, sps = c.ofdm_nfft, c.ofdm_cp_len, c.samples_per_symbol
    low = -(n_fft // 2)
    k = (
        np.array([v for v in range(low, low + n_fft) if v != 0], dtype=np.int64)
        if c.ofdm_subcarriers is None
        else np.array(c.ofdm_subcarriers, dtype=np.int64)
    )
    u, fs = k.size, c.symbol_rate * sps
    if c.num_symbols % u or c.preamble_symbols % u:
        raise ValueError(f"num_symbols and preamble_symbols must be multiples of {u} (subcarriers)")
    rrc_taps(c.rolloff, sps, c.span_symbols)  # checked as for the other modulations
    if c.carrier_loop_gains is not None:
        raise ValueError("ofdm takes no carrier_loop_gains: the block phase is its carrier loop")
    if not abs(c.frequency_offset_hz) < fs / (2 * n_fft):
        raise ValueError("ofdm needs |frequency_offset_hz| below half a subcarrier spacing")
    spread = 0 if c.multipath_delays is None else max(c.multipath_delays)
    if spread > cp // 2:
        raise ValueError("ofdm needs every multipath delay at most half of ofdm_cp_len")
    b, p = c.num_symbols // u, c.preamble_symbols // u
    if abs(c.clock_offset_ppm) * 1e-6 * (c.delay_samples + b * (n_fft + cp)) > cp // 2 - spread:
        raise ValueError("ofdm needs the clock drift over the frame within half the prefix")
    bits = prbs(c.prbs_order, 2 * c.num_symbols)
    a = qpsk_map(bits)
    frame = ofdm_modulate(a, n_fft, cp, k)
    # room after the frame for every echo and a slow clock
    zeros = np.zeros(c.delay_samples, dtype=np.complex128), np.zeros(cp // 2, dtype=np.complex128)
    tx = np.concatenate([zeros[0], frame, zeros[1]])
    if c.multipath_delays is not None:
        gains = [complex(re, im) for re, im in c.multipath_gains or ()]
        tx = multipath(tx, list(c.multipath_delays), gains)
    rx = np.asarray(_channel(c, tx, 2, 1 / sps), dtype=np.complex128)
    # 1. timing and frequency from the cyclic prefix
    length = frame.size
    idx = (np.arange(b)[:, None] * (n_fft + cp) + np.arange(cp)[None, :]).reshape(-1)
    best, d0, gamma = -math.inf, 0, 0j
    for d in range(rx.size - length + 1):
        r0, r1 = rx[d + idx], rx[d + idx + n_fft]
        g = complex(np.sum(r0 * np.conj(r1)))
        m = abs(g) - float(np.sum(r0.real**2 + r0.imag**2 + r1.real**2 + r1.imag**2)) / 2
        if m > best:
            best, d0, gamma = m, d, g
    f_hat = -math.atan2(gamma.imag, gamma.real) * fs / (2 * math.pi * n_fft)
    # the block: the prefix ties one block early over leading zeros; the preamble decides
    x = np.conj(frame[: p * (n_fft + cp)]) * np.exp(
        -2j * math.pi * f_hat / fs * np.arange(p * (n_fft + cp))
    )
    best, d1 = -1.0, d0
    for d in range(d0 % (n_fft + cp), rx.size - length + 1, n_fft + cp):
        m = abs(complex(np.sum(x * rx[d : d + x.size])))
        if m > best:
            best, d1 = m, d
    d0 = d1
    # 2. back off half a prefix, derotate (phase 0 at d0) and demodulate; 3. channel from the
    # preamble blocks
    d2 = max(d0 - cp // 2, 0)
    shift = d0 - d2
    y = frequency_offset(rx[d2 : d2 + length], -f_hat, fs, 2 * math.pi * f_hat * shift / fs)
    zm = ofdm_demodulate(y, n_fft, cp, k).reshape(b, u)
    am = a.reshape(b, u)
    # each preamble block's common phase turned to block 0's before the average: a residual
    # frequency or phase noise would otherwise smear the estimate
    gp = zm[:p] / am[:p]
    for i in range(1, p):
        t = complex(np.sum(gp[i] * np.conj(gp[0])))
        gp[i] *= complex(t.real, -t.imag) / abs(t) if t != 0 else 1
    h = np.mean(gp, axis=0)
    w = zm / h
    # 4. common phase per block and, with timing_loop_gains, the window offset: on the known
    # symbols through the preamble, then decision-directed
    z = np.empty_like(w)
    theta = tau = v = 0.0
    kc = k - np.mean(k)
    kk = float(np.sum(kc * kc))
    for i in range(b):
        r = w[i] * np.exp(-1j * (theta + 2 * math.pi * k * tau / n_fft))
        e = r * np.conj(am[i] if i < p else qpsk_map(qpsk_demap_hard(r)))
        s = complex(np.sum(e))
        theta += math.atan2(s.imag, s.real)
        if c.timing_loop_gains is not None and kk > 0:
            kp, ki = c.timing_loop_gains
            ph = np.angle(e * np.conj(s))
            err = n_fft / (2 * math.pi) * float(np.sum(kc * ph)) / kk
            v += ki * err
            tau += kp * err + v
        z[i] = w[i] * np.exp(-1j * (theta + 2 * math.pi * k * tau / n_fft))
    hs = complex(np.sum(h * np.exp(2j * math.pi * k * shift / n_fft)))
    zf = z.reshape(-1)
    theory: float | None = None
    if c.eb_n0_db is not None:
        theory = qpsk_ber_theory(c.eb_n0_db)
        if c.multipath_delays is not None:
            hk = np.zeros(u, dtype=np.complex128)
            for dly, (re, im) in zip(c.multipath_delays, c.multipath_gains or (), strict=True):
                hk += complex(re, im) * np.exp(-2j * math.pi * k * dly / n_fft)
            p2 = hk.real**2 + hk.imag**2
            theory = (
                sum(
                    0.5 if v == 0 else qpsk_ber_theory(c.eb_n0_db + 10 * math.log10(v))
                    for v in p2.tolist()
                )
                / u
            )
    return QpskLinkReport(
        config=c,
        timing_offset=float(d0 % sps),
        frame_start=d0 // sps,
        frequency_offset_hz=f_hat,
        phase_offset=_wrap(math.atan2(hs.imag, hs.real)),
        evm=evm(zf, a),
        bit_errors=bit_errors(bits, qpsk_demap_hard(zf)),
        ber_theory=theory,
    )


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
