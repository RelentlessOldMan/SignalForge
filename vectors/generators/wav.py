"""Writes vectors/cases/wav.json and the .wav files in vectors/files/, using only the standard library.

It does not import NumPy or SignalForge. Bytes come from the struct module; integer codes from
round() (half to even) of x * 2^(b-1), plus 128 for u8; float32 values from a struct round trip.
Every PCM file with an even data size is also written by Python's wave module, and the two must be
the same bytes, so the header layout is checked against an independent writer. Files from other
tools' layouts (extensible, extra chunks, no fact chunk) are written here as literal chunks.

Run from the repo root: python vectors/generators/wav.py [--check]
With --check it writes nothing and exits 1 unless every file matches what it would write.
"""

import io
import json
import pathlib
import struct
import sys
import wave

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOL = {"abs": 0, "rel": 0}
BITS = {"u8": 8, "i16": 16, "i24": 24, "i32": 32, "f32": 32, "f64": 64}
GUID_TAIL = bytes.fromhex("000000001000800000aa00389b71")


def code(v, fmt):
    c = round(v * 2 ** (BITS[fmt] - 1))
    return c + 128 if fmt == "u8" else c


def sample_bytes(v, fmt):
    if fmt == "f32":
        try:
            return struct.pack("<f", v)
        except OverflowError:  # rounds beyond the largest float32: stored as infinity
            return struct.pack("<f", float("inf") if v > 0 else float("-inf"))
    if fmt == "f64":
        return struct.pack("<d", v)
    c = code(v, fmt)
    if fmt == "u8":
        return struct.pack("<B", c)
    if fmt == "i16":
        return struct.pack("<h", c)
    return struct.pack("<i", c)[:3] if fmt == "i24" else struct.pack("<i", c)


def value(raw, fmt):
    """The sample a reader gets from the bytes of one sample."""
    if fmt == "f32":
        return struct.unpack("<f", raw)[0]
    if fmt == "f64":
        return struct.unpack("<d", raw)[0]
    if fmt == "u8":
        return (raw[0] - 128) / 128
    c = int.from_bytes(raw, "little", signed=True)
    return c / 2 ** (8 * len(raw) - 1)


def chunk(cid, body):
    return cid + struct.pack("<I", len(body)) + body + (b"\0" if len(body) % 2 else b"")


def riff(chunks, size=None):
    body = b"WAVE" + b"".join(chunks)
    return b"RIFF" + struct.pack("<I", len(body) if size is None else size) + body


def fmt_chunk(tag, nch, rate, bits, extra=None, block=None):
    ba = nch * bits // 8 if block is None else block
    body = struct.pack("<HHIIHH", tag, nch, rate, rate * ba % 2**32, ba, bits)
    return chunk(b"fmt ", body + (extra if extra is not None else b""))


def frames(channels, fmt):
    n = len(channels[0])
    return b"".join(sample_bytes(channels[c][i], fmt) for i in range(n) for c in range(len(channels)))


