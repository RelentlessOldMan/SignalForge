"""Linkwitz-Riley crossover (ADR 0284)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


@pytest.mark.parametrize("order", [2, 4, 6, 8])
def test_bands_sum_to_an_all_pass(order: int) -> None:
    x = sf.linkwitz_riley(order, 1200.0, 48000.0)
    f = np.linspace(10.0, 23990.0, 50)
    h = sf.sos_response(x.low, f, 48000.0) + sf.sos_response(x.high, f, 48000.0)
    assert np.abs(h) == pytest.approx(np.ones(50), abs=1e-10)
    at = [1200.0]
    assert abs(sf.sos_response(x.low, at, 48000.0)[0]) == pytest.approx(0.5, abs=1e-12)
    assert abs(sf.sos_response(x.high, at, 48000.0)[0]) == pytest.approx(0.5, abs=1e-12)


def test_filtered_bands_add_back_to_an_all_pass_of_the_input() -> None:
    rng = np.random.default_rng(51)
    x = rng.standard_normal(4000)
    lr = sf.linkwitz_riley(4, 0.1, 1.0)
    y = sf.IirFilter(lr.low).process(x) + sf.IirFilter(lr.high).process(x)
    assert np.sum(y**2) == pytest.approx(np.sum(x**2), rel=0.02)


def test_rejects_odd_order() -> None:
    with pytest.raises(ValueError):
        sf.linkwitz_riley(5, 1.0, 8.0)
