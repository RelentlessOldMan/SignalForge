"""Welch equivalent degrees of freedom (conventions: Welch degrees of freedom; ADR 0200)."""

from __future__ import annotations

import signalforge as sf


def test_hann_half_overlap_tends_to_36_over_19_per_segment() -> None:
    # periodic Hann at 50 %: rho(1) = 1/6, so nu/K -> 2 / (1 + 2/36) = 36/19
    k = 4000
    assert abs(sf.welch_dof(256, 128, k) / k - 36 / 19) < 1e-3
