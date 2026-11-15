"""Signal files: raw sample encoding, SigMF-layout recordings, WAV and NumPy .npy files
(conventions: Signal files)."""

from __future__ import annotations

import copy
import itertools
import json
import math
import os
import re
import struct
import zlib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from ._checks import real
from .core import Signal

SIGMF_VERSION = "1.2.0"
_DATATYPE = re.compile(r"([cr])(f64|f32|f16|[iu]32|[iu]16|[iu]8)(?:_(le|be))?")
_CODES = {
    "f64": "f8",
    "f32": "f4",
    "f16": "f2",
    "i32": "i4",
    "i16": "i2",
    "i8": "i1",
    "u32": "u4",
    "u16": "u2",
    "u8": "u1",
}
_RESERVED = frozenset(
    {
        "core:datatype",
        "core:version",
        "core:sample_rate",
        "core:extensions",
        "core:num_channels",
        "core:dataset",
        "core:metadata_only",
    }
)
_EXTENSION = {"name": "signalforge", "version": "1.0.0", "optional": True}
MAX_DEPTH = 64
"""Deepest nesting of objects and arrays in a ``.sigmf-meta`` file; the top object is level 1."""
MAX_CHANNELS = 65535
"""Most channels in one SigMF recording (``core:num_channels``)."""
_INT64 = (-(2**63), 2**63 - 1)


def _parse(datatype: str) -> tuple[bool, np.dtype[Any], int]:
    """``(is_complex, element dtype in its byte order, integer bits or 0)``."""
    m = _DATATYPE.fullmatch(datatype) if isinstance(datatype, str) else None
    if m is None or (m[2][1:] == "8") != (m[3] is None):
        raise ValueError(f"unknown datatype {datatype!r}")
    order = {"le": "<", "be": ">", None: "|"}[m[3]]
    bits = int(m[2][1:]) if m[2][0] in "iu" else 0
    return m[1] == "c", np.dtype(order + _CODES[m[2]]), bits


def encode_samples(x: ArrayLike, datatype: str) -> bytes:
    """The raw bytes of ``x`` as ``datatype`` (interleaved I/Q for complex types)."""
    is_complex, dt, bits = _parse(datatype)
    a = np.asarray(x)
    if a.ndim != 1 or a.dtype.kind not in "fiuc":
        raise ValueError("x must be a 1-D numeric array")
    if bool(np.iscomplexobj(a)) != is_complex:
        raise ValueError(f"{datatype} needs {'complex' if is_complex else 'real'} samples")
    parts = a.astype(np.complex128).view(np.float64) if is_complex else a.astype(np.float64)
    if not bits:
        with np.errstate(over="ignore"):
            return parts.astype(dt).tobytes()
    if not np.all(np.isfinite(parts)):
        raise ValueError(f"{datatype} cannot hold non-finite samples")
    codes = np.rint(parts * 2.0 ** (bits - 1))
    if codes.size and (codes.min() < -(2 ** (bits - 1)) or codes.max() > 2 ** (bits - 1) - 1):
        raise ValueError(f"a sample is outside the range of {datatype} (full scale is 1.0)")
    if dt.kind == "u":  # offset binary
        codes += 2.0 ** (bits - 1)
    return codes.astype(dt).tobytes()


