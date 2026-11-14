"""Symbol mapping, FSK and OFDM. Definitions in docs/conventions.md."""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray

from ._checks import count, real

_INV_SQRT2 = 1.0 / np.sqrt(2.0)
_INV_SQRT10 = 1.0 / math.sqrt(10.0)
_QAM16_THRESHOLD = 2.0 / math.sqrt(10.0)
_INV_SQRT42 = 1.0 / math.sqrt(42.0)
_QAM64_T2 = 2.0 / math.sqrt(42.0)
_QAM64_T4 = 4.0 / math.sqrt(42.0)
_QAM64_T6 = 6.0 / math.sqrt(42.0)


def _bits(bits: ArrayLike) -> NDArray[np.uint8]:
    b = np.asarray(bits)
    if b.ndim != 1:
        raise ValueError("bits must be one-dimensional")
    if b.size and not np.all((b == 0) | (b == 1)):
        raise ValueError("bits must be 0 or 1")
    return b.astype(np.uint8)


def qpsk_map(bits: ArrayLike) -> NDArray[np.complex128]:
    """Gray-coded QPSK: bit pair ``(b0, b1)`` to ``((1-2*b0) + j*(1-2*b1)) / sqrt(2)``."""
    b = _bits(bits)
    if b.size % 2:
        raise ValueError("QPSK needs an even number of bits")
    i = 1.0 - 2.0 * b[0::2]
    q = 1.0 - 2.0 * b[1::2]
    symbols: NDArray[np.complex128] = (i + 1j * q) * _INV_SQRT2
    return symbols


def qpsk_demap_hard(symbols: ArrayLike) -> NDArray[np.uint8]:
    """Hard-decision QPSK demapping: bit is 1 where I (or Q) is negative; exactly 0 gives bit 0."""
    s = np.asarray(symbols, dtype=np.complex128)
    if s.ndim != 1:
        raise ValueError("symbols must be one-dimensional")
    out = np.empty(2 * s.size, dtype=np.uint8)
    out[0::2] = s.real < 0
    out[1::2] = s.imag < 0
    return out


def _groups(bits: ArrayLike, k: int, name: str) -> NDArray[np.int64]:
    b = _bits(bits)
    if b.size % k:
        raise ValueError(f"{name} needs a multiple of {k} bits")
    groups = b.reshape(-1, k).astype(np.int64)
    return groups


def _bits_of(labels: NDArray[np.int64], k: int) -> NDArray[np.uint8]:
    shifts = np.arange(k - 1, -1, -1)
    return ((labels[:, None] >> shifts) & 1).astype(np.uint8).reshape(-1)


def psk8_map(bits: ArrayLike) -> NDArray[np.complex128]:
    """Gray-coded 8-PSK: label ``m`` (3 bits, MSB first) to ``exp(j*pi*p/4)`` where
    ``p ^ (p >> 1) == m`` (conventions: Bits and symbols)."""
    g = _groups(bits, 3, "8-PSK")
    m = 4 * g[:, 0] + 2 * g[:, 1] + g[:, 2]
    p = m ^ (m >> 1) ^ (m >> 2)
    symbols = np.asarray(np.exp(1j * (np.pi / 4) * p), dtype=np.complex128)
    return symbols


def psk8_demap_hard(symbols: ArrayLike) -> NDArray[np.uint8]:
    """Hard-decision 8-PSK: the nearest point's label; 0 decides ``000``."""
    s = np.asarray(symbols, dtype=np.complex128)
    if s.ndim != 1:
        raise ValueError("symbols must be one-dimensional")
    if np.isnan(s).any():
        raise ValueError("symbols must not be NaN")
    p = np.mod(np.floor(np.arctan2(s.imag, s.real) / (np.pi / 4) + 0.5), 8).astype(np.int64)
    return _bits_of(p ^ (p >> 1), 3)


