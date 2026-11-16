"""Inharmonicity (conventions: Spectra, Inharmonicity; ADR 0140)."""

from __future__ import annotations

import itertools

import numpy as np
import pytest

import signalforge as sf

TONES = np.array([100.0, 203.0, 298.5, 404.0])
HEIGHTS = np.array([5.0, 3.0, 2.0, 1.0])
ORDERS = np.array([1, 2, 3, 4])


def test_scaling_frequencies_and_fundamental_leaves_it_unchanged() -> None:
    a = sf.inharmonicity(TONES, HEIGHTS, 100.0, ORDERS)
    b = sf.inharmonicity(3.5 * TONES, HEIGHTS, 350.0, ORDERS)
    assert b == pytest.approx(a, rel=1e-12)


def test_scaling_heights_leaves_it_unchanged() -> None:
    a = sf.inharmonicity(TONES, HEIGHTS, 100.0, ORDERS)
    b = sf.inharmonicity(TONES, 7.0 * HEIGHTS, 100.0, ORDERS)
    assert b == pytest.approx(a, rel=1e-12)


def test_stiff_string_grows_with_stiffness() -> None:
    m = np.arange(1, 9)
    values = [
        sf.inharmonicity(110.0 * m * np.sqrt(1 + b * m**2), 1.0 / m, 110.0, m)
        for b in (0.0, 1e-4, 1e-3, 1e-2)
    ]
    assert values[0] == 0.0
    assert all(x < y for x, y in itertools.pairwise(values))