def decode_samples(
    data: bytes | bytearray | memoryview, datatype: str
) -> NDArray[np.complex128] | NDArray[np.float64]:
    """Samples from the raw bytes of ``datatype``, as ``float64`` or ``complex128``."""
    is_complex, dt, bits = _parse(datatype)
    if not isinstance(data, bytes | bytearray | memoryview):
        raise ValueError("data must be bytes")
    size = dt.itemsize * (2 if is_complex else 1)
    nbytes = memoryview(data).nbytes
    if nbytes % size:
        raise ValueError(f"{nbytes} bytes is not a whole number of {datatype} samples")
    parts = np.frombuffer(data, dtype=dt).astype(np.float64)
    if dt.kind == "u":  # offset binary
        parts -= 2.0 ** (bits - 1)
    if bits:
        parts /= 2.0 ** (bits - 1)
    if not is_complex:
        return parts
    z = np.empty(parts.size // 2, dtype=np.complex128)
    z.real, z.imag = parts[0::2], parts[1::2]
    return z


def _base(path: str | os.PathLike[str]) -> Path:
    p = Path(os.fspath(path))
    return p.with_suffix("") if p.suffix in (".sigmf-meta", ".sigmf-data") else p


def _files(path: str | os.PathLike[str]) -> tuple[Path, Path]:
    base = _base(path)
    return base.with_name(base.name + ".sigmf-meta"), base.with_name(base.name + ".sigmf-data")


def _text(s: str, where: str) -> str:
    try:
        s.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError(f"{where}: not valid Unicode (a lone surrogate)") from None
    return s


def _json(v: Any, where: str, depth: int = 1) -> Any:
    """``v`` as plain JSON data within the limits of conventions: Signal files, or ValueError.

    ``depth`` is the level an object or array ``v`` would sit at.
    """
    if isinstance(v, np.generic):
        v = v.item()
    if v is None or isinstance(v, bool):
        return v
    if isinstance(v, str):
        return _text(v, where)
    if isinstance(v, int):
        if not _INT64[0] <= v <= _INT64[1]:
            raise ValueError(f"{where}: integer outside the signed 64-bit range")
        return v
    if isinstance(v, float):
        if not math.isfinite(v):
            raise ValueError(f"{where}: JSON cannot hold {v}")
        return v
    if isinstance(v, list | tuple | Mapping) and depth > MAX_DEPTH:
        raise ValueError(f"{where}: nested deeper than {MAX_DEPTH} levels")
    if isinstance(v, list | tuple):
        return [_json(x, f"{where}[{i}]", depth + 1) for i, x in enumerate(v)]
    if isinstance(v, Mapping):
        if not all(isinstance(k, str) for k in v):
            raise ValueError(f"{where}: object keys must be strings")
        return {_text(k, where): _json(x, f"{where}.{k}", depth + 1) for k, x in v.items()}
    raise ValueError(f"{where}: {type(v).__name__} is not JSON data")


def _finite(v: float, what: str) -> float:
    return real(v, what)


_ANNOTATIONS = "core:annotations"


def _annotations(v: Any, what: str) -> list[dict[str, Any]]:
    """``v`` checked as a SigMF annotations list (conventions: Signal files, Annotations)."""
    if not isinstance(v, list):
        raise ValueError(f"{what} must be a JSON array")
    last = 0
    for i, a in enumerate(v):
        a = _object(a, f"{what}[{i}]")
        for k in ("core:sample_start", "core:sample_count"):
            if k == "core:sample_start" or k in a:
                n = a.get(k)
                if not isinstance(n, int) or isinstance(n, bool) or n < 0:
                    raise ValueError(f"{what}[{i}] {k} must be an integer >= 0")
        if a["core:sample_start"] < last:
            raise ValueError(f"{what} must be sorted by core:sample_start")
        last = a["core:sample_start"]
    return v


def write_sigmf(path: str | os.PathLike[str], signal: Signal, datatype: str | None = None) -> None:
    """Write ``signal`` as ``<base>.sigmf-data`` and ``<base>.sigmf-meta``. ``datatype`` defaults
    to ``cf64_le`` or ``rf64_le``, which lose nothing."""
    write_sigmf_channels(path, [signal], datatype)


def write_sigmf_channels(
    path: str | os.PathLike[str], channels: Sequence[Signal], datatype: str | None = None
) -> None:
    """Write ``channels``, one signal per channel, as one interleaved SigMF recording. They must
    have one kind, one length and identical metadata (rate, frequency, time origin, units,
    impedance and metadata); ``datatype`` defaults as for :func:`write_sigmf`."""
    if isinstance(channels, Signal) or not isinstance(channels, Sequence):
        raise ValueError("channels must be a list of signals")
    if not 1 <= len(channels) <= MAX_CHANNELS:
        raise ValueError(f"a recording needs 1 to {MAX_CHANNELS} channels, not {len(channels)}")
    if not all(isinstance(s, Signal) for s in channels):
        raise ValueError("channels must be a list of signals")
    first = channels[0]
    if any(s.is_complex != first.is_complex for s in channels):
        raise ValueError("the channels must be all real or all complex")
    if any(len(s.samples) != len(first.samples) for s in channels):
        raise ValueError("the channels must have the same number of samples")
    if datatype is None:
        datatype = "cf64_le" if first.is_complex else "rf64_le"
    frames = np.stack([s.samples for s in channels], axis=1).reshape(-1)
    data = encode_samples(frames, datatype)
    text = _sigmf_text(first, datatype, len(channels))
    for s in channels[1:]:
        if _sigmf_text(s, datatype, len(channels)) != text:
            raise ValueError(
                "the channels must have the same sample rate, center frequency, time origin, "
                "units, impedance and metadata"
            )
    meta_path, data_path = _files(path)
    data_path.write_bytes(data)  # only once nothing above can fail
    meta_path.write_bytes(text.encode("utf-8"))


def write_sigmf_captures(
    path: str | os.PathLike[str], segments: Sequence[Signal], datatype: str | None = None
) -> None:
    """Write ``segments`` as one one-channel SigMF recording with one capture per segment, the
    inverse of :func:`read_sigmf_captures` (conventions: Signal files, Captures; ADR 0100). Each
    later time origin must be exactly the first's plus ``start / sample_rate``, and everything but
    the center frequency, time origin and annotations must be identical."""
    if isinstance(segments, Signal) or not isinstance(segments, Sequence) or not segments:
        raise ValueError("segments must be a non-empty list of signals")
    if not all(isinstance(s, Signal) for s in segments):
        raise ValueError("segments must be a non-empty list of signals")
    first = segments[0]
    if any(s.is_complex != first.is_complex for s in segments):
        raise ValueError("the segments must be all real or all complex")
    if any(len(s.samples) == 0 for s in segments[:-1]):
        raise ValueError("only the last segment may be empty")
    if datatype is None:
        datatype = "cf64_le" if first.is_complex else "rf64_le"
    t0 = _finite(first.time_origin, "time_origin")
    shared = _sigmf_text(first, datatype, 1, (0.0, [], []))
    rate = float(first.sample_rate)
    captures: list[dict[str, Any]] = []
    annotations: list[dict[str, Any]] = []
    start = 0
    for j, s in enumerate(segments):
        if j and _sigmf_text(s, datatype, 1, (0.0, [], [])) != shared:
            raise ValueError(
                "the segments must have the same sample rate, units, impedance and metadata "
                "apart from annotations"
            )
        if j and s.time_origin != t0 + start / rate:
            raise ValueError(
                f"segment {j} must have time origin {t0 + start / rate!r} "
                f"(the first's plus {start} / sample_rate), not {s.time_origin!r}"
            )
        n = len(s.samples)
        mine = _json(s.metadata.get(_ANNOTATIONS, []), "metadata")
        if j < len(segments) - 1 and any(a["core:sample_start"] >= n for a in mine):
            raise ValueError(f"an annotation of segment {j} starts past its {n} samples")
        annotations += [{**a, "core:sample_start": a["core:sample_start"] + start} for a in mine]
        captures.append(
            {
                "core:sample_start": start,
                "core:frequency": _finite(s.center_frequency, "center_frequency"),
            }
        )
        start += n
    data = encode_samples(np.concatenate([s.samples for s in segments]), datatype)
    text = _sigmf_text(first, datatype, 1, (t0, captures, annotations))
    meta_path, data_path = _files(path)
    data_path.write_bytes(data)  # only once nothing above can fail
    meta_path.write_bytes(text.encode("utf-8"))


_Layout = tuple[float, list[dict[str, Any]], list[dict[str, Any]]]


def _sigmf_text(signal: Signal, datatype: str, channels: int, layout: _Layout | None = None) -> str:
    """The ``.sigmf-meta`` text for ``signal`` (one of ``channels``), checked. ``layout`` replaces
    its time origin, captures and annotations (its own annotations are still checked)."""
    glob: dict[str, Any] = {
        "core:datatype": datatype,
        "core:version": SIGMF_VERSION,
        "core:sample_rate": float(signal.sample_rate),
    }
    if channels > 1:
        glob["core:num_channels"] = channels
    glob["core:extensions"] = [dict(_EXTENSION)]
    glob["signalforge:time_origin"] = (
        _finite(signal.time_origin, "time_origin") if layout is None else layout[0]
    )
    if signal.units is not None:
        if not isinstance(signal.units, str):
            raise ValueError("units must be a string")
        glob["signalforge:units"] = signal.units
    if signal.impedance is not None:
        glob["signalforge:impedance"] = float(signal.impedance)
    meta = _json(signal.metadata, "metadata", depth=-MAX_DEPTH)  # depth checked on doc below
    plain = {k: v for k, v in meta.items() if ":" not in k}
    if plain:
        glob["signalforge:metadata"] = plain
    annotations = _annotations(meta.pop(_ANNOTATIONS, []), f"metadata {_ANNOTATIONS}")
    for k, v in meta.items():
        if ":" in k:
            if k in _RESERVED or k.startswith("signalforge:"):
                raise ValueError(f"metadata key {k!r} is reserved")
            glob[k] = v
    if layout is None:
        frequency = _finite(signal.center_frequency, "center_frequency")
        captures = [{"core:sample_start": 0, "core:frequency": frequency}]
    else:
        captures, annotations = layout[1], layout[2]
    doc = _json({"global": glob, "captures": captures, "annotations": annotations}, "the metadata")
    return json.dumps(doc, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate JSON key {k!r}")
        out[k] = v
    return out


def _no_constant(name: str) -> Any:
    raise ValueError(f"{name} is not JSON")


def _integer(v: Any, n: int) -> bool:
    """Whether ``v`` is the JSON integer ``n`` (not ``n.0``, not a bool)."""
    return type(v) is int and v == n


def _object(v: Any, what: str) -> dict[str, Any]:
    if not isinstance(v, dict):
        raise ValueError(f"{what} must be a JSON object")
    return v


def read_sigmf(path: str | os.PathLike[str]) -> Signal:
    """Read a ``.sigmf-meta`` / ``.sigmf-data`` pair as a :class:`Signal`."""
    return _read_sigmf(path, "one")[0]


def read_sigmf_channels(path: str | os.PathLike[str]) -> list[Signal]:
    """Read a SigMF recording of any number of channels as one :class:`Signal` per channel."""
    return _read_sigmf(path, "channels")


def read_sigmf_captures(path: str | os.PathLike[str]) -> list[Signal]:
    """Read a one-channel SigMF recording as one :class:`Signal` per capture, each with its
    capture's center frequency and a time origin moved to the capture's first sample."""
    return _read_sigmf(path, "captures")


def _read_sigmf(path: str | os.PathLike[str], mode: str) -> list[Signal]:
    """``mode`` is ``"one"`` (read_sigmf), ``"channels"`` or ``"captures"``."""
    meta_path, data_path = _files(path)
    try:
        parsed = json.loads(
            meta_path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique,
            parse_constant=_no_constant,
        )
    except RecursionError:
        raise ValueError(f"the metadata is nested deeper than {MAX_DEPTH} levels") from None
    doc = _object(_json(parsed, "the metadata"), "the metadata")
    glob = _object(doc.get("global"), "global")
    datatype = glob.get("core:datatype")
    if not isinstance(datatype, str):
        raise ValueError("core:datatype is required")
    version = glob.get("core:version")
    if not isinstance(version, str) or not version.startswith("1."):
        raise ValueError(f"unsupported core:version {version!r}")
    rate = _finite(glob.get("core:sample_rate"), "core:sample_rate")  # type: ignore[arg-type]
    n = glob.get("core:num_channels", 1)
    if mode != "channels" and not _integer(n, 1):
        reader = "read_sigmf" if mode == "one" else "read_sigmf_captures"
        raise ValueError(f"{reader} reads one channel; read_sigmf_channels reads more")
    if type(n) is not int or not 1 <= n <= MAX_CHANNELS:
        raise ValueError(f"core:num_channels must be a whole number from 1 to {MAX_CHANNELS}")
    for k in ("core:dataset", "core:metadata_only"):
        if k in glob:
            raise ValueError(f"{k} recordings are not supported")
    captures = doc.get("captures", [])
    if not isinstance(captures, list):
        raise ValueError("captures must be a JSON array")
    freqs: list[float] = []
    starts: list[int] = []
    for i, c in enumerate(captures):
        c = _object(c, f"captures[{i}]")
        if not _integer(c.get("core:header_bytes", 0), 0):
            raise ValueError("captures with header bytes are not supported")
        freqs.append(_finite(c.get("core:frequency", 0), f"captures[{i}] core:frequency"))
        if mode == "captures":
            start = c.get("core:sample_start")
            if type(start) is not int or start < 0:
                raise ValueError(f"captures[{i}] core:sample_start must be an integer, at least 0")
            starts.append(start)
    if mode != "captures" and len(set(freqs)) > 1:
        raise ValueError(
            "captures at different frequencies are not one signal; read_sigmf_captures reads them"
        )
    if _ANNOTATIONS in glob:
        raise ValueError(f"{_ANNOTATIONS} belongs at the top level, not in global")
    annotations = _annotations(doc.get("annotations", []), "annotations")
    units = glob.get("signalforge:units")
    if units is not None and not isinstance(units, str):
        raise ValueError("signalforge:units must be a string")
    impedance = glob.get("signalforge:impedance")
    metadata = dict(_object(glob.get("signalforge:metadata", {}), "signalforge:metadata"))
    metadata.update(
        {k: v for k, v in glob.items() if k not in _RESERVED and not k.startswith("signalforge:")}
    )
    if annotations:
        metadata[_ANNOTATIONS] = annotations
    frequency = freqs[0] if freqs else 0.0
    time_origin = _finite(glob.get("signalforge:time_origin", 0.0), "signalforge:time_origin")
    ohms = None if impedance is None else _finite(impedance, "signalforge:impedance")
    samples = decode_samples(data_path.read_bytes(), datatype)
    if mode == "captures":
        if not starts:
            starts, freqs = [0], [0.0]
        if starts[0] != 0:
            raise ValueError("the first capture must start at sample 0")
        if any(b <= a for a, b in itertools.pairwise(starts)):
            raise ValueError("each capture must start after the one before")
        if starts[-1] > len(samples):
            raise ValueError(f"a capture starts past the last of {len(samples)} samples")
        shared = {k: v for k, v in metadata.items() if k != _ANNOTATIONS}
        ends = [*starts[1:], len(samples)]
        segments = []
        for j, (a, b) in enumerate(zip(starts, ends, strict=True)):
            last = j == len(starts) - 1
            mine = [
                {**x, "core:sample_start": x["core:sample_start"] - a}
                for x in annotations
                if a <= x["core:sample_start"] and (last or x["core:sample_start"] < b)
            ]
            md = copy.deepcopy(shared)
            if mine:
                md[_ANNOTATIONS] = copy.deepcopy(mine)
            segments.append(
                Signal(
                    samples[a:b].copy(),
                    rate,
                    center_frequency=freqs[j],
                    time_origin=time_origin + a / rate,
                    units=units,
                    impedance=ohms,
                    metadata=md,
                )
            )
        return segments
    if len(samples) % n:
        raise ValueError(f"{len(samples)} samples is not a whole number of {n}-channel frames")
    frames = samples.reshape(-1, n)
    return [
        Signal(
            np.ascontiguousarray(frames[:, c]),
            rate,
            center_frequency=frequency,
            time_origin=time_origin,
            units=units,
            impedance=ohms,
            metadata=copy.deepcopy(metadata),
        )
        for c in range(n)
    ]


_WAV_BITS = {"u8": 8, "i16": 16, "i24": 24, "i32": 32, "f32": 32, "f64": 64}
_WAV_FORMATS = {1: {8: "u8", 16: "i16", 24: "i24", 32: "i32"}, 3: {32: "f32", 64: "f64"}}
_GUID_TAIL = bytes.fromhex("000000001000800000aa00389b71")
_U32 = 2**32 - 1


def _chunk(cid: bytes, body: bytes) -> bytes:
    return cid + struct.pack("<I", len(body)) + body + b"\0" * (len(body) % 2)


def _wav_encode(x: NDArray[np.float64], fmt: str) -> bytes:
    if fmt == "f32":
        with np.errstate(over="ignore"):
            return x.astype("<f4").tobytes()
    if fmt == "f64":
        return x.astype("<f8").tobytes()
    bits = _WAV_BITS[fmt]
    if not np.all(np.isfinite(x)):
        raise ValueError(f"{fmt} cannot hold non-finite samples")
    codes = np.rint(x * 2.0 ** (bits - 1))
    if codes.size and (codes.min() < -(2 ** (bits - 1)) or codes.max() > 2 ** (bits - 1) - 1):
        raise ValueError(f"a sample is outside the range of {fmt} (full scale is 1.0)")
    if fmt == "u8":
        return (codes + 128).astype(np.uint8).tobytes()
    if fmt == "i24":
        return codes.astype("<i4").view(np.uint8).reshape(-1, 4)[:, :3].tobytes()
    return codes.astype("<i2" if fmt == "i16" else "<i4").tobytes()


def write_wav(
    path: str | os.PathLike[str],
    channels: Signal | Sequence[Signal],
    sample_format: str = "f32",
    info: Mapping[str, str] | None = None,
    cues: Sequence[tuple[int, int, str]] | None = None,
) -> None:
    """Write real signals, one per channel, as a PCM or IEEE float WAV file (conventions: Signal
    files, WAV). Only the samples, the sample rate, the ``info`` text tags (four-character IDs
    to printable ASCII, written as a ``LIST``/``INFO`` chunk after the data; ADR 0091) and the
    ``cues``, (position, length, label) triples in frames (ADR 0094, 0095), are stored."""
    tags = _wav_info_chunk(info)
    if not isinstance(sample_format, str) or sample_format not in _WAV_BITS:
        raise ValueError(f"unknown WAV sample format {sample_format!r}")
    sigs = [channels] if isinstance(channels, Signal) else list(channels)
    if not sigs or not all(isinstance(s, Signal) for s in sigs):
        raise ValueError("channels must be one signal or a non-empty list of them")
    if any(s.is_complex for s in sigs):
        raise ValueError("WAV channels must be real signals")
    rate, n = sigs[0].sample_rate, len(sigs[0])
    if any(s.sample_rate != rate or len(s) != n for s in sigs):
        raise ValueError("every channel must have the same sample rate and length")
    if not (float(rate).is_integer() and rate <= _U32):
        raise ValueError("sample_rate must be a whole number of hertz below 2^32")
    bits, is_float = _WAV_BITS[sample_format], sample_format[0] == "f"
    block = len(sigs) * bits // 8
    if block > 0xFFFF:
        raise ValueError("too many channels: the block align must fit 16 bits")
    if int(rate) * block > _U32:
        raise ValueError("the byte rate (sample rate x block align) must fit 32 bits")
    tags = _wav_cue_chunks(cues, n) + tags
    nbytes = n * block
    if 4 + (26 + 12 if is_float else 24) + 8 + nbytes + nbytes % 2 + len(tags) > _U32:
        raise ValueError("too many samples for a WAV file")
    x = np.stack([s.samples.astype(np.float64) for s in sigs], axis=1).reshape(-1)
    data = _wav_encode(x, sample_format)
    fmt = struct.pack(
        "<HHIIHH", 3 if is_float else 1, len(sigs), int(rate), int(rate) * block, block, bits
    )
    if is_float:
        body = _chunk(b"fmt ", fmt + bytes(2)) + _chunk(b"fact", struct.pack("<I", n))
    else:
        body = _chunk(b"fmt ", fmt)
    body = b"WAVE" + body + _chunk(b"data", data) + tags
    Path(os.fspath(path)).write_bytes(b"RIFF" + struct.pack("<I", len(body)) + body)


def _wav_info_chunk(info: Mapping[str, str] | None) -> bytes:
    """The ``LIST``/``INFO`` chunk for ``info``, or nothing when it is empty."""
    if info is None:
        return b""
    if not isinstance(info, Mapping):
        raise ValueError("info must be a mapping from four-character IDs to text")
    subs = b""
    for cid, text in info.items():
        if not isinstance(cid, str) or len(cid) != 4 or any(c not in _INFO_ID for c in cid):
            raise ValueError(f"info ID {cid!r} must be four characters from A-Z and 0-9")
        if not isinstance(text, str) or any(not " " <= c <= "~" for c in text):
            raise ValueError(f"info[{cid!r}] must be printable ASCII text")
        subs += _chunk(cid.encode("ascii"), text.encode("ascii") + b"\0")
    return _chunk(b"LIST", b"INFO" + subs) if subs else b""


_INFO_ID = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")


def _wav_cue_chunks(cues: Sequence[tuple[int, int, str]] | None, frames: int) -> bytes:
    """The ``cue `` chunk and ``LIST``/``adtl`` labels and regions for ``cues``, or nothing when it
    is empty."""
    if cues is None:
        return b""
    if isinstance(cues, (str, bytes, Mapping)) or not isinstance(cues, Sequence):
        raise ValueError("cues must be a sequence of (position, length, label) triples")
    points, labels = b"", b""
    for i, cue in enumerate(cues, 1):
        if not isinstance(cue, (tuple, list)) or len(cue) != 3:
            raise ValueError(f"cues[{i - 1}] must be a (position, length, label) triple")
        pos, length, label = cue
        if not _is_whole(pos) or not 0 <= pos <= frames:
            raise ValueError(f"cue position {pos!r} must be a whole number from 0 to {frames}")
        if not _is_whole(length) or not 0 <= length <= frames - pos:
            raise ValueError(
                f"cue length {length!r} must be a whole number from 0 to {frames - pos}"
            )
        if not isinstance(label, str) or any(not " " <= c <= "~" for c in label):
            raise ValueError(f"cue label {label!r} must be printable ASCII text")
        points += struct.pack("<II4sIII", i, int(pos), b"data", 0, 0, int(pos))
        if label:
            labels += _chunk(b"labl", struct.pack("<I", i) + label.encode("ascii") + b"\0")
        if length:
            labels += _chunk(b"ltxt", struct.pack("<II4s4H", i, int(length), b"rgn ", 0, 0, 0, 0))
    if not points:
        return b""
    out = _chunk(b"cue ", struct.pack("<I", len(cues)) + points)
    return out + (_chunk(b"LIST", b"adtl" + labels) if labels else b"")


def _is_whole(x: object) -> bool:
    return isinstance(x, (int, np.integer)) and not isinstance(x, bool)


def read_wav_cues(path: str | os.PathLike[str]) -> list[tuple[int, int, str]]:
    """Read the cue points of a WAV file's ``cue `` chunk, in its order, as (position, length,
    label) triples in frames, the labels from ``LIST``/``adtl`` ``labl`` subchunks (``""`` for
    none) and the lengths from ``ltxt`` subchunks (0 for none) (conventions: Signal files, WAV;
    ADR 0094, 0095)."""
    raw = Path(os.fspath(path)).read_bytes()
    if len(raw) < 12 or raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise ValueError("not a RIFF WAVE file")
    block = frames = None
    points: dict[int, int] | None = None
    labels: dict[int, str] = {}
    lengths: dict[int, int] = {}
    for cid, start, end in _riff_walk(raw, 12, len(raw), "chunk"):
        if cid == b"fmt " and block is None:
            if end - start < 16:
                raise ValueError("the fmt chunk is shorter than 16 bytes")
            (block,) = struct.unpack_from("<H", raw, start + 12)
        elif cid == b"data" and frames is None:
            frames = end - start
        elif cid == b"cue ":
            if points is not None:
                raise ValueError("there are two cue chunks")
            points = {}
            if end - start < 4:
                raise ValueError("the cue chunk is shorter than 4 bytes")
            (count,) = struct.unpack_from("<I", raw, start)
            if end - start != 4 + 24 * count:
                raise ValueError(f"the cue chunk is not 4 + 24 x {count} bytes")
            for k in range(count):
                cue_id, _, chunk, cstart, bstart, offset = struct.unpack_from(
                    "<II4sIII", raw, start + 4 + 24 * k
                )
                if chunk != b"data" or cstart or bstart:
                    raise ValueError(f"cue {cue_id} does not point straight into the data chunk")
                if cue_id in points:
                    raise ValueError(f"the cue ID {cue_id} appears twice")
                points[cue_id] = offset
        elif cid == b"LIST" and end - start >= 4 and raw[start : start + 4] == b"adtl":
            for sid, s, e in _riff_walk(raw, start + 4, end, "adtl subchunk"):
                if sid == b"ltxt":
                    if e - s < 20:
                        raise ValueError("an ltxt subchunk is shorter than 20 bytes")
                    cue_id, length = struct.unpack_from("<II", raw, s)
                    if cue_id in lengths:
                        raise ValueError(f"cue {cue_id} has two ltxt subchunks")
                    lengths[cue_id] = length
                    continue
                if sid != b"labl":
                    continue
                if e - s < 4:
                    raise ValueError("a labl subchunk is shorter than 4 bytes")
                (cue_id,) = struct.unpack_from("<I", raw, s)
                if cue_id in labels:
                    raise ValueError(f"cue {cue_id} has two labels")
                labels[cue_id] = raw[s + 4 : e].split(b"\0", 1)[0].decode("latin-1")
    if block is None:
        raise ValueError("no fmt chunk")
    if frames is None:
        raise ValueError("no data chunk")
    if block == 0:
        raise ValueError("the block align is 0")
    points = points or {}
    if any(cue_id not in points for cue_id in labels):
        raise ValueError("a label names a cue ID with no cue point")
    if any(cue_id not in points for cue_id in lengths):
        raise ValueError("an ltxt names a cue ID with no cue point")
    n = frames // block
    if any(offset > n for offset in points.values()):
        raise ValueError(f"a cue point is past the last of {n} frames")
    if any(points[cue_id] + length > n for cue_id, length in lengths.items()):
        raise ValueError(f"a cue region runs past the last of {n} frames")
    return [(p, lengths.get(c, 0), labels.get(c, "")) for c, p in points.items()]


def read_wav_info(path: str | os.PathLike[str]) -> dict[str, str]:
    """Read the text tags of every ``LIST``/``INFO`` chunk in a WAV file, in file order, IDs and
    texts decoded byte for byte as Latin-1 (conventions: Signal files, WAV; ADR 0091)."""
    raw = Path(os.fspath(path)).read_bytes()
    if len(raw) < 12 or raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise ValueError("not a RIFF WAVE file")
    out: dict[str, str] = {}
    for cid, start, end in _riff_walk(raw, 12, len(raw), "chunk"):
        if cid != b"LIST" or end - start < 4 or raw[start : start + 4] != b"INFO":
            continue
        for sid, s, e in _riff_walk(raw, start + 4, end, "INFO subchunk"):
            key = sid.decode("latin-1")
            if key in out:
                raise ValueError(f"the info ID {key!r} appears twice")
            out[key] = raw[s:e].split(b"\0", 1)[0].decode("latin-1")
    return out


def _riff_walk(raw: bytes, pos: int, stop: int, what: str) -> list[tuple[bytes, int, int]]:
    """(id, body start, body end) of each chunk from ``pos`` until fewer than 8 bytes are left."""
    out = []
    while pos + 8 <= stop:
        cid, (size,) = raw[pos : pos + 4], struct.unpack_from("<I", raw, pos + 4)
        if pos + 8 + size > stop:
            raise ValueError(f"the {cid.decode('latin-1')!r} {what} runs past its end")
        out.append((cid, pos + 8, pos + 8 + size))
        pos += 8 + size + size % 2
    return out


def _wav_decode(data: bytes, fmt: str) -> NDArray[np.float64]:
    if fmt == "u8":
        return (np.frombuffer(data, np.uint8).astype(np.float64) - 128) / 128
    if fmt == "i24":
        b = np.frombuffer(data, np.uint8).reshape(-1, 3).astype(np.int64)
        v = b[:, 0] | b[:, 1] << 8 | b[:, 2] << 16
        return (v - (v >> 23 << 24)).astype(np.float64) / 2.0**23
    codes = {"i16": "<i2", "i32": "<i4", "f32": "<f4", "f64": "<f8"}[fmt]
    x = np.frombuffer(data, codes).astype(np.float64)
    return x / 2.0 ** (_WAV_BITS[fmt] - 1) if fmt[0] == "i" else x


def read_wav(path: str | os.PathLike[str]) -> list[Signal]:
    """Read a PCM or IEEE float WAV file as real signals, one per channel, in units ``"FS"``."""
    raw = Path(os.fspath(path)).read_bytes()
    if len(raw) < 12 or raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise ValueError("not a RIFF WAVE file")
    pos, fmt = 12, None
    while True:
        if pos + 8 > len(raw):
            raise ValueError("no data chunk" if fmt is not None else "no fmt chunk")
        cid, (size,) = raw[pos : pos + 4], struct.unpack("<I", raw[pos + 4 : pos + 8])
        start, end = pos + 8, pos + 8 + size
        if end > len(raw):
            raise ValueError(f"the {cid.decode('latin-1')!r} chunk runs past the end of the file")
        if cid == b"data":
            if fmt is None:
                raise ValueError("the fmt chunk must come before the data chunk")
            data = raw[start:end]
            break
        if cid == b"fmt " and fmt is None:
            fmt = raw[start:end]
        pos = end + size % 2
    if len(fmt) < 16:
        raise ValueError("the fmt chunk is shorter than 16 bytes")
    tag, nch, rate, _, block, bits = struct.unpack("<HHIIHH", fmt[:16])
    if tag == 0xFFFE:
        if len(fmt) < 40:
            raise ValueError("an extensible fmt chunk needs at least 40 bytes")
        guid = fmt[24:40]
        if guid[2:] != _GUID_TAIL or guid[:2] not in (b"\x01\x00", b"\x03\x00"):
            raise ValueError("the extensible sub-format is not PCM or IEEE float")
        tag = guid[0]
    if tag not in _WAV_FORMATS:
        raise ValueError(f"WAV format {tag} is not PCM or IEEE float")
    if bits not in _WAV_FORMATS[tag]:
        raise ValueError(f"{bits}-bit {'PCM' if tag == 1 else 'float'} is not supported")
    if nch < 1 or rate < 1:
        raise ValueError("a WAV file needs at least one channel and a sample rate of at least 1")
    if block != nch * bits // 8:
        raise ValueError(f"block align {block} does not match {nch} channels of {bits} bits")
    if len(data) % block:
        raise ValueError(f"{len(data)} data bytes is not a whole number of {block}-byte frames")
    x = _wav_decode(data, _WAV_FORMATS[tag][bits])
    return [Signal(x[c::nch], float(rate), units="FS") for c in range(nch)]


_NPY_MAGIC = b"\x93NUMPY"
_NPY_DESCR = {
    f"{e}{t}": np.dtype(f"{e}{t}")
    for e in "<>"
    for t in ("f8", "f4", "f2", "c16", "c8", "i2", "u2", "i4", "u4", "i8", "u8")
} | {"|i1": np.dtype("i1"), "|u1": np.dtype("u1")}  # integers: ADR 0090
_NPY_KEYS = frozenset({"descr", "fortran_order", "shape"})


def write_npy(path: str | os.PathLike[str], x: ArrayLike) -> None:
    """Write a 1-D or 2-D array as a NumPy ``.npy`` file: ``'<f8'`` for real values, ``'<c16'``
    for complex, 2-D in C order, in the layout ``numpy.save`` writes (conventions: Signal files,
    NumPy .npy; ADR 0092)."""
    Path(os.fspath(path)).write_bytes(_npy_bytes(x, "x", 2))


def _npy_bytes(x: ArrayLike, name: str, max_ndim: int = 1) -> bytes:
    a = np.asarray(x)
    if not 1 <= a.ndim <= max_ndim or a.dtype.kind not in "fiuc":
        raise ValueError(
            f"{name} must be a {'1-D or 2-D' if max_ndim == 2 else '1-D'} numeric array"
        )
    descr = "<c16" if a.dtype.kind == "c" else "<f8"
    shape = f"({a.shape[0]},)" if a.ndim == 1 else f"({a.shape[0]}, {a.shape[1]})"
    text = f"{{'descr': '{descr}', 'fortran_order': False, 'shape': {shape}, }}"
    head = (text.ljust(117) + "\n").encode("ascii")
    data = a.astype(_NPY_DESCR[descr]).tobytes()
    return _NPY_MAGIC + b"\x01\x00" + struct.pack("<H", 118) + head + data


class _NpyHeader:
    """The header grammar of conventions: Signal files, NumPy .npy. The text is never evaluated."""

    def __init__(self, text: str) -> None:
        self.s, self.i = text, 0

    def fail(self) -> ValueError:
        return ValueError(f"the .npy header is not a dict this reader accepts (at {self.i})")

    def peek(self) -> str:
        while self.i < len(self.s) and self.s[self.i] in " \t\r\n":
            self.i += 1
        return self.s[self.i] if self.i < len(self.s) else ""

    def take(self, c: str) -> None:
        if self.peek() != c:
            raise self.fail()
        self.i += 1

    def string(self) -> str:
        q = self.peek()
        j = self.s.find(q, self.i + 1) if q in ("'", '"') else -1
        if j < 0 or "\\" in self.s[self.i + 1 : j]:
            raise self.fail()
        v, self.i = self.s[self.i + 1 : j], j + 1
        return v

    def integer(self) -> int:
        self.peek()
        j = self.i
        while j < len(self.s) and self.s[j] in "0123456789":
            j += 1
        t = self.s[self.i : j]
        if not t or (len(t) > 1 and t[0] == "0"):
            raise self.fail()
        self.i = j
        return int(t)

    def value(self) -> str | bool | tuple[int, ...]:
        c = self.peek()
        if c in ("'", '"'):
            return self.string()
        if c == "(":
            self.i += 1
            items, trailing = [], False
            while self.peek() != ")":
                items.append(self.integer())
                trailing = self.peek() == ","
                if trailing:
                    self.i += 1
                elif self.peek() != ")":
                    raise self.fail()
            self.i += 1
            if len(items) == 1 and not trailing:
                raise self.fail()
            return tuple(items)
        for word in ("True", "False"):
            if self.s.startswith(word, self.i):
                self.i += len(word)
                return word == "True"
        raise self.fail()

    def parse(self) -> dict[str, str | bool | tuple[int, ...]]:
        d: dict[str, str | bool | tuple[int, ...]] = {}
        self.take("{")
        while self.peek() != "}":
            key = self.string()
            self.take(":")
            if key in d:
                raise ValueError(f"the .npy header has {key!r} twice")
            d[key] = self.value()
            if self.peek() == ",":
                self.i += 1
            elif self.peek() != "}":
                raise self.fail()
        self.i += 1
        if self.peek():
            raise self.fail()
        return d


def read_npy(path: str | os.PathLike[str]) -> NDArray[np.float64] | NDArray[np.complex128]:
    """Read a 1-D NumPy ``.npy`` file (versions 1.0 to 3.0) of ``float64``, ``float32``,
    ``float16``, ``complex128`` or ``complex64`` in either byte order, widened exactly to
    ``float64`` or ``complex128`` (ADR 0088), or of 8- to 64-bit integers, read as ``float64``
    values without scaling (ADR 0090)."""
    return _parse_npy(Path(os.fspath(path)).read_bytes())


def read_npy_2d(path: str | os.PathLike[str]) -> NDArray[np.float64] | NDArray[np.complex128]:
    """Read a 2-D NumPy ``.npy`` file of shape ``(rows, columns)``, in either ``fortran_order``,
    as a C-ordered array, with the dtypes ``read_npy`` reads (conventions: Signal files, NumPy
    .npy; ADR 0092)."""
    return _parse_npy(Path(os.fspath(path)).read_bytes(), 2)


def _parse_npy(raw: bytes, ndim: int | None = 1) -> NDArray[np.float64] | NDArray[np.complex128]:
    """The values of a .npy file's bytes, of exactly ``ndim`` dimensions, or 1 or 2 for None."""
    if len(raw) < 8 or raw[:6] != _NPY_MAGIC:
        raise ValueError("not a .npy file")
    version = (raw[6], raw[7])
    if version not in ((1, 0), (2, 0), (3, 0)):
        raise ValueError(f".npy version {version[0]}.{version[1]} is not supported")
    width = 2 if version == (1, 0) else 4
    if len(raw) < 8 + width:
        raise ValueError("the .npy file ends inside its header length")
    (size,) = struct.unpack("<H" if width == 2 else "<I", raw[8 : 8 + width])
    start = 8 + width + size
    if start > len(raw):
        raise ValueError("the .npy header runs past the end of the file")
    head = raw[8 + width : start]
    if any(b > 127 for b in head):
        raise ValueError("the .npy header must be ASCII")
    d = _NpyHeader(head.decode("ascii")).parse()
    if d.keys() != _NPY_KEYS:
        raise ValueError("the .npy header needs exactly descr, fortran_order and shape")
    descr, order, shape = d["descr"], d["fortran_order"], d["shape"]
    if not isinstance(descr, str) or descr not in _NPY_DESCR:
        raise ValueError(f"descr {descr!r} is not one read_npy reads")
    if not isinstance(order, bool):
        raise ValueError("fortran_order must be True or False")
    dims = "1-D and 2-D" if ndim is None else f"{ndim}-D"
    if not isinstance(shape, tuple) or len(shape) not in ((1, 2) if ndim is None else (ndim,)):
        raise ValueError(f"only {dims} arrays are read here, not shape {shape!r}")
    if len(shape) == 2 and max(shape) > 2147483591:
        raise ValueError(f"shape {shape!r} has a dimension beyond 2147483591")
    dt = _NPY_DESCR[descr]
    if len(raw) - start != math.prod(shape) * dt.itemsize:
        raise ValueError(f"{len(raw) - start} data bytes do not match shape {shape!r}")
    values = np.frombuffer(raw, dt, offset=start).reshape(shape, order="F" if order else "C")
    if dt.kind == "c":
        return values.astype(np.complex128, order="C")
    return values.astype(np.float64, order="C")


_ZIP_LOCAL, _ZIP_CENTRAL, _ZIP_END = b"PK\x03\x04", b"PK\x01\x02", b"PK\x05\x06"
_ZIP_DATE = 0x0021  # 1980-01-01


def write_npz(path: str | os.PathLike[str], arrays: Mapping[str, ArrayLike]) -> None:
    """Write 1-D or 2-D arrays as a NumPy ``.npz`` archive: one uncompressed ``<key>.npy`` member
    each, in the mapping's order (conventions: Signal files, NumPy .npz; ADRs 0089 and 0093)."""
    if not isinstance(arrays, Mapping):
        raise ValueError("arrays must be a mapping from names to arrays")
    if len(arrays) > 65535:
        raise ValueError("an archive holds at most 65535 arrays")
    body, central = bytearray(), bytearray()
    for key, x in arrays.items():
        if (
            not isinstance(key, str)
            or not 1 <= len(key) <= 250
            or any(not " " <= c <= "~" or c in "/\\" for c in key)
        ):
            raise ValueError(
                f"name {key!r} must be 1 to 250 printable ASCII characters, no / or \\"
            )
        name, data = (key + ".npy").encode("ascii"), _npy_bytes(x, f"arrays[{key!r}]", 2)
        crc, offset = zlib.crc32(data), len(body)
        sizes = struct.pack("<HHHIIIH", 0, 0, _ZIP_DATE, crc, len(data), len(data), len(name))
        body += _ZIP_LOCAL + struct.pack("<HH", 20, 0) + sizes + b"\0\0" + name + data
        central += _ZIP_CENTRAL + struct.pack("<HHH", 20, 20, 0) + sizes
        central += struct.pack("<HHHHII", 0, 0, 0, 0, 0, offset) + name
        if len(body) + len(central) + 22 >= 2**32:
            raise ValueError("the archive would reach 4 GiB, which needs ZIP64")
    n = len(arrays)
    end = _ZIP_END + struct.pack("<HHHHIIH", 0, 0, n, n, len(central), len(body), 0)
    Path(os.fspath(path)).write_bytes(bytes(body + central + end))


def read_npz(
    path: str | os.PathLike[str],
) -> dict[str, NDArray[np.float64] | NDArray[np.complex128]]:
    """Read a NumPy ``.npz`` archive (stored or deflated ``.npy`` members, each 1-D or 2-D) as a
    dict in member order; the ZIP is parsed here, not by ``zipfile`` (conventions: Signal files,
    NumPy .npz; ADRs 0089 and 0093)."""
    raw = Path(os.fspath(path)).read_bytes()
    at = next(
        (
            i
            for i in range(len(raw) - 22, max(-1, len(raw) - 65558), -1)
            if raw[i : i + 4] == _ZIP_END
            and i + 22 + struct.unpack_from("<H", raw, i + 20)[0] == len(raw)
        ),
        -1,
    )
    if at < 0:
        raise ValueError("not a ZIP archive: no end record")
    disk, cd_disk, here, count, cd_size, cd_at = struct.unpack_from("<HHHHII", raw, at + 4)
    if disk or cd_disk:
        raise ValueError("multi-disk archives are not read")
    if here != count:
        raise ValueError("the end record's two member counts differ")
    if count == 0xFFFF or cd_size == 0xFFFFFFFF or cd_at == 0xFFFFFFFF:
        raise ValueError("archives that need ZIP64 are not read")
    if cd_at + cd_size > at:
        raise ValueError("the central directory runs past the end record")
    out: dict[str, NDArray[np.float64] | NDArray[np.complex128]] = {}
    i = cd_at
    for _ in range(count):
        if i + 46 > cd_at + cd_size or raw[i : i + 4] != _ZIP_CENTRAL:
            raise ValueError("a central directory header is missing")
        flags, method = struct.unpack_from("<HH", raw, i + 8)
        crc, csize, usize, nlen, xlen, clen = struct.unpack_from("<IIIHHH", raw, i + 16)
        (offset,) = struct.unpack_from("<I", raw, i + 42)
        name_end = i + 46 + nlen
        if name_end + xlen + clen > cd_at + cd_size:
            raise ValueError("a central directory header runs past the directory")
        name_raw, extra = raw[i + 46 : name_end], raw[name_end : name_end + xlen]
        i = name_end + xlen + clen
        if flags & 1:
            raise ValueError("encrypted members are not read")
        if method not in (0, 8):
            raise ValueError(f"compression method {method} is not read (only stored and deflate)")
        usize, csize, offset = _zip64_fields(extra, usize, csize, offset)
        try:
            name = name_raw.decode("utf-8" if flags & 0x800 else "ascii")
        except UnicodeDecodeError:
            raise ValueError("a member name is not valid text") from None
        if not name.endswith(".npy") or len(name) == 4:
            raise ValueError(f"member {name!r} is not a .npy array")
        key = name[:-4]
        if key in out:
            raise ValueError(f"the archive has {key!r} twice")
        if offset + 30 > len(raw) or raw[offset : offset + 4] != _ZIP_LOCAL:
            raise ValueError(f"member {name!r} has no local header")
        ln, lx = struct.unpack_from("<HH", raw, offset + 26)
        start = offset + 30 + ln + lx
        if start + csize > len(raw):
            raise ValueError(f"member {name!r} runs past the end of the file")
        data = raw[start : start + csize]
        if method == 8:
            d = zlib.decompressobj(-15)
            try:
                data = d.decompress(data, usize + 1)
            except zlib.error:
                raise ValueError(f"member {name!r} is not valid deflate data") from None
        if len(data) != usize:
            raise ValueError(f"member {name!r} is not {usize} bytes")
        if zlib.crc32(data) != crc:
            raise ValueError(f"member {name!r} fails its CRC-32")
        out[key] = _parse_npy(data, None)
    return out


def _zip64_fields(extra: bytes, usize: int, csize: int, offset: int) -> tuple[int, int, int]:
    """Sizes and offset, with each 0xFFFFFFFF taken from the ZIP64 extra field (0x0001)."""
    need = [v == 0xFFFFFFFF for v in (usize, csize, offset)]
    if not any(need):
        return usize, csize, offset
    j = 0
    while j + 4 <= len(extra):
        tag, size = struct.unpack_from("<HH", extra, j)
        if tag == 1:
            values = (
                list(struct.unpack_from(f"<{size // 8}Q", extra, j + 4))
                if j + 4 + size <= len(extra)
                else []
            )
            got = [usize, csize, offset]
            for k in range(3):
                if need[k]:
                    if not values:
                        raise ValueError("the ZIP64 extra field is too short")
                    got[k] = values.pop(0)
            return got[0], got[1], got[2]
        j += 4 + size
    raise ValueError("a ZIP64 size or offset has no ZIP64 extra field")