def qam16_map(bits: ArrayLike) -> NDArray[np.complex128]:
    """Gray-coded 16-QAM: ``I`` from ``(b0, b1)``, ``Q`` from ``(b2, b3)``, each
    ``(1 - 2*first)*(3 - 2*second)``, over ``sqrt(10)`` (conventions: Bits and symbols)."""
    g = _groups(bits, 4, "16-QAM").astype(np.float64)
    i = (1 - 2 * g[:, 0]) * (3 - 2 * g[:, 1])
    q = (1 - 2 * g[:, 2]) * (3 - 2 * g[:, 3])
    symbols = np.asarray((i + 1j * q) * _INV_SQRT10, dtype=np.complex128)
    return symbols


def qam16_demap_hard(symbols: ArrayLike) -> NDArray[np.uint8]:
    """Hard-decision 16-QAM: per component, first bit ``v < 0``, second ``|v| < 2/sqrt(10)``."""
    s = np.asarray(symbols, dtype=np.complex128)
    if s.ndim != 1:
        raise ValueError("symbols must be one-dimensional")
    if np.isnan(s).any():
        raise ValueError("symbols must not be NaN")
    out = np.empty(4 * s.size, dtype=np.uint8)
    out[0::4] = s.real < 0
    out[1::4] = np.abs(s.real) < _QAM16_THRESHOLD
    out[2::4] = s.imag < 0
    out[3::4] = np.abs(s.imag) < _QAM16_THRESHOLD
    return out


def qam64_map(bits: ArrayLike) -> NDArray[np.complex128]:
    """Gray-coded 64-QAM: ``I`` from ``(b0, b1, b2)``, ``Q`` from ``(b3, b4, b5)``, each
    ``(1 - 2*a)*(4 + (1 - 2*b)*(3 - 2*c))``, over ``sqrt(42)`` (conventions: Bits and symbols)."""
    g = _groups(bits, 6, "64-QAM").astype(np.float64)
    i = (1 - 2 * g[:, 0]) * (4 + (1 - 2 * g[:, 1]) * (3 - 2 * g[:, 2]))
    q = (1 - 2 * g[:, 3]) * (4 + (1 - 2 * g[:, 4]) * (3 - 2 * g[:, 5]))
    return np.asarray((i + 1j * q) * _INV_SQRT42, dtype=np.complex128)


def qam64_demap_hard(symbols: ArrayLike) -> NDArray[np.uint8]:
    """Hard-decision 64-QAM: per component ``v`` with ``a = |v|``, bits ``v < 0``,
    ``a < 4/sqrt(42)`` and ``2/sqrt(42) < a < 6/sqrt(42)``."""
    s = np.asarray(symbols, dtype=np.complex128)
    if s.ndim != 1:
        raise ValueError("symbols must be one-dimensional")
    if np.isnan(s).any():
        raise ValueError("symbols must not be NaN")
    out = np.empty(6 * s.size, dtype=np.uint8)
    for j, v in enumerate((s.real, s.imag)):
        a = np.abs(v)
        out[3 * j :: 6] = v < 0
        out[3 * j + 1 :: 6] = a < _QAM64_T4
        out[3 * j + 2 :: 6] = (a > _QAM64_T2) & (a < _QAM64_T6)
    return out


def _label_bits(k: int) -> NDArray[np.uint8]:
    m = np.arange(1 << k)
    return ((m[:, None] >> np.arange(k - 1, -1, -1)) & 1).astype(np.uint8).reshape(-1)


def _demap_llr(
    symbols: ArrayLike, noise_variance: float, points: NDArray[np.complex128], k: int
) -> NDArray[np.float64]:
    s = np.asarray(symbols, dtype=np.complex128)
    if s.ndim != 1:
        raise ValueError("symbols must be one-dimensional")
    if not np.isfinite(s).all():
        raise ValueError("symbols must be finite")
    nv = real(noise_variance, "noise_variance")
    if not nv > 0:
        raise ValueError("noise_variance must be positive and finite")
    dr = s.real[:, None] - points.real[None, :]
    di = s.imag[:, None] - points.imag[None, :]
    d2 = dr * dr + di * di
    labels = np.arange(points.size)
    out = np.empty((s.size, k))
    for i in range(k):
        one = ((labels >> (k - 1 - i)) & 1) == 1
        if s.size:
            out[:, i] = (d2[:, one].min(axis=1) - d2[:, ~one].min(axis=1)) / nv
    return out.reshape(-1)


