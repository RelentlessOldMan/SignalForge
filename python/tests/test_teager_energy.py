"""Teager-Kaiser energy (conventions: Teager-Kaiser energy; ADR 0188)."""

from __future__ import annotations

import numpy as np

import signalforge as sf


def test_real_and_complex_forms_agree_on_real_input() -> None:
    x = np.random.default_rng(34).standard_normal(50)
    assert np.allclose(sf.teager_energy(x), sf.teager_energy(x.astype(np.complex128)))
