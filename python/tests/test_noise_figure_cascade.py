"""Cascaded noise figure by Friis' formula (conventions: Noise figure, Cascade; ADR 0106)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_noise_temperatures_add_through_the_gain() -> None:
    # the same chain in noise temperatures: Te = Te1 + Te2/G1 + Te3/(G1 G2)
    te = [50.0, 400.0, 2000.0]
    g = [15.0, 8.0, -3.0]
    nf = [10 * math.log10(1 + t / 290) for t in te]
    r = sf.noise_figure_cascade(nf, g)
    want = te[0] + te[1] / 10**1.5 + te[2] / 10**2.3
    assert r.noise_temperature == pytest.approx(want, rel=1e-12)
    assert r.gain_db == pytest.approx(20.0, rel=1e-15)
    assert r.contributions.sum() == pytest.approx(r.noise_factor, rel=1e-15)


def test_loss_in_front_adds_in_db_and_one_stage_is_itself() -> None:
    for loss, nf2 in ((3.0, 1.5), (6.0, 2.0), (10.0, 0.5)):
        r = sf.noise_figure_cascade([loss, nf2], [-loss, 25.0])
        assert r.noise_figure_db == pytest.approx(loss + nf2, abs=1e-12)
    r = sf.noise_figure_cascade(np.array([4.5]), np.array([12.0]))
    assert r.noise_figure_db == pytest.approx(4.5, abs=1e-12)
    assert r.contributions.shape == (1,)


def test_a_huge_first_gain_hides_later_stages() -> None:
    r = sf.noise_figure_cascade([2.0, 30.0, 30.0], [300.0, 300.0, 0.0])
    assert r.noise_figure_db == pytest.approx(2.0, abs=1e-12)
    r = sf.noise_figure_cascade([1.0, 1.0], [4000.0, 0.0])  # G1 overflows to +inf
    assert r.noise_figure_db == pytest.approx(1.0, abs=1e-12)


@pytest.mark.parametrize(
    ("nf", "g"),
    [
        ([], []),
        ([1.0], [1.0, 2.0]),
        ([1.0, -0.5], [1.0, 1.0]),
        ([math.nan], [1.0]),
        ([1.0], [-math.inf]),
        ([1.0, 2.0], [-4000.0, 0.0]),
        ([4000.0], [0.0]),
        ([[1.0]], [[1.0]]),
    ],
)
def test_bad_arguments(nf: list[float], g: list[float]) -> None:
    with pytest.raises(ValueError):
        sf.noise_figure_cascade(nf, g)
