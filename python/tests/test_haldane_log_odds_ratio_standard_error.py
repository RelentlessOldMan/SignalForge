"""The standard error of the Haldane log odds ratio (ADR 0497)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_is_woolf_on_the_corrected_cells_and_ignores_complementing() -> None:
    rng = np.random.default_rng(260)
    for _ in range(30):
        t = (rng.random(20) < 0.3).astype(float)
        d = (rng.random(20) < 0.7).astype(float)
        tp, fn = np.sum(t * d) + 0.5, np.sum(t * (1 - d)) + 0.5
        fp, tn = np.sum((1 - t) * d) + 0.5, np.sum((1 - t) * (1 - d)) + 0.5
        v = sf.haldane_log_odds_ratio_standard_error(t, d)
        want = math.sqrt(float(1 / tp + 1 / fn + 1 / fp + 1 / tn))
        assert v == pytest.approx(want, rel=1e-14)
        assert sf.haldane_log_odds_ratio_standard_error(t, 1 - d) == pytest.approx(v, rel=1e-15)


def test_rejects_records_of_different_lengths() -> None:
    with pytest.raises(ValueError):
        sf.haldane_log_odds_ratio_standard_error([1.0, 0.0], [1.0])
