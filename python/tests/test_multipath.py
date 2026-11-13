"""Multipath: the tapped delay line against NumPy's convolution with the dense taps, truncated to
the input's length (conventions: Channel, Multipath)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_matches_dense_convolution() -> None:
    rng = np.random.default_rng(3)
    x = rng.standard_normal(200) + 1j * rng.standard_normal(200)
    delays = [0, 3, 3, 17, 250]
    gains = [1.0, 0.5 - 0.25j, 0.1j, -0.3, 2.0]
    dense = np.zeros(max(delays) + 1, complex)
    for d, g in zip(delays, gains, strict=True):
        dense[d] += g
    want = np.convolve(x, dense)[: x.size]
    np.testing.assert_allclose(sf.multipath(x, delays, gains), want, rtol=0, atol=1e-13)


def test_real_input_and_numpy_delays() -> None:
    y = sf.multipath(np.array([1.0, 2.0, 3.0]), np.array([1], dtype=np.int64), [2])
    np.testing.assert_array_equal(y, [0, 2, 4])
    assert y.dtype == np.complex128


@pytest.mark.parametrize(
    ("samples", "delays", "gains"),
    [
        ([[1.0]], [0], [1]),
        ([1.0], [0.5], [1]),
        ([1.0], [1.0], [1]),
        ([1.0], [True], [1]),
        ([1.0], [-1], [1]),
        ([1.0], [[0]], [[1]]),
        ([1.0], [0, 1], [1]),
        ([1.0], [], []),
        ([1.0], [0], [True]),
        ([1.0], [0], [np.inf]),
    ],
)
def test_bad_arguments_raise(samples: object, delays: object, gains: object) -> None:
    with pytest.raises(ValueError):
        sf.multipath(samples, delays, gains)  # type: ignore[arg-type]
