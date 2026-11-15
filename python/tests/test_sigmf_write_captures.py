"""Writing multi-capture SigMF recordings (conventions: Signal files, Captures; ADR 0100)."""

import json
import struct
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import signalforge as sf

BY_HAND = """{
  "global": {
    "core:datatype": "rf64_le",
    "core:version": "1.2.0",
    "core:sample_rate": 4.0,
    "core:extensions": [
      {
        "name": "signalforge",
        "version": "1.0.0",
        "optional": true
      }
    ],
    "signalforge:time_origin": 0.5,
    "signalforge:metadata": {
      "k": 1
    }
  },
  "captures": [
    {
      "core:sample_start": 0,
      "core:frequency": 100.0
    },
    {
      "core:sample_start": 3,
      "core:frequency": 200.0
    }
  ],
  "annotations": [
    {
      "core:sample_start": 2,
      "core:label": "x"
    },
    {
      "core:sample_start": 3,
      "core:sample_count": 5
    }
  ]
}
"""


def seg(x: Any, t0: float, f: float = 0.0, ann: Any = None, rate: float = 4.0) -> sf.Signal:
    md: dict[str, Any] = {"k": 1}
    if ann is not None:
        md["core:annotations"] = ann
    return sf.Signal(np.asarray(x), rate, center_frequency=f, time_origin=t0, metadata=md)


def test_writes_the_files_by_hand(tmp_path: Path) -> None:
    a = seg([1.0, 2, 3], 0.5, 100.0, [{"core:sample_start": 2, "core:label": "x"}])
    b = seg([4.0], 0.5 + 3 / 4, 200.0, [{"core:sample_start": 0, "core:sample_count": 5}])
    sf.write_sigmf_captures(tmp_path / "r", [a, b])
    assert (tmp_path / "r.sigmf-meta").read_text(encoding="utf-8") == BY_HAND
    assert (tmp_path / "r.sigmf-data").read_bytes() == struct.pack("<4d", 1, 2, 3, 4)


def test_round_trips_through_the_reader(tmp_path: Path) -> None:
    rate = 3.0
    parts = [
        seg([1 + 1j, 2], 0.25, -5.0, [{"core:sample_start": 1}], rate),
        seg([3j, 4, 5], 0.25 + 2 / rate, 7.5, None, rate),
        seg(np.zeros(0, complex), 0.25 + 5 / rate, 9.0, [{"core:sample_start": 4}], rate),
    ]
    sf.write_sigmf_captures(tmp_path / "c", parts, "cf32_le")
    back = sf.read_sigmf_captures(tmp_path / "c")
    assert len(back) == 3
    for p, q in zip(parts, back, strict=True):
        assert np.array_equal(p.samples, q.samples)
        assert (q.center_frequency, q.time_origin) == (p.center_frequency, p.time_origin)
        assert dict(q.metadata) == dict(p.metadata)
    sf.write_sigmf_captures(tmp_path / "d", back, "cf32_le")
    for ext in (".sigmf-meta", ".sigmf-data"):
        assert (tmp_path / f"c{ext}").read_bytes() == (tmp_path / f"d{ext}").read_bytes()


def test_one_segment_writes_the_write_sigmf_files(tmp_path: Path) -> None:
    s = seg([1.0, -2.0], 1.5, 3.0, [{"core:sample_start": 9}])
    sf.write_sigmf(tmp_path / "a", s)
    sf.write_sigmf_captures(tmp_path / "b", [s])
    for ext in (".sigmf-meta", ".sigmf-data"):
        assert (tmp_path / f"a{ext}").read_bytes() == (tmp_path / f"b{ext}").read_bytes()


def test_a_single_empty_segment(tmp_path: Path) -> None:
    sf.write_sigmf_captures(tmp_path / "e", [seg(np.zeros(0), 0.0)])
    doc = json.loads((tmp_path / "e.sigmf-meta").read_text(encoding="utf-8"))
    assert doc["captures"] == [{"core:sample_start": 0, "core:frequency": 0.0}]
    assert len(sf.read_sigmf_captures(tmp_path / "e")[0].samples) == 0


def test_the_time_origin_must_be_exact(tmp_path: Path) -> None:
    # 0.1 + 2/10 is 0.30000000000000004 in binary64, so 0.3 is off by one ulp.
    a, b = seg([1.0, 2], 0.1, rate=10.0), seg([4.0], 0.3, rate=10.0)
    with pytest.raises(ValueError, match="time origin"):
        sf.write_sigmf_captures(tmp_path / "t", [a, b])
    sf.write_sigmf_captures(tmp_path / "t", [a, seg([4.0], 0.1 + 2 / 10, rate=10.0)])


def test_the_last_annotation_may_run_past(tmp_path: Path) -> None:
    sf.write_sigmf_captures(
        tmp_path / "l", [seg([1.0], 0.0), seg([2.0], 0.25, ann=[{"core:sample_start": 7}])]
    )
    assert sf.read_sigmf_captures(tmp_path / "l")[1].metadata["core:annotations"] == [
        {"core:sample_start": 7}
    ]


@pytest.mark.parametrize(
    "segments",
    [
        [],
        [seg([1.0], 0.0), "x"],
        [seg([1.0], 0.0), seg([1j], 0.25)],
        [seg(np.zeros(0), 0.0), seg([1.0], 0.0)],
        [seg([1.0], 0.0), seg([2.0], 0.25, rate=5.0)],
        [seg([1.0], 0.0), sf.Signal(np.array([2.0]), 4.0, time_origin=0.25)],
        [seg([1.0], 0.0, ann=[{"core:sample_start": 1}]), seg([2.0], 0.25)],
        [
            seg([1.0], 0.0),
            seg([2.0], 0.25, ann=[{"core:sample_start": 1}, {"core:sample_start": 0}]),
        ],
        [seg([1.0], 0.0), seg([2.0], 0.25, f=float("nan"))],
        [seg([1.0], float("inf")), seg([2.0], float("inf"))],
    ],
)
def test_rejects_and_writes_nothing(tmp_path: Path, segments: Any) -> None:
    with pytest.raises(ValueError):
        sf.write_sigmf_captures(tmp_path / "x", segments)
    assert not list(tmp_path.iterdir())


def test_rejects_a_signal_alone(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        sf.write_sigmf_captures(tmp_path / "x", seg([1.0], 0.0))  # type: ignore[arg-type]
