"""Multi-channel SigMF recordings (conventions: Signal files, Channels; ADR 0096)."""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import signalforge as sf
from signalforge.files import MAX_CHANNELS

BURST = [{"core:sample_start": 1, "core:sample_count": 2, "core:label": "burst"}]


def _channel(samples: Any, **kw: Any) -> sf.Signal:
    fields: dict[str, Any] = {
        "center_frequency": 2.4e9,
        "time_origin": 0.5,
        "units": "V",
        "impedance": 50.0,
        "metadata": {"core:annotations": BURST, "run": 3, "x:gain": 1.5},
    }
    fields.update(kw)
    return sf.Signal(np.asarray(samples), 2e6, **fields)


def _meta(path: Path) -> dict[str, Any]:
    doc: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return doc


def test_round_trip(tmp_path: Path) -> None:
    chans = [_channel([1 + 2j, -0.5j, 0.25]), _channel([3, 4j, -1 - 1j])]
    sf.write_sigmf_channels(tmp_path / "r", chans)
    back = sf.read_sigmf_channels(tmp_path / "r")
    assert len(back) == 2
    for want, got in zip(chans, back, strict=True):
        np.testing.assert_array_equal(got.samples, want.samples)
        assert got.samples.dtype == np.complex128
        assert (got.sample_rate, got.center_frequency, got.time_origin) == (2e6, 2.4e9, 0.5)
        assert (got.units, got.impedance) == ("V", 50.0)
        assert dict(got.metadata) == dict(want.metadata)


def test_samples_are_interleaved_frame_by_frame(tmp_path: Path) -> None:
    sf.write_sigmf_channels(
        tmp_path / "i", [sf.Signal(np.array([1.0, 2.0]), 10), sf.Signal(np.array([3.0, 4.0]), 10)]
    )
    assert (tmp_path / "i.sigmf-data").read_bytes() == struct.pack("<4d", 1, 3, 2, 4)
    glob = _meta(tmp_path / "i.sigmf-meta")["global"]
    assert glob["core:num_channels"] == 2
    keys = list(glob)
    assert keys.index("core:num_channels") == keys.index("core:sample_rate") + 1


def test_reading_takes_every_nth_sample(tmp_path: Path) -> None:
    (tmp_path / "t.sigmf-data").write_bytes(struct.pack("<6h", 1, 2, 3, 4, 5, 6))
    glob = {"core:datatype": "ri16_le", "core:version": "1.0.0", "core:sample_rate": 1}
    glob["core:num_channels"] = 3
    (tmp_path / "t.sigmf-meta").write_text(json.dumps({"global": glob}), encoding="utf-8")
    got = [list(s.samples * 32768) for s in sf.read_sigmf_channels(tmp_path / "t")]
    assert got == [[1, 4], [2, 5], [3, 6]]


def test_one_channel_writes_the_write_sigmf_files(tmp_path: Path) -> None:
    s = _channel([0.5 + 1j, -0.25])
    sf.write_sigmf(tmp_path / "a", s, "cf32_le")
    sf.write_sigmf_channels(tmp_path / "b", [s], "cf32_le")
    for ext in (".sigmf-meta", ".sigmf-data"):
        assert (tmp_path / f"a{ext}").read_bytes() == (tmp_path / f"b{ext}").read_bytes()
    assert "core:num_channels" not in _meta(tmp_path / "b.sigmf-meta")["global"]
    [r] = sf.read_sigmf_channels(tmp_path / "a")
    np.testing.assert_array_equal(r.samples, sf.read_sigmf(tmp_path / "a").samples)


def test_read_sigmf_refuses_several_channels(tmp_path: Path) -> None:
    sf.write_sigmf_channels(
        tmp_path / "two", [sf.Signal(np.array([1.0]), 1), sf.Signal(np.array([2.0]), 1)]
    )
    with pytest.raises(ValueError, match="read_sigmf_channels"):
        sf.read_sigmf(tmp_path / "two")


def test_each_channel_has_its_own_metadata(tmp_path: Path) -> None:
    sf.write_sigmf_channels(tmp_path / "m", [_channel([1.0]), _channel([2.0])])
    a, b = sf.read_sigmf_channels(tmp_path / "m")
    assert a.metadata["core:annotations"] == b.metadata["core:annotations"]
    assert a.metadata["core:annotations"] is not b.metadata["core:annotations"]
    a.metadata["core:annotations"][0]["core:label"] = "changed"
    assert b.metadata["core:annotations"][0]["core:label"] == "burst"


def test_the_most_channels_are_read(tmp_path: Path) -> None:
    glob = {"core:datatype": "ri8", "core:version": "1.0.0", "core:sample_rate": 1}
    glob["core:num_channels"] = MAX_CHANNELS
    (tmp_path / "w.sigmf-meta").write_text(json.dumps({"global": glob}), encoding="utf-8")
    (tmp_path / "w.sigmf-data").write_bytes(b"")
    assert len(sf.read_sigmf_channels(tmp_path / "w")) == MAX_CHANNELS


@pytest.mark.parametrize(
    "channels",
    [
        [],
        [_channel([1.0]), _channel([1j])],
        [_channel([1.0]), _channel([1.0, 2.0])],
        [_channel([1.0]), sf.Signal(np.array([1.0]), 2e6)],
        [_channel([1.0]), _channel([1.0], units="A")],
        [_channel([1.0]), _channel([1.0], impedance=75.0)],
        [_channel([1.0]), _channel([1.0], time_origin=0.0)],
        [_channel([1.0]), _channel([1.0], center_frequency=0.0)],
        [_channel([1.0], metadata={"run": 1}), _channel([1.0], metadata={"run": 1.0})],
        [_channel([1.0], metadata={"run": 1}), _channel([1.0], metadata={"run": 1, "x:y": 2})],
        [_channel([1.0]), [1.0]],
    ],
)
def test_bad_channel_lists_are_rejected(tmp_path: Path, channels: Any) -> None:
    sf.write_sigmf(tmp_path / "keep", sf.Signal(np.array([0.5]), 1))
    before = (tmp_path / "keep.sigmf-meta").read_bytes()
    with pytest.raises(ValueError):
        sf.write_sigmf_channels(tmp_path / "keep", channels)
    assert (tmp_path / "keep.sigmf-meta").read_bytes() == before


def test_a_signal_alone_is_not_a_list(tmp_path: Path) -> None:
    bad: Any = sf.Signal(np.array([1.0]), 1)
    with pytest.raises(ValueError, match="list of signals"):
        sf.write_sigmf_channels(tmp_path / "s", bad)


def test_too_many_channels_are_rejected(tmp_path: Path) -> None:
    one = sf.Signal(np.zeros(0), 1)
    with pytest.raises(ValueError, match="65535"):
        sf.write_sigmf_channels(tmp_path / "x", [one] * (MAX_CHANNELS + 1))
    assert not (tmp_path / "x.sigmf-meta").exists()
