"""8-PSK and 16-QAM: round trips, unit energy, Gray neighbors, decisions under small noise
(conventions: Bits and symbols)."""

from __future__ import annotations

import itertools
import math

import numpy as np
import pytest

import signalforge as sf

SCHEMES = [(sf.psk8_map, sf.psk8_demap_hard, 3), (sf.qam16_map, sf.qam16_demap_hard, 4)]


def _all_labels(k: int) -> np.ndarray:
    return np.array(list(itertools.product([0, 1], repeat=k)), dtype=np.uint8).reshape(-1)


@pytest.mark.parametrize(("mod", "demod", "k"), SCHEMES)
def test_round_trip_and_unit_energy(mod, demod, k) -> None:  # type: ignore[no-untyped-def]
    pts = mod(_all_labels(k))
    assert len(set(np.round(pts, 12))) == 2**k
    assert np.mean(np.abs(pts) ** 2) == pytest.approx(1.0, abs=1e-15)
    bits = sf.prbs(9, 511 * k)
    np.testing.assert_array_equal(demod(mod(bits)), bits)


@pytest.mark.parametrize(("mod", "demod", "k"), SCHEMES)
def test_nearest_neighbors_differ_by_one_bit(mod, demod, k) -> None:  # type: ignore[no-untyped-def]
    labels = _all_labels(k).reshape(-1, k)
    pts = mod(labels.reshape(-1))
    dist = np.abs(pts[:, None] - pts[None, :])
    nearest = np.min(dist + np.eye(len(pts)) * 9)
    pairs = np.argwhere(np.isclose(dist, nearest, atol=1e-12))
    assert len(pairs) == {3: 16, 4: 48}[k]
    for a, b in pairs:
        assert np.sum(labels[a] != labels[b]) == 1


@pytest.mark.parametrize(("mod", "demod", "k"), SCHEMES)
def test_small_noise_does_not_change_a_decision(mod, demod, k) -> None:  # type: ignore[no-untyped-def]
    bits = sf.prbs(11, 2047 * k)
    s = mod(bits)
    margin = {3: math.sin(math.pi / 8), 4: 1 / math.sqrt(10)}[k]
    rng = np.random.default_rng(5)
    noise = rng.uniform(-1, 1, s.size) + 1j * rng.uniform(-1, 1, s.size)
    noisy = s + 0.99 * margin / math.sqrt(2) * noise
    np.testing.assert_array_equal(demod(noisy), bits)


def test_psk8_labels_go_round_as_a_gray_code() -> None:
    angles = np.angle(sf.psk8_map(_all_labels(3))) % (2 * math.pi)
    order = np.argsort(angles)
    np.testing.assert_array_equal(order, [0, 1, 3, 2, 6, 7, 5, 4])


def test_qam16_ties() -> None:
    t = 2 / math.sqrt(10)
    np.testing.assert_array_equal(
        sf.qam16_demap_hard([0, complex(t, -t)]), [0, 1, 0, 1, 0, 0, 1, 0]
    )
    np.testing.assert_array_equal(sf.psk8_demap_hard([0]), [0, 0, 0])


@pytest.mark.parametrize(
    "call",
    [
        lambda: sf.psk8_map([0, 1]),
        lambda: sf.psk8_map([0, 1, 2]),
        lambda: sf.qam16_map([0, 1, 1]),
        lambda: sf.qam16_map([0, 1, 1, 0.5]),
        lambda: sf.psk8_demap_hard([[1]]),
        lambda: sf.qam16_demap_hard([[1]]),
    ],
)
def test_bad_arguments_raise(call: object) -> None:
    with pytest.raises(ValueError):
        call()  # type: ignore[operator]
