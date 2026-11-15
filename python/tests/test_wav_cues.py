"""WAV cue points, their LIST/adtl labels and regions (conventions: Signal files, WAV; ADR 0094,
0095)."""

from __future__ import annotations

import struct
import wave
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from signalforge import Signal, read_wav, read_wav_cues, read_wav_info, write_wav

TONE = Signal(np.array([0.5, -0.25, 0.0, 0.125]), 8000.0)


def test_round_trip_keeps_order_positions_and_labels(tmp_path: Path) -> None:
    printable = "".join(chr(c) for c in range(0x20, 0x7F))
    cues = [(4, 0, "end"), (0, 4, ""), (2, 0, printable), (2, 2, "again"), (1, 1, "")]
    path = tmp_path / "c.wav"
    write_wav(path, TONE, "i16", cues=cues)
    assert read_wav_cues(path) == cues


@pytest.mark.parametrize("fmt", ["u8", "i16", "i24", "f32", "f64"])
def test_cues_leave_the_audio_and_tags_alone(tmp_path: Path, fmt: str) -> None:
    plain, marked = tmp_path / "plain.wav", tmp_path / "marked.wav"
    odd = Signal(TONE.samples[:3], 8000.0)  # odd data sizes for u8 and i24
    write_wav(plain, [odd, odd], fmt, {"INAM": "tone"})
    write_wav(marked, [odd, odd], fmt, {"INAM": "tone"}, [(1, 2, "one"), (3, 0, "")])
    a, b = read_wav(plain), read_wav(marked)
    assert all(np.array_equal(x.samples, y.samples) for x, y in zip(a, b, strict=True))
    assert read_wav_info(marked) == {"INAM": "tone"}
    assert read_wav_cues(marked) == [(1, 2, "one"), (3, 0, "")]
    raw = marked.read_bytes()
    assert struct.unpack_from("<I", raw, 4)[0] == len(raw) - 8


def test_no_or_empty_cues_write_a_plain_file(tmp_path: Path) -> None:
    write_wav(tmp_path / "a.wav", TONE, "i16")
    write_wav(tmp_path / "b.wav", TONE, "i16", cues=[])
    assert (tmp_path / "a.wav").read_bytes() == (tmp_path / "b.wav").read_bytes()
    assert read_wav_cues(tmp_path / "a.wav") == []


def test_the_wave_module_still_reads_the_frames(tmp_path: Path) -> None:
    path = tmp_path / "c.wav"
    write_wav(path, TONE, "i16", cues=[(0, 4, "a"), (4, 0, "b")])
    with wave.open(str(path)) as w:
        got = np.frombuffer(w.readframes(w.getnframes()), "<i2")
    assert got.tolist() == [16384, -8192, 0, 4096]


def test_numpy_integer_positions_are_accepted(tmp_path: Path) -> None:
    path = tmp_path / "c.wav"
    # typed as int, accepted as NumPy too
    cues: Any = [
        (np.int64(3), np.int32(1), "x"),
        (np.uint8(1), 0, ""),
    ]
    write_wav(path, TONE, "i16", cues=cues)
    assert read_wav_cues(path) == [(3, 1, "x"), (1, 0, "")]


@pytest.mark.parametrize(
    "cues",
    [
        [(True, 0, "")],
        [(1.0, 0, "")],
        [("1", 0, "")],
        [(-1, 0, "")],
        [(5, 0, "")],
        [(0, False, "")],
        [(0, 1.0, "")],
        [(0, -1, "")],
        [(1, 4, "")],
        [(4, 1, "")],
        [(0, 0, b"x")],
        [(0, 0, None)],
        [(0, 0, "caf\u00e9")],
        [(0, 0, "\t")],
        [(0, "")],
        [(0, 0, "", "")],
        [0],
        "ab",
        {0: "x"},
        b"\x00",
    ],
)
def test_bad_cues_are_rejected(tmp_path: Path, cues: Any) -> None:
    with pytest.raises(ValueError, match="cue"):
        write_wav(tmp_path / "c.wav", TONE, "i16", cues=cues)
    assert not (tmp_path / "c.wav").exists()


def test_a_region_is_one_ltxt_after_its_labl(tmp_path: Path) -> None:
    path = tmp_path / "r.wav"
    write_wav(path, TONE, "i16", cues=[(1, 3, "ab")])
    raw = path.read_bytes()
    want = b"adtl" + b"labl" + struct.pack("<II", 7, 1) + b"ab\0\0"
    want += b"ltxt" + struct.pack("<III4s4H", 20, 1, 3, b"rgn ", 0, 0, 0, 0)
    assert raw[raw.index(b"adtl") :] == want


def test_a_file_that_is_not_wave_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "x.wav"
    path.write_bytes(b"RIFF\x04\x00\x00\x00WAV")
    with pytest.raises(ValueError, match="RIFF WAVE"):
        read_wav_cues(path)
