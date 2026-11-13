"""Error-rate metrics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike


@dataclass(frozen=True)
class ErrorCount:
    """Errors over a compared span. ``rate`` is ``errors / compared``, NaN if nothing compared."""

    errors: int
    compared: int
    rate: float


def bit_errors(reference: ArrayLike, received: ArrayLike) -> ErrorCount:
    """Count differing bits between two equal-length bit sequences."""
    a = np.asarray(reference)
    b = np.asarray(received)
    if a.ndim != 1 or b.ndim != 1:
        raise ValueError("bit sequences must be one-dimensional")
    if a.shape != b.shape:
        raise ValueError(f"length mismatch: {a.shape[0]} reference vs {b.shape[0]} received")
    errors = int(np.count_nonzero(a != b))
    n = int(a.shape[0])
    return ErrorCount(errors, n, errors / n if n else float("nan"))
