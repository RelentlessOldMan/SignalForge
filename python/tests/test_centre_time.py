"""Centre time and the early decay time (conventions: Centre time; ADR 0173)."""

from __future__ import annotations

import math

import numpy as np
import pytest

import signalforge as sf


def test_a_long_geometric_decay_has_centre_q_over_one_minus_q() -> None:
    q = 0.999**2
    ir = 0.999 ** np.arange(40000)
    assert sf.centre_time(ir, 1000.0) == pytest.approx(q / (1 - q) / 1000.0, rel=1e-9)


def test_the_early_decay_time_is_the_zero_to_minus_ten_fit() -> None:
    ir = 0.999 ** np.arange(40000)
    edt = sf.reverberation_time(ir, 1000.0, start_db=0.0, stop_db=-10.0)
    assert edt == pytest.approx(60 / (-20 * math.log10(0.999) * 1000.0), rel=1e-9)