def wav(channels, rate, fmt):
    """The bytes write_wav writes (conventions: Signal files, WAV)."""
    nch, bits = len(channels), BITS[fmt]
    if fmt[0] == "f":
        head = [fmt_chunk(3, nch, rate, bits, struct.pack("<H", 0)),
                chunk(b"fact", struct.pack("<I", len(channels[0])))]
    else:
        head = [fmt_chunk(1, nch, rate, bits)]
    out = riff(head + [chunk(b"data", frames(channels, fmt))])
    data = frames(channels, fmt)
    if fmt[0] != "f" and len(data) % 2 == 0:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(nch)
            w.setsampwidth(bits // 8)
            w.setframerate(rate)
            w.writeframes(data)
        assert buf.getvalue() == out, f"wave module disagrees for {fmt} x{nch}"
    return out


def decoded(data, nch, fmt):
    size = BITS[fmt] // 8
    vals = [value(data[i:i + size], fmt) for i in range(0, len(data), size)]
    return [vals[c::nch] for c in range(nch)]


cases = []


def case_write(name, channels, rate, fmt, why):
    cases.append({"id": f"write_wav.{name}", "op": "write_wav",
                  "args": {"channels": channels, "sample_rate": rate, "sample_format": fmt},
                  "expected": wav(channels, rate, fmt).hex(), "tol": TOL, "source": why})


def bad_write(name, channels, rate, fmt, why):
    cases.append({"id": f"write_wav.{name}", "op": "write_wav",
                  "args": {"channels": channels, "sample_rate": rate, "sample_format": fmt},
                  "error": "invalid_argument", "source": why})


X = [0.5, -0.25, 0.123456789, -1.0, 0.0, 0.0078125]
SRC = "struct.pack of each sample (integers: round(x * 2^(b-1)), half to even, +128 for u8); " \
      "PCM headers also from Python's wave module"
for fmt in BITS:
    case_write(f"{fmt}_mono", [X], 48000, fmt, SRC)
case_write("i16_stereo", [X[:3], X[3:]], 44100, "i16", "interleaved frame by frame; " + SRC)
case_write("f32_stereo", [X[:3], X[3:]], 44100, "f32", "interleaved, fact chunk holds 3 frames; " + SRC)
case_write("i24_three_channels", [[0.5, -0.5], [0.25, -0.25], [-1.0, 0.0]], 96000, "i24",
           "3 channels of 3 bytes, block align 9; " + SRC)
case_write("u8_odd_pad", [[0.5, -0.5, 0.0]], 8000, "u8", "3 data bytes, padded to 4 (RIFF size counts the pad)")
case_write("i24_one_sample_pad", [[-0.5]], 8000, "i24", "3 data bytes, padded to 4")
case_write("i16_ties_to_even", [[1.5 / 32768, 2.5 / 32768, -0.5 / 32768, -1.5 / 32768]], 1000, "i16",
           "codes 1.5, 2.5, -0.5, -1.5 round half to even: 2, 2, 0, -2")
case_write("u8_ties_to_even", [[0.5 / 128, 1.5 / 128, -0.5 / 128]], 1000, "u8",
           "codes 0.5, 1.5, -0.5 round to 0, 2, 0, then +128")
case_write("i16_extremes", [[-1.0, 32767 / 32768]], 1000, "i16", "the most negative and most positive codes")
case_write("i24_extremes", [[-1.0, (2**23 - 1) / 2**23]], 1000, "i24", "the most negative and most positive codes")
case_write("i32_extremes", [[-1.0, (2**31 - 1) / 2**31]], 1000, "i32", "the most negative and most positive codes")
case_write("u8_extremes", [[-1.0, 127 / 128]], 1000, "u8", "bytes 0x00 and 0xff")
case_write("f32_overflow_is_inf", [[1e39, -1e39]], 1000, "f32", "beyond the float32 range becomes +-inf")
case_write("f64_beyond_full_scale", [[2.5, -1e300]], 1000, "f64", "floats hold values beyond full scale")
case_write("i16_empty", [[]], 1000, "i16", "no frames: a data chunk of size 0")
case_write("f32_empty_stereo", [[], []], 1000, "f32", "no frames: fact 0, data size 0")
case_write("u8_largest_rate", [[0.0, 0.0]], 2**32 - 1, "u8", "the largest rate that fits 32 bits, byte rate too")
bad_write("i16_full_scale", [[1.0]], 1000, "i16", "+1.0 is code 32768, outside i16")
bad_write("u8_below_range", [[-129 / 128]], 1000, "u8", "code -129 is outside u8")
bad_write("i24_full_scale", [[1.0]], 1000, "i24", "+1.0 is code 2^23, outside i24")
bad_write("fractional_rate", [[0.0]], 8000.5, "i16", "the sample rate must be a whole number of hertz")
bad_write("rate_too_big", [[0.0]], 2**32, "u8", "2^32 does not fit the 32-bit sample rate field")
bad_write("byte_rate_too_big", [[0.0]], 2**31, "i16", "byte rate 2^31 * 2 does not fit 32 bits")
bad_write("zero_rate", [[0.0]], 0, "i16", "a signal's sample rate must be positive")
bad_write("no_channels", [], 1000, "i16", "at least one channel")
bad_write("format_i8", [[0.0]], 1000, "i8", "8-bit WAV is unsigned: u8, not i8")
bad_write("format_f16", [[0.0]], 1000, "f16", "no 16-bit float")
bad_write("format_sigmf_name", [[0.0]], 1000, "ri16_le", "WAV formats are named without kind or order")

recs = []  # (name, bytes, expected record or None, why)


def good(name, data, channels, rate, why):
    recs.append((name, data, {"channels": channels, "sample_rate": rate, "units": "FS"}, why))


def bad(name, data, why):
    recs.append((name, data, None, why))


def by_wave(nch, width, rate, data):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(nch)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(data)
    return buf.getvalue()


for name, fmt, nch, rate, raw in (
    ("wave_i16_stereo", "i16", 2, 44100, struct.pack("<6h", 16384, -16384, 1, -32768, 32767, 0)),
    ("wave_u8_mono", "u8", 1, 8000, bytes([0, 64, 128, 255])),
    ("wave_i24_mono", "i24", 1, 96000, bytes.fromhex("000080" "ffff7f")),
    ("wave_i32_stereo", "i32", 2, 192000, struct.pack("<4i", -2**31, 2**31 - 1, 1 << 16, -3)),
):
    good(name, by_wave(nch, BITS[fmt] // 8, rate, raw), decoded(raw, nch, fmt), rate,
         f"written by Python's wave module; samples from the {fmt} codes")

f32 = struct.pack("<4f", 0.5, -2.0, 0.1, 1e-3)
good("float32_stereo", riff([fmt_chunk(3, 2, 48000, 32, b"\0\0"), chunk(b"fact", struct.pack("<I", 2)),
                             chunk(b"data", f32)]), decoded(f32, 2, "f32"), 48000,
     "format 3 with a fact chunk; float32 values from a struct round trip")
f64 = struct.pack("<3d", 0.1, -3.5, 1e-300)
good("float64_no_fact", riff([fmt_chunk(3, 1, 1000, 64), chunk(b"data", f64)]),
     decoded(f64, 1, "f64"), 1000, "format 3 with a 16-byte fmt and no fact chunk, as some tools write")
i24 = bytes.fromhex("000040" "0000c0" "ffff7f" "000080" "010000" "000000")
ext = struct.pack("<HHI", 22, 24, 7) + b"\x01\x00" + GUID_TAIL
good("extensible_i24_three_channels", riff([fmt_chunk(0xFFFE, 3, 48000, 24, ext), chunk(b"data", i24)]),
     decoded(i24, 3, "i24"), 48000, "WAVE_FORMAT_EXTENSIBLE, PCM sub-format, 24 bits, mask 7")
i32 = bytes.fromhex("00000040" "000000c0" "00ffff7f")
ext = struct.pack("<HHI", 22, 24, 4) + b"\x01\x00" + GUID_TAIL
good("extensible_i32_valid_24", riff([fmt_chunk(0xFFFE, 1, 44100, 32, ext), chunk(b"data", i32)]),
     decoded(i32, 1, "i32"), 44100, "24 valid bits in a 32-bit container: scaled by the container, as left-justified")
ext = struct.pack("<HHI", 22, 32, 3) + b"\x03\x00" + GUID_TAIL
good("extensible_float", riff([fmt_chunk(0xFFFE, 2, 48000, 32, ext), chunk(b"fact", struct.pack("<I", 2)),
                               chunk(b"data", f32)]), decoded(f32, 2, "f32"), 48000,
     "WAVE_FORMAT_EXTENSIBLE, IEEE float sub-format")
i16 = struct.pack("<3h", 100, -200, 300)
good("extra_chunks", riff([chunk(b"LIST", b"INFOx"), fmt_chunk(1, 1, 22050, 16), chunk(b"junk", b"abc"),
                           chunk(b"data", i16), chunk(b"cue ", b"\0" * 4)], size=0),
     decoded(i16, 1, "i16"), 22050, "odd-sized unknown chunks before and after fmt are skipped with their pad; "
     "a chunk after data and a RIFF size of 0 are ignored")
u8 = bytes([192, 64, 128])
good("u8_odd_pad", riff([fmt_chunk(1, 1, 8000, 8), chunk(b"data", u8)]), decoded(u8, 1, "u8"), 8000,
     "3 data bytes and a pad byte")
good("u8_odd_no_pad", riff([fmt_chunk(1, 1, 8000, 8), chunk(b"data", u8)])[:-1], decoded(u8, 1, "u8"), 8000,
     "the pad byte after the last chunk is missing, as some tools write")
good("empty_stereo", riff([fmt_chunk(1, 2, 1000, 16), chunk(b"data", b"")]), [[], []], 1000,
     "no frames: two empty channels")
good("fmt_18_pcm", riff([fmt_chunk(1, 1, 1000, 16, b"\0\0"), chunk(b"data", i16)]),
     decoded(i16, 1, "i16"), 1000, "a PCM fmt chunk of 18 bytes (cbSize 0)")

pcm = fmt_chunk(1, 1, 1000, 16)
data = chunk(b"data", i16)
bad("rifx", b"RIFX" + riff([pcm, data])[4:], "RIFX (big-endian) is not RIFF")
bad("not_wave", riff([pcm, data]).replace(b"WAVE", b"AVI ", 1), "a RIFF file that is not WAVE")
bad("too_short", b"RIFF\0\0\0\0", "8 bytes: no form type")
bad("no_fmt", riff([data]), "no fmt chunk")
bad("data_before_fmt", riff([data, pcm]), "the fmt chunk must come before data")
bad("no_data", riff([pcm]), "no data chunk")
bad("fmt_14_bytes", riff([chunk(b"fmt ", struct.pack("<HHIIH", 1, 1, 1000, 2000, 2)), data]),
    "a 14-byte fmt has no bits per sample")
bad("adpcm", riff([fmt_chunk(2, 1, 1000, 4, block=256), data]), "format 2 (ADPCM) is compressed")
bad("pcm_12_bits", riff([fmt_chunk(1, 1, 1000, 12, block=2), data]), "PCM takes 8, 16, 24 or 32 bits")
bad("float_16_bits", riff([fmt_chunk(3, 1, 1000, 16), data]), "float takes 32 or 64 bits")
bad("pcm_64_bits", riff([fmt_chunk(1, 1, 1000, 64), chunk(b"data", b"\0" * 8)]), "64-bit PCM is not read")
bad("block_align_wrong", riff([fmt_chunk(1, 2, 1000, 16, block=2), data]), "block align must be 2 * 16 / 8 = 4")
bad("zero_channels", riff([fmt_chunk(1, 0, 1000, 16, block=0), data]), "at least one channel")
bad("zero_rate", riff([fmt_chunk(1, 1, 0, 16), data]), "the sample rate must be at least 1")
ext = struct.pack("<HHI", 22, 16, 4) + b"\x02\x00" + GUID_TAIL
bad("extensible_adpcm", riff([fmt_chunk(0xFFFE, 1, 1000, 16, ext), data]), "sub-format 2 is ADPCM")
ext = struct.pack("<HHI", 22, 16, 4) + b"\x01\x00" + GUID_TAIL[:-1] + b"\x72"
bad("extensible_bad_guid", riff([fmt_chunk(0xFFFE, 1, 1000, 16, ext), data]), "the GUID tail must match")
bad("extensible_short", riff([fmt_chunk(0xFFFE, 1, 1000, 16, b"\0\0"), data]),
    "an extensible fmt needs at least 40 bytes")
bad("partial_frame", riff([fmt_chunk(1, 2, 1000, 16), chunk(b"data", i16)]),
    "6 data bytes is not a whole number of 4-byte frames")
bad("data_past_end", riff([pcm, b"data" + struct.pack("<I", 100) + i16]), "the data chunk says 100 bytes, the file has 6")
bad("chunk_past_end", riff([pcm, b"LIST" + struct.pack("<I", 1000) + b"INFO"]),
    "a chunk before data runs past the end of the file")

for name, _, expected, why in recs:
    c = {"id": f"read_wav.{name}", "op": "read_wav", "args": {"file": f"{name}.wav"}}
    c.update({"error": "invalid_argument", "source": why} if expected is None
             else {"expected": expected, "tol": TOL, "source": why})
    cases.append(c)

doc = {
    "schema": 1,
    "suite": "wav",
    "description": "Writing WAV files in every sample format, and reading WAV files laid out as "
    "SignalForge and other tools write them, from vectors/files (conventions: Signal files, WAV).",
    "cases": cases,
}
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
outputs = {ROOT / "cases" / "wav.json": (head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n").encode()}
for name, data, _, _ in recs:
    outputs[ROOT / "files" / f"{name}.wav"] = data

if "--check" in sys.argv[1:]:
    stale = [p for p, b in outputs.items() if not p.is_file() or p.read_bytes() != b]
    stale += [p for p in (ROOT / "files").glob("*.wav") if p not in outputs]
    if stale:
        sys.exit("out of date (run python vectors/generators/wav.py): "
                 + ", ".join(str(p.relative_to(ROOT)) for p in stale))
    print(f"{len(outputs)} files are up to date")
    sys.exit(0)
for p, b in outputs.items():
    p.write_bytes(b)
print(f"wrote {len(outputs)} files ({len(cases)} cases)")
