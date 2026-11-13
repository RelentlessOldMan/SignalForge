"""Block fading: the gain's statistics against Rician theory, one gain per block
(conventions: Channel, Block fading)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf

N = 200_000


@pytest.mark.parametrize("k", [0.0, 1.0, 3.0, 10.0])
def test_gain_statistics(k: float) -> None:
    g = sf.rician_fading(np.ones(N), k, 1, seed=4)
    # unit mean power; the line-of-sight part is the mean; the scatter is circular
    assert np.mean(np.abs(g) ** 2) == pytest.approx(1, rel=0.015)
    assert g.real.mean() == pytest.approx(math.sqrt(k / (k + 1)), abs=0.01)
    assert abs(g.imag.mean()) < 0.01
    assert g.real.var() == pytest.approx(0.5 / (k + 1), rel=0.02)
    assert g.imag.var() == pytest.approx(0.5 / (k + 1), rel=0.02)


def test_rayleigh_power_is_exponential() -> None:
    p = np.abs(sf.rician_fading(np.ones(N), 0.0, 1, seed=8)) ** 2
    for x in (0.1, 0.5, 1.0, 2.0, 4.0):
        assert np.mean(p < x) == pytest.approx(1 - math.exp(-x), abs=0.005)


def test_one_gain_per_block() -> None:
    x = np.arange(1, 12) * (1 - 0.5j)
    y = sf.rician_fading(x, 2.0, 4, seed=1)
    g = y / x
    for block in (g[0:4], g[4:8], g[8:11]):
        np.testing.assert_allclose(block, block[0], rtol=1e-15)
    assert len({g[0], g[4], g[8]}) == 3


def test_seed_reproducible() -> None:
    x = np.ones(50)
    a = sf.rician_fading(x, 1.0, 5, seed=9)
    np.testing.assert_array_equal(a, sf.rician_fading(x, 1.0, 5, seed=9))
    np.testing.assert_array_equal(a, sf.rician_fading(x, 1.0, 5, seed=np.random.default_rng(9)))


def test_infinite_k_is_identity() -> None:
    x = np.array([1 + 2j, -3, 0.5j])
    np.testing.assert_array_equal(sf.rician_fading(x, math.inf, 1, seed=0), x)


@pytest.mark.parametrize(
    "call",
    [
        lambda: sf.rician_fading([[1.0]], 1.0, 1, seed=0),
        lambda: sf.rician_fading([1.0], -1.0, 1, seed=0),
        lambda: sf.rician_fading([1.0], math.nan, 1, seed=0),
        lambda: sf.rician_fading([1.0], True, 1, seed=0),
        lambda: sf.rician_fading([1.0], 1.0, 0, seed=0),
        lambda: sf.rician_fading([1.0], 1.0, 2.0, seed=0),  # type: ignore[arg-type]
        lambda: sf.rician_fading([1.0], 1.0, 1, seed=-1),
    ],
)
def test_bad_arguments_raise(call: object) -> None:
    with pytest.raises(ValueError):
        call()  # type: ignore[operator]
