"""Noise figure by the Y-factor method (conventions: Noise figure; ADR 0105)."""

from __future__ import annotations

import math

import pytest

import signalforge as sf

K = 1.380649e-23  # Boltzmann's constant; any gain-bandwidth factor cancels in Y


@pytest.mark.parametrize("te", [0.0, 35.0, 290.0, 1500.0, 12000.0])
@pytest.mark.parametrize("tc", [77.0, 290.0, 300.0])
@pytest.mark.parametrize("enr_db", [5.0, 15.0, 25.0])
def test_measures_a_simulated_device(te: float, tc: float, enr_db: float) -> None:
    # a device adding te kelvin: output power is proportional to (source + te)
    th = 290 * (1 + 10 ** (enr_db / 10))
    gain_bw = 1e6 * 1e3
    r = sf.noise_figure_y_factor(
        K * gain_bw * (th + te), K * gain_bw * (tc + te), enr_db, cold_temperature=tc
    )
    assert r.noise_temperature == pytest.approx(te, abs=1e-9 * th)
    assert r.noise_factor == pytest.approx(1 + te / 290, rel=1e-12, abs=1e-12)
    assert r.y_factor == pytest.approx((th + te) / (tc + te), rel=1e-14)


def test_textbook_and_reduced_form() -> None:
    r = sf.noise_figure_y_factor(10.0, 1.0, 15.0)
    assert r.noise_figure_db == pytest.approx(15 - 10 * math.log10(9), rel=1e-14)
    for y in (1.5, 4.0, 30.0):
        assert sf.noise_figure_y_factor(y, 1.0, 12.0).noise_factor == pytest.approx(
            10**1.2 / (y - 1), rel=1e-14
        )
    assert sf.noise_figure_y_factor(12.0, 1.0, 10.0).noise_figure_db < 0


@pytest.mark.parametrize(
    "args",
    [
        (1.0, 1.0, 15.0, 290.0),
        (0.5, 1.0, 15.0, 290.0),
        (1.0, 0.0, 15.0, 290.0),
        (math.nan, 1.0, 15.0, 290.0),
        (2.0, 1.0, math.inf, 290.0),
        (2.0, 1.0, 4000.0, 290.0),
        (1e300, 1e-300, 15.0, 290.0),
        (2.0, 1.0, 15.0, 0.0),
        (2.0, 1.0, 15.0, -10.0),
        (2.0, 1.0, 0.0, 580.0),
        (True, 0.5, 15.0, 290.0),
    ],
)
def test_bad_arguments(args: tuple[float, float, float, float]) -> None:
    with pytest.raises(ValueError):
        sf.noise_figure_y_factor(args[0], args[1], args[2], cold_temperature=args[3])
