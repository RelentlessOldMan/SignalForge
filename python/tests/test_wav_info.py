"""WAV LIST/INFO text tags (conventions: Signal files, WAV; ADR 0091)."""

from __future__ import annotations

import string
import struct
import wave
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from signalforge import Signal, read_wav, read_wav_info, write_wav

TONE = Signal(np.array([0.5, -0.25, 0.0, 0.125]), 8000.0)


def test_round_trip_keeps_order_and_every_printable_character(tmp_path: Path) -> None:
    printable = "".join(chr(c) for c in range(0x20, 0x7F))
    tags = {"ISFT": "SignalForge", "ICMT": printable, "INAM": "", "IAR1": "x" * 255, "ZZZZ": "ab"}
    path = tmp_path / "t.wav"
    write_wav(path, TONE, "i16", tags)
    got = read_wav_info(path)
    assert list(got.items()) == list(tags.items())


@pytest.mark.parametrize("fmt", ["u8", "i16", "i24", "f32", "f64"])
def test_tags_leave_the_audio_alone(tmp_path: Path, fmt: str) -> None:
    plain, tagged = tmp_path / "plain.wav", tmp_path / "tagged.wav"
    odd = Signal(TONE.samples[:3], 8000.0)  # odd data sizes for u8 and i24
    write_wav(plain, [odd, odd], fmt)
    write_wav(tagged, [odd, odd], fmt, {"INAM": "tone"})
    a, b = read_wav(plain), read_wav(tagged)
    assert all(np.array_equal(x.samples, y.samples) for x, y in zip(a, b, strict=True))
    raw = tagged.read_bytes()
    assert raw.startswith(plain.read_bytes()[:4])
    assert raw[8:].startswith(plain.read_bytes()[8:])  # the tags only add bytes at the end
    assert struct.unpack_from("<I", raw, 4)[0] == len(raw) - 8


def test_wave_module_reads_tagged_pcm(tmp_path: Path) -> None:
    path = tmp_path / "t.wav"
    write_wav(path, TONE, "i16", {"INAM": "Test tone", "ICMT": "odd"})
    with wave.open(str(path)) as w:
        frames = w.readframes(w.getnframes())
    assert struct.unpack("<4h", frames) == (16384, -8192, 0, 4096)


def test_no_or_empty_info_writes_the_plain_file(tmp_path: Path) -> None:
    a, b = tmp_path / "a.wav", tmp_path / "b.wav"
    write_wav(a, TONE, "f32")
    write_wav(b, TONE, "f32", {})
    assert a.read_bytes() == b.read_bytes()
    assert read_wav_info(a) == {}


def test_reads_a_file_from_the_wave_module(tmp_path: Path) -> None:
    path = tmp_path / "w.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(1000)
        w.writeframes(b"\0\0\1\0")
    assert read_wav_info(path) == {}


def test_random_tags_round_trip(tmp_path: Path) -> None:
    rng = np.random.default_rng(91)
    alphabet = string.ascii_uppercase + string.digits
    path = tmp_path / "r.wav"
    for _ in range(20):
        ids = {"".join(rng.choice(list(alphabet), 4)) for _ in range(rng.integers(1, 8))}
        tags = {
            i: "".join(chr(c) for c in rng.integers(0x20, 0x7F, rng.integers(0, 40))) for i in ids
        }
        write_wav(path, TONE, "i16", tags)
        assert list(read_wav_info(path).items()) == list(tags.items())
        assert np.array_equal(read_wav(path)[0].samples, TONE.samples)


@pytest.mark.parametrize("cid", ["inam", "NAM", "INAME", "ID3 ", "", "IN-M", "INAÉ", 1234])
def test_rejects_bad_ids(tmp_path: Path, cid: Any) -> None:
    with pytest.raises(ValueError, match="info ID"):
        write_wav(tmp_path / "x.wav", TONE, "i16", {cid: "x"})
    assert not (tmp_path / "x.wav").exists()


@pytest.mark.parametrize("text", ["café", "a\nb", "a\tb", "a\0b", "\x7f", None, 3])
def test_rejects_bad_text(tmp_path: Path, text: Any) -> None:
    with pytest.raises(ValueError, match="printable ASCII"):
        write_wav(tmp_path / "x.wav", TONE, "i16", {"ICMT": text})


def test_rejects_info_that_is_not_a_mapping(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="mapping"):
        write_wav(tmp_path / "x.wav", TONE, "i16", [("INAM", "x")])  # type: ignore[arg-type]


@pytest.mark.parametrize("raw", [b"", b"RIFF\0\0\0\0WAV", b"RIFX\4\0\0\0WAVE", b"RIFF\4\0\0\0AVI "])
def test_rejects_files_that_are_not_wave(tmp_path: Path, raw: bytes) -> None:
    path = tmp_path / "x.wav"
    path.write_bytes(raw)
    with pytest.raises(ValueError, match="not a RIFF WAVE"):
        read_wav_info(path)
