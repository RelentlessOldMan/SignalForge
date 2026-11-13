"""The Signal type: samples plus the metadata needed to interpret them."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray


@dataclass(frozen=True, eq=False)
class Signal:
    """A finite sampled signal, real or complex baseband.

    ``samples`` is stored read-only. Operations return new signals. ``units`` names what one sample
    unit is (``"V"`` for volts, ``"FS"`` for full scale, ``None`` when unknown); ``impedance`` is in
    ohms and only meaningful for voltage units. See docs/conventions.md.
    """

    samples: NDArray[Any]
    sample_rate: float
    center_frequency: float = 0.0
    time_origin: float = 0.0
    units: str | None = None
    impedance: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        a = np.array(self.samples, copy=True)
        if a.ndim != 1:
            raise ValueError("samples must be one-dimensional")
        if not (np.issubdtype(a.dtype, np.floating) or np.issubdtype(a.dtype, np.complexfloating)):
            a = a.astype(np.float64)
        a.setflags(write=False)
        object.__setattr__(self, "samples", a)
        if not 0 < self.sample_rate < math.inf:
            raise ValueError("sample_rate must be positive and finite")
        if self.impedance is not None and not 0 < self.impedance < math.inf:
            raise ValueError("impedance must be positive and finite")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @classmethod
    def from_samples(cls, samples: ArrayLike, sample_rate: float, **kwargs: Any) -> Signal:
        return cls(np.asarray(samples), sample_rate, **kwargs)

    def __len__(self) -> int:
        return int(self.samples.shape[0])

    @property
    def is_complex(self) -> bool:
        return bool(np.iscomplexobj(self.samples))

    @property
    def duration(self) -> float:
        """Number of samples divided by the sample rate, in seconds."""
        return len(self) / self.sample_rate

    def times(self) -> NDArray[np.float64]:
        """Time of each sample: ``time_origin + n / sample_rate``."""
        return self.time_origin + np.arange(len(self)) / self.sample_rate

    def with_samples(self, samples: ArrayLike) -> Signal:
        """A copy with new samples and the same metadata."""
        return replace(self, samples=np.asarray(samples))
