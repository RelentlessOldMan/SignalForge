import numpy as np
import pytest

from signalforge import bit_errors, prbs, qpsk_demap_hard, qpsk_map


def test_qpsk_round_trip_and_unit_energy():
    bits = prbs(9, 2 * 511 + 2)[: 2 * 511]
    s = qpsk_map(bits)
    assert np.mean(np.abs(s) ** 2) == pytest.approx(1.0)
    np.testing.assert_array_equal(qpsk_demap_hard(s), bits)


def test_qpsk_neighbours_differ_by_one_bit():
    pts = {tuple(qpsk_demap_hard([s])): s for s in qpsk_map([0, 0, 0, 1, 1, 1, 1, 0])}
    order = [(0, 0), (0, 1), (1, 1), (1, 0)]  # going around the circle
    for a, b in zip(order, order[1:] + order[:1], strict=True):
        assert sum(x != y for x, y in zip(a, b, strict=True)) == 1
        assert abs(pts[a] - pts[b]) == pytest.approx(np.sqrt(2))


def test_rotation_by_90_degrees_costs_one_bit_per_symbol():
    bits = np.array([0, 0, 0, 1, 1, 0, 1, 1])
    rx = qpsk_demap_hard(qpsk_map(bits) * 1j)
    assert bit_errors(bits, rx).errors == 4


def test_bit_errors_empty():
    r = bit_errors([], [])
    assert r.errors == 0 and r.compared == 0 and np.isnan(r.rate)
