"""Reading multi-capture SigMF recordings (conventions: Signal files, Captures; ADR 0097)."""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import signalforge as sf


def _write(path: Path, captures: Any, annotations: Any = (), glob: Any = None, n: int = 6) -> Path:
    g = {"core:datatype": "ri16_le", "core:version": "1.0.0", "core:sample_rate": 8, **(glob or {})}
    doc = {"global": g, "captures": captures, "annotations": list(annotations)}
    (path.parent / f"{path.name}.sigmf-meta").write_text(json.dumps(doc), encoding="utf-8")
    (path.parent / f"{path.name}.sigmf-data").write_bytes(struct.pack(f"<{n}h", *range(1, n + 1)))
    return path


def _codes(s: sf.Signal) -> list[float]:
    return list(s.samples * 32768)


def test_segments_split_at_each_start(tmp_path: Path) -> None:
    caps = [{"core:sample_start": 0, "core:frequency": 1e6}, {"core:sample_start": 1}]
    caps.append({"core:sample_start": 4, "core:frequency": -5.5})
    segs = sf.read_sigmf_captures(_write(tmp_path / "s", caps, glob={"signalforge:time_origin": 2}))
    assert [_codes(s) for s in segs] == [[1], [2, 3, 4], [5, 6]]
    assert [s.center_frequency for s in segs] == [1e6, 0.0, -5.5]
    assert [s.time_origin for s in segs] == [2.0, 2 + 1 / 8, 2 + 4 / 8]
    assert all(s.sample_rate == 8 for s in segs)


def test_annotations_are_rebased_into_their_segment(tmp_path: Path) -> None:
    caps = [{"core:sample_start": 0}, {"core:sample_start": 3}]
    spans = [
        {"core:sample_start": 2, "core:sample_count": 4, "x:k": [1]},
        {"core:sample_start": 3, "core:label": "edge"},
        {"core:sample_start": 9},
    ]
    a, b = sf.read_sigmf_captures(_write(tmp_path / "a", caps, spans))
    assert a.metadata["core:annotations"] == [spans[0]]
    assert b.metadata["core:annotations"] == [
        {"core:sample_start": 0, "core:label": "edge"},
        {"core:sample_start": 6},
    ]


def test_a_segment_without_annotations_has_no_key(tmp_path: Path) -> None:
    caps = [{"core:sample_start": 0}, {"core:sample_start": 3}]
    a, b = sf.read_sigmf_captures(_write(tmp_path / "k", caps, [{"core:sample_start": 4}]))
    assert "core:annotations" not in a.metadata
    assert b.metadata["core:annotations"] == [{"core:sample_start": 1}]


def test_segments_share_no_metadata(tmp_path: Path) -> None:
    caps = [{"core:sample_start": 0}, {"core:sample_start": 3}]
    a, b = sf.read_sigmf_captures(_write(tmp_path / "m", caps, glob={"x:tags": ["t"]}))
    a.metadata["x:tags"].append("changed")
    assert b.metadata["x:tags"] == ["t"]


def test_no_captures_is_one_segment(tmp_path: Path) -> None:
    [s] = sf.read_sigmf_captures(_write(tmp_path / "n", []))
    assert (_codes(s), s.center_frequency, s.time_origin) == ([1, 2, 3, 4, 5, 6], 0.0, 0.0)


def test_a_segment_round_trips_through_write_sigmf(tmp_path: Path) -> None:
    caps: list[dict[str, Any]] = [{"core:sample_start": 0, "core:frequency": 1.0}]
    caps.append({"core:sample_start": 2})
    caps[1]["core:frequency"] = 2.0
    seg = sf.read_sigmf_captures(_write(tmp_path / "w", caps))[1]
    sf.write_sigmf(tmp_path / "seg", seg)
    back = sf.read_sigmf(tmp_path / "seg")
    np.testing.assert_array_equal(back.samples, seg.samples)
    assert (back.center_frequency, back.time_origin) == (2.0, 2 / 8)


def test_read_sigmf_names_the_capture_reader(tmp_path: Path) -> None:
    caps = [{"core:sample_start": 0, "core:frequency": 1.0}, {"core:sample_start": 2}]
    with pytest.raises(ValueError, match="read_sigmf_captures"):
        sf.read_sigmf(_write(tmp_path / "r", caps))


@pytest.mark.parametrize(
    ("captures", "glob"),
    [
        ([{"core:sample_start": 2}], {}),
        ([{"core:sample_start": 0}, {"core:sample_start": 3}, {"core:sample_start": 3}], {}),
        ([{"core:sample_start": 0}, {"core:sample_start": 4}, {"core:sample_start": 3}], {}),
        ([{"core:sample_start": 0}, {"core:sample_start": 7}], {}),
        ([{"core:sample_start": 0}, {}], {}),
        ([{"core:sample_start": 0}, {"core:sample_start": "3"}], {}),
        ([{"core:sample_start": 0}, {"core:sample_start": True}], {}),
        ([{"core:sample_start": 0}], {"core:num_channels": 2}),
        ([{"core:sample_start": 0, "core:header_bytes": 2}], {}),
    ],
)
def test_bad_captures_are_rejected(tmp_path: Path, captures: Any, glob: Any) -> None:
    with pytest.raises(ValueError):
        sf.read_sigmf_captures(_write(tmp_path / "b", captures, glob=glob))


def test_a_start_at_the_end_is_an_empty_last_segment(tmp_path: Path) -> None:
    caps = [{"core:sample_start": 0}, {"core:sample_start": 6}]
    a, b = sf.read_sigmf_captures(_write(tmp_path / "e", caps, [{"core:sample_start": 6}]))
    assert (len(a.samples), len(b.samples), b.time_origin) == (6, 0, 6 / 8)
    assert b.metadata["core:annotations"] == [{"core:sample_start": 0}]