_QPSK_POINTS = qpsk_map(_label_bits(2))
_PSK8_POINTS = psk8_map(_label_bits(3))
_QAM16_POINTS = qam16_map(_label_bits(4))
_QAM64_POINTS = qam64_map(_label_bits(6))


def qpsk_demap_llr(symbols: ArrayLike, noise_variance: float) -> NDArray[np.float64]:
    """Max-log LLRs of QPSK, positive for bit 0 (conventions: Bits and symbols, Soft demapping)."""
    return _demap_llr(symbols, noise_variance, _QPSK_POINTS, 2)


def psk8_demap_llr(symbols: ArrayLike, noise_variance: float) -> NDArray[np.float64]:
    """Max-log LLRs of 8-PSK, positive for bit 0 (conventions: Bits and symbols, Soft demapping)."""
    return _demap_llr(symbols, noise_variance, _PSK8_POINTS, 3)


def qam16_demap_llr(symbols: ArrayLike, noise_variance: float) -> NDArray[np.float64]:
    """Max-log LLRs of 16-QAM, positive for bit 0 (conventions: Bits and symbols, Soft
    demapping)."""
    return _demap_llr(symbols, noise_variance, _QAM16_POINTS, 4)


def qam64_demap_llr(symbols: ArrayLike, noise_variance: float) -> NDArray[np.float64]:
    """Max-log LLRs of 64-QAM, positive for bit 0 (conventions: Bits and symbols, Soft
    demapping)."""
    return _demap_llr(symbols, noise_variance, _QAM64_POINTS, 6)


_FSK_ORDERS = {2: 1, 4: 2, 8: 3, 16: 4}


def _fsk_args(
    order: int, samples_per_symbol: int, modulation_index: float
) -> tuple[int, int, float]:
    if count(order, "order") not in _FSK_ORDERS:
        raise ValueError("order must be 2, 4, 8 or 16")
    sps = count(samples_per_symbol, "samples_per_symbol")
    if sps < 1:
        raise ValueError("samples_per_symbol must be at least 1")
    h = real(modulation_index, "modulation_index")
    if h <= 0:
        raise ValueError("modulation_index must be positive")
    return _FSK_ORDERS[int(order)], sps, h


def fsk_modulate(
    bits: ArrayLike, order: int, samples_per_symbol: int, modulation_index: float
) -> NDArray[np.complex128]:
    """Continuous-phase M-FSK, natural binary labels, tone levels ``2m - (M - 1)`` at ``a*h/2``
    cycles per symbol (conventions: Bits and symbols, FSK; ADR 0054)."""
    k, sps, h = _fsk_args(order, samples_per_symbol, modulation_index)
    g = _groups(bits, k, f"{order}-FSK")
    m = g @ (1 << np.arange(k - 1, -1, -1))
    a = 2 * m - (int(order) - 1)
    start = np.concatenate(([0], np.cumsum(a)[:-1])) if a.size else a
    n = np.arange(sps)
    phi = np.pi * h * (start[:, None] + (a[:, None] * n[None, :]) / sps)
    out: NDArray[np.complex128] = (np.cos(phi) + 1j * np.sin(phi)).reshape(-1)
    return out


