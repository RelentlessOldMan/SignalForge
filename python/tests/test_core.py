import numpy as np
import pytest

from signalforge import Signal


def test_signal_is_read_only_and_copies() -> None:
    raw = np.array([1.0, 2.0, 3.0])
    s = Signal(raw, 10.0, units="V", impedance=50.0)
    raw[0] = 99
    assert s.samples[0] == 1.0
    with pytest.raises(ValueError):
        s.samples[0] = 5
    assert len(s) == 3 and s.duration == pytest.approx(0.3) and not s.is_complex


def test_times_and_with_samples() -> None:
    s = Signal(np.zeros(4, complex), 2.0, center_frequency=1e9, time_origin=1.0, metadata={"a": 1})
    np.testing.assert_allclose(s.times(), [1.0, 1.5, 2.0, 2.5])
    t = s.with_samples([1j, 2j])
    assert t.center_frequency == 1e9 and len(t) == 2 and t.is_complex and t.metadata["a"] == 1


def test_integer_samples_become_float_and_validation() -> None:
    assert Signal.from_samples([1, 2], 1.0).samples.dtype == np.float64
    with pytest.raises(ValueError):
        Signal.from_samples([1.0], 0.0)
    with pytest.raises(ValueError):
        Signal(np.zeros((2, 2)), 1.0)
    with pytest.raises(TypeError):
        Signal.from_samples([1.0], 1.0).metadata["x"] = 1  # type: ignore[index]
