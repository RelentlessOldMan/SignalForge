"""SigMF annotations as the metadata key core:annotations (conventions: Signal files; ADR 0061)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import signalforge as sf

SPANS: list[dict[str, Any]] = [
    {"core:sample_start": 2, "core:sample_count": 3, "core:label": "burst"},
    {"core:sample_start": 2, "core:comment": "same start"},
    {"core:sample_start": np.int64(7), "x:score": 0.5},
]


def _signal(metadata: dict[str, Any]) -> sf.Signal:
    return sf.Signal(np.arange(8) / 16, 1e3, metadata=metadata)


def test_round_trip_and_layout(tmp_path: Path) -> None:
    sf.write_sigmf(tmp_path / "a", _signal({"core:annotations": SPANS, "run": 1}))
    doc = json.loads((tmp_path / "a.sigmf-meta").read_text(encoding="utf-8"))
    assert "core:annotations" not in doc["global"]
    assert doc["annotations"][0] == SPANS[0]
    assert doc["annotations"][2] == {"core:sample_start": 7, "x:score": 0.5}
    r = sf.read_sigmf(tmp_path / "a")
    assert r.metadata["core:annotations"] == [*SPANS[:2], doc["annotations"][2]]
    assert r.metadata["run"] == 1


def test_empty_list_reads_back_as_no_key(tmp_path: Path) -> None:
    sf.write_sigmf(tmp_path / "e", _signal({"core:annotations": []}))
    assert json.loads((tmp_path / "e.sigmf-meta").read_text(encoding="utf-8"))["annotations"] == []
    assert "core:annotations" not in sf.read_sigmf(tmp_path / "e").metadata


def test_span_past_the_samples_is_kept(tmp_path: Path) -> None:
    far = [{"core:sample_start": 100, "core:sample_count": 50}]
    sf.write_sigmf(tmp_path / "f", _signal({"core:annotations": far}))
    assert sf.read_sigmf(tmp_path / "f").metadata["core:annotations"] == far


@pytest.mark.parametrize(
    "annotations",
    [
        {"core:sample_start": 0},
        "spans",
        [5],
        [{"core:label": "no start"}],
        [{"core:sample_start": 1.0}],
        [{"core:sample_start": True}],
        [{"core:sample_start": -1}],
        [{"core:sample_start": 0, "core:sample_count": -1}],
        [{"core:sample_start": 0, "core:sample_count": 2.5}],
        [{"core:sample_start": 3}, {"core:sample_start": 2}],
        [{"core:sample_start": 0, "x:bad": float("nan")}],
    ],
)
def test_write_rejects(tmp_path: Path, annotations: object) -> None:
    with pytest.raises(ValueError):
        sf.write_sigmf(tmp_path / "w", _signal({"core:annotations": annotations}))
    assert not (tmp_path / "w.sigmf-meta").exists()