def fsk_demod_noncoherent(
    samples: ArrayLike, order: int, samples_per_symbol: int, modulation_index: float
) -> NDArray[np.uint8]:
    """Square-law M-FSK detection, one block of ``samples_per_symbol`` per symbol; the label with
    the most energy wins, ties to the smallest (conventions: Bits and symbols, FSK; ADR 0054)."""
    k, sps, h = _fsk_args(order, samples_per_symbol, modulation_index)
    x = np.asarray(samples, dtype=np.complex128)
    if x.ndim != 1:
        raise ValueError("samples must be one-dimensional")
    if x.size % sps:
        raise ValueError("samples must be a multiple of samples_per_symbol")
    if not np.isfinite(x).all():
        raise ValueError("samples must be finite")
    levels = 2 * np.arange(int(order)) - (int(order) - 1)
    psi = np.pi * h * ((levels[:, None] * np.arange(sps)[None, :]) / sps)
    ref = np.cos(psi) - 1j * np.sin(psi)
    c = x.reshape(-1, sps) @ ref.T
    energy = c.real * c.real + c.imag * c.imag
    return _bits_of(np.argmax(energy, axis=1).astype(np.int64), k)


def _ofdm_args(
    nfft: int, cp_len: int, subcarriers: ArrayLike | None
) -> tuple[int, int, NDArray[np.int64]]:
    n = count(nfft, "nfft")
    if n < 1:
        raise ValueError("nfft must be at least 1")
    cp = count(cp_len, "cp_len")
    if cp > n:
        raise ValueError("cp_len must be at most nfft")
    low = -(n // 2)
    if subcarriers is None:
        return n, cp, np.arange(low, low + n, dtype=np.int64)
    k = np.asarray(subcarriers)
    if k.ndim != 1 or k.size == 0 or k.dtype.kind not in "iu":
        raise ValueError("subcarriers must be a non-empty list of integers")
    if np.any(k < low) or np.any(k > low + n - 1):
        raise ValueError(f"subcarriers must lie in {low} ... {low + n - 1}")
    if np.unique(k).size != k.size:
        raise ValueError("subcarriers must be distinct")
    return n, cp, k.astype(np.int64)


def _finite_complex(x: ArrayLike, what: str) -> NDArray[np.complex128]:
    a = np.asarray(x)
    if a.ndim != 1 or (a.size and a.dtype.kind not in "iufc"):
        raise ValueError(f"{what} must be a 1-D array of numbers")
    z = a.astype(np.complex128)
    if not np.isfinite(z).all():
        raise ValueError(f"{what} must be finite")
    return z


def ofdm_modulate(
    symbols: ArrayLike, nfft: int, cp_len: int, subcarriers: ArrayLike | None = None
) -> NDArray[np.complex128]:
    """OFDM blocks: symbols on the listed subcarriers, unitary inverse DFT of ``nfft``, cyclic
    prefix of ``cp_len`` (conventions: Bits and symbols, OFDM; ADR 0060)."""
    n, cp, k = _ofdm_args(nfft, cp_len, subcarriers)
    s = _finite_complex(symbols, "symbols")
    if s.size % k.size:
        raise ValueError("symbols must fill a whole number of blocks")
    spectra = np.zeros((s.size // k.size, n), dtype=np.complex128)
    spectra[:, k % n] = s.reshape(-1, k.size)
    blocks = np.fft.ifft(spectra, axis=1) * math.sqrt(n)
    out: NDArray[np.complex128] = np.concatenate([blocks[:, n - cp :], blocks], axis=1).reshape(-1)
    return out


def ofdm_demodulate(
    samples: ArrayLike, nfft: int, cp_len: int, subcarriers: ArrayLike | None = None
) -> NDArray[np.complex128]:
    """Drop each block's cyclic prefix, take the unitary DFT of ``nfft``, and read the listed
    subcarriers in order (conventions: Bits and symbols, OFDM; ADR 0060)."""
    n, cp, k = _ofdm_args(nfft, cp_len, subcarriers)
    x = _finite_complex(samples, "samples")
    if x.size % (n + cp):
        raise ValueError("samples must be a whole number of blocks of nfft + cp_len")
    blocks = x.reshape(-1, n + cp)[:, cp:]
    spectra = np.fft.fft(blocks, axis=1) / math.sqrt(n)
    out: NDArray[np.complex128] = spectra[:, k % n].reshape(-1)
    return out
