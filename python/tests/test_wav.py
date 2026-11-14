"""WAV files (conventions: Signal files, WAV; ADR 0055)."""

from __future__ import annotations

import math
import wave
from pathlib import Path

import numpy as np
import pytest

from signalforge import Signal, read_wav, write_wav

FORMATS = {"u8": 8, "i16": 16, "i24": 24, "i32": 32, "f32": 32, "f64": 64}


@pytest.mark.parametrize("fmt", FORMATS)
@pytest.mark.parametrize("nch", [1, 2, 5])
def test_round_trip(tmp_path: Path, fmt: str, nch: int) -> None:
    rng = np.random.default_rng(nch)
    bits = FORMATS[fmt]
    x = rng.uniform(-1, 1 - 2.0 ** (1 - bits), (nch, 101))
    if fmt[0] != "f":  # values on the integer grid survive exactly
        x = np.rint(x * 2.0 ** (bits - 1)) / 2.0 ** (bits - 1)
    elif fmt == "f32":
        x = x.astype(np.float32).astype(np.float64)
    path = tmp_path / "x.wav"
    write_wav(path, [Signal(row, 48000.0) for row in x], fmt)
    got = read_wav(path)
    assert len(got) == nch
    for row, s in zip(x, got, strict=True):
        assert np.array_equal(s.samples, row)
        assert s.sample_rate == 48000.0
        assert s.units == "FS"
        assert s.time_origin == 0.0 and s.center_frequency == 0.0 and not s.metadata


@pytest.mark.parametrize("fmt", ["u8", "i16", "i24", "i32"])
def test_python_wave_module_reads_it(tmp_path: Path, fmt: str) -> None:
    bits = FORMATS[fmt]
    x = np.array([[0.5, -0.25, -1.0, 0.0], [0.125, 0.75, 0.0, -0.5]])
    path = tmp_path / "x.wav"
    write_wav(path, [Signal(row, 22050) for row in x], fmt)
    with wave.open(str(path)) as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (2, bits // 8, 22050)
        raw = w.readframes(w.getnframes())
    width = bits // 8
    codes = [
        int.from_bytes(raw[i : i + width], "little", signed=fmt != "u8")
        for i in range(0, len(raw), width)
    ]
    if fmt == "u8":
        codes = [c - 128 for c in codes]
    want = np.rint(x.T.reshape(-1) * 2.0 ** (bits - 1)).astype(int).tolist()
    assert codes == want


def test_one_signal_and_floats_keep_non_finite(tmp_path: Path) -> None:
    path = tmp_path / "x.wav"
    write_wav(path, Signal(np.array([math.nan, math.inf, -math.inf, 3.0]), 1000))  # default f32
    (s,) = read_wav(path)
    assert np.isnan(s.samples[0]) and s.samples[1] == math.inf and s.samples[2] == -math.inf
    assert s.samples[3] == 3.0


def test_rejected_write_leaves_the_file(tmp_path: Path) -> None:
    path = tmp_path / "x.wav"
    write_wav(path, Signal(np.array([0.5]), 1000), "i16")
    before = path.read_bytes()
    with pytest.raises(ValueError, match="range"):
        write_wav(path, Signal(np.array([1.0]), 1000), "i16")
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    ("channels", "fmt", "match"),
    [
        (Signal(np.array([0j]), 1000), "f32", "real"),
        ([Signal(np.array([0.0]), 1000), Signal(np.array([0.0, 0.0]), 1000)], "f32", "same"),
        ([Signal(np.array([0.0]), 1000), Signal(np.array([0.0]), 2000)], "f32", "same"),
        ([], "f32", "channels"),
        ([np.zeros(3)], "f32", "channels"),
        (Signal(np.array([math.nan]), 1000), "i16", "non-finite"),
        (Signal(np.array([0.0]), 1000.5), "i16", "whole"),
        ([Signal(np.array([0.0]), 1000)] * 8192, "f64", "block align"),
        (Signal(np.array([0.0]), 1000), "pcm16", "format"),
        (Signal(np.array([0.0]), 1000), 16, "format"),
    ],
)
def test_bad_writes(tmp_path: Path, channels: object, fmt: object, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        write_wav(tmp_path / "x.wav", channels, fmt)  # type: ignore[arg-type]
    assert not (tmp_path / "x.wav").exists()


def test_largest_block_align(tmp_path: Path) -> None:
    path = tmp_path / "x.wav"
    write_wav(path, [Signal(np.array([0.5]), 1)] * 8191, "f64")  # 65528 bytes per frame
    got = read_wav(path)
    assert len(got) == 8191 and got[-1].samples.tolist() == [0.5]


def test_missing_file_is_an_os_error(tmp_path: Path) -> None:
    with pytest.raises(OSError):
        read_wav(tmp_path / "missing.wav")
