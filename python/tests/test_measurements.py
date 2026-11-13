import math

import numpy as np
import pytest

from signalforge import measurements, waveforms


def test_real_sine_papr_is_3db():
    x = waveforms.tone(1000, 1000, 50, complex=False)
    s = measurements.power_stats(x)
    assert s.mean_power == pytest.approx(0.5)
    assert s.papr_db == pytest.approx(10 * math.log10(2))
    assert abs(s.dc) < 1e-12


def test_complex_dc_and_types():
    s = measurements.power_stats(np.array([1 + 2j, 3 - 1j]))
    assert s.dc == pytest.approx(2 + 0.5j)
    assert s.peak_index == 1
    assert isinstance(s.num_samples, int)


def test_float32_accumulates_in_double():
    x = np.full(1_000_001, 0.1, dtype=np.float32)
    assert measurements.power_stats(x).mean_power == pytest.approx(float(np.float32(0.1)) ** 2)


def test_rejects_2d():
    with pytest.raises(ValueError):
        measurements.power_stats(np.zeros((2, 2)))
