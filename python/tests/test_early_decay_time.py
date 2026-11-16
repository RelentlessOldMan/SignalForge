"""Early decay time (conventions: Early decay time; ADR 0181)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_it_is_reverberation_time_from_zero_to_minus_ten() -> None:
    rng = np.random.default_rng(31)
    h = rng.standard_normal(6000) * 0.998 ** np.arange(6000)
    assert sf.early_decay_time(h, 8000.0) == sf.reverberation_time(
        h, 8000.0, start_db=0.0, stop_db=-10.0
    )
