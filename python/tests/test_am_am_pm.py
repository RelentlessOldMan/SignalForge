"""AM/AM and AM/PM by input-level bin (conventions: AM/AM and AM/PM; ADR 0113)."""

import math

import numpy as np
import pytest

from signalforge import am_am_pm, gain_compression


def test_a_linear_gain_with_a_fixed_phase_reads_flat_curves() -> None:
    rng = np.random.default_rng(3)
    x = rng.standard_normal(5000) + 1j * rng.standard_normal(5000)
    g = 3.0 * np.exp(1j * math.radians(-40.0))
    r = am_am_pm(x, g * x, np.arange(-30.0, 13.0, 3.0))
    full = r.counts > 0
    np.testing.assert_allclose(r.gain_db[full], 20 * math.log10(3.0), atol=1e-12)
    np.testing.assert_allclose(r.phase_deg[full], -40.0, atol=1e-10)
    levels = 20 * np.log10(np.abs(x))
    assert r.counts.sum() == np.count_nonzero((levels >= -30) & (levels <= 12))


@pytest.mark.parametrize("p", [1.0, 2.0, 3.0])
def test_a_rapp_limiter_through_gain_compression_finds_its_point(p: float) -> None:
    # A(r) = r / (1 + (r/s)^(2p))^(1/(2p)): 1 dB down where (r/s)^(2p) = 10^(2p/20) - 1
    s = 0.8
    edges = np.arange(-80.0, 10.0 + 0.005, 0.01)
    centres = (edges[:-1] + edges[1:]) / 2
    rad = 10 ** (centres / 20)
    th = np.linspace(0, 2 * math.pi, 4, endpoint=False)
    x = (rad[:, None] * np.exp(1j * th)[None, :]).ravel()
    amp = np.abs(x)
    y = x / (1 + (amp / s) ** (2 * p)) ** (1 / (2 * p))
    r = am_am_pm(x, y, edges)
    assert np.all(r.counts == 4)
    np.testing.assert_allclose(r.phase_deg, 0.0, atol=1e-12)
    c = gain_compression(r.levels_db, r.levels_db + r.gain_db)
    expected = 20 * math.log10(s * (10 ** (2 * p / 20) - 1) ** (1 / (2 * p)))
    assert c.input_point_db == pytest.approx(expected, abs=1e-4)


def test_amplitude_dependent_phase_is_read_per_bin() -> None:
    edges = np.array([-20.0, -10.0, 0.0, 10.0])
    rad = 10 ** (np.array([-15.0, -5.0, 5.0]) / 20)
    x = np.repeat(rad, 3) * np.exp(1j * np.tile([0.1, 2.0, -2.5], 3))
    phi = 0.5 * np.abs(x) ** 2
    r = am_am_pm(x, x * np.exp(1j * phi), edges)
    np.testing.assert_allclose(r.phase_deg, np.degrees(0.5 * rad**2), atol=1e-12)
    np.testing.assert_allclose(r.gain_db, 0.0, atol=1e-12)


@pytest.mark.parametrize(
    ("x", "y", "edges"),
    [
        ([1.0], [1.0, 2.0], [0.0, 1.0]),
        ([], [], [0.0, 1.0]),
        ([1.0], [1.0], [0.0]),
        ([1.0], [1.0], [1.0, 0.0]),
        ([complex(math.nan, 0)], [1.0], [0.0, 1.0]),
        ([[1.0]], [[1.0]], [0.0, 1.0]),
    ],
)
def test_bad_arguments(x: object, y: object, edges: object) -> None:
    with pytest.raises(ValueError):
        am_am_pm(x, y, edges)  # type: ignore[arg-type]
