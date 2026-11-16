"""DCT-II and its inverse (conventions: DCT-II; ADR 0156)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


@pytest.mark.parametrize("orthonormal", [True, False])
@pytest.mark.parametrize("n", [1, 2, 3, 7, 16, 25])
def test_round_trip(n: int, orthonormal: bool) -> None:
    x = np.random.default_rng(n).standard_normal(n)
    back = sf.idct(sf.dct(x, orthonormal=orthonormal), orthonormal=orthonormal)
    assert back == pytest.approx(x, abs=1e-12)


def test_orthonormal_matrix_is_orthogonal_and_keeps_energy() -> None:
    n = 13
    m = np.column_stack([sf.dct(e) for e in np.eye(n)])
    assert m @ m.T == pytest.approx(np.eye(n), abs=1e-12)
    x = np.random.default_rng(1).standard_normal(n)
    assert np.sum(sf.dct(x) ** 2) == pytest.approx(np.sum(x**2), rel=1e-12)


def test_rejects_complex_and_two_dimensional() -> None:
    with pytest.raises(ValueError):
        sf.dct([1 + 1j, 0])
    with pytest.raises(ValueError):
        sf.idct(np.zeros((2, 2)))
