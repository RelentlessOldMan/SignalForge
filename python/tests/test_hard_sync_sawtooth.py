"""Hard-synced sawtooth (ADR 0315)."""

from __future__ import annotations

import numpy as np
import pytest

import signalforge as sf


def test_equal_frequencies_give_the_naive_sawtooth() -> None:
    y = sf.hard_sync_sawtooth(8000.0, 200, 250.0, 250.0, 0.7)
    assert np.allclose(y, sf.sawtooth(8000.0, 200, 250.0, 0.7), rtol=0, atol=1e-12)


def test_the_output_repeats_at_the_master_period() -> None:
    # Master 256 Hz at 8192 Hz: 32 samples a cycle, whatever the slave does; n/fs is exact.
    y = sf.hard_sync_sawtooth(8192.0, 320, 537.3, 256.0)
    assert np.allclose(y[32:], y[:-32], rtol=0, atol=1e-12)
    spectrum = np.abs(np.fft.rfft(y))
    lines = np.flatnonzero(spectrum > 1e-9 * spectrum.max())
    assert np.all(lines % 10 == 0)


@pytest.mark.parametrize("sync", [0.0, -100.0, float("inf")])
def test_rejects_a_master_that_does_not_run_forwards(sync: float) -> None:
    with pytest.raises(ValueError):
        sf.hard_sync_sawtooth(8000.0, 4, 1000.0, sync)
