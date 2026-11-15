"""Writes vectors/cases/wav.json and the .wav files in vectors/files/, using only the standard library.

It does not import NumPy or SignalForge. Bytes come from the struct module; integer codes from
round() (half to even) of x * 2^(b-1), plus 128 for u8; float32 values from a struct round trip.
Every PCM file with an even data size is also written by Python's wave module, and the two must be
the same bytes, so the header layout is checked against an independent writer. Files from other
tools' layouts (extensible, extra chunks, no fact chunk) are written here as literal chunks.
LIST/INFO text tags (ADR 0091) are literal byte strings packed with struct; a tagged PCM file must
still give the wave module the same frames as the untagged one. Cue points and their labels
(ADR 0094) are cue and LIST/adtl chunks packed with struct from the 24-byte cue point layout; a
PCM file with cues must also give the wave module the same frames.

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

def info_chunk(tags):
    """A LIST/INFO chunk of (id, text) byte pairs, each text NUL-terminated and padded to even."""
    return chunk(b"LIST", b"INFO" + b"".join(chunk(i, t + b"\0") for i, t in tags))


def tagged(base, tags):
    """A WAV file with a LIST/INFO chunk appended after everything else, RIFF size updated."""
    body = base[8:] + info_chunk(tags)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def case_info(name, channels, rate, fmt, tags, why):
    expected = tagged(wav(channels, rate, fmt), tags) if tags else wav(channels, rate, fmt)
    if fmt in ("i16", "u8") and len(channels[0]) % 2 == 0:
        with wave.open(io.BytesIO(expected)) as w:
            assert w.readframes(w.getnframes()) == frames(channels, fmt), name
    info = [{"id": i.decode(), "text": t.decode()} for i, t in tags]
    cases.append({"id": f"write_wav.{name}", "op": "write_wav",
                  "args": {"channels": channels, "sample_rate": rate, "sample_format": fmt, "info": info},
                  "expected": expected.hex(), "tol": TOL, "source": why})


def bad_info(name, info, why):
    cases.append({"id": f"write_wav.{name}", "op": "write_wav",
                  "args": {"channels": [[0.0]], "sample_rate": 1000, "sample_format": "i16", "info": info},
                  "error": "invalid_argument", "source": why})


case_info("info_i16", [X[:2]], 8000, "i16", [(b"INAM", b"Test tone"), (b"ISFT", b"SignalForge")],
          "LIST, size, INFO, then INAM size 10 (9 + NUL), ISFT size 12 (11 + NUL) and its pad; "
          "the wave module still reads the frames")
case_info("info_f32", [X[:3], X[3:]], 44100, "f32", [(b"ICMT", b"stereo, 3 frames")],
          "after fmt, fact and data; ICMT size 17 (16 + NUL), padded to 18")
case_info("info_u8_odd_data", [[0.5, -0.5, 0.0]], 8000, "u8", [(b"IART", b"x")],
          "the data pad byte comes first, then LIST; IART size 2, no pad")
case_info("info_empty_text", [X[:2]], 1000, "i16", [(b"ICMT", b"")], "an empty text is one NUL, padded to 2")
case_info("info_order_kept", [X[:2]], 1000, "i16",
          [(b"ISFT", b"a"), (b"ICRD", b"2026-11-14"), (b"IART", b"~ !")],
          "tags in the order given, not sorted; sizes 2, 11 (padded) and 4")
case_info("info_digit_id", [X[:2]], 1000, "i16", [(b"I0A9", b"ok")], "digits are allowed in an ID")
case_info("info_empty", [X[:2]], 1000, "i16", [], "no tags: no LIST chunk, the bytes of a plain file")
for n, (bad_id, why) in enumerate((("inam", "lowercase is not allowed"), ("NAM", "three characters"),
                                   ("INAME", "five characters"), ("ID3 ", "a space is not allowed"),
                                   ("", "an empty ID"))):
    bad_info(f"info_bad_id_{n}", [{"id": bad_id, "text": "x"}], "IDs are four of A-Z, 0-9: " + why)
bad_info("info_non_ascii", [{"id": "INAM", "text": "caf\u00e9"}], "texts are printable ASCII: no e-acute")
bad_info("info_newline", [{"id": "ICMT", "text": "a\nb"}], "a line feed is not printable")
bad_info("info_nul", [{"id": "ICMT", "text": "a\u0000b"}], "a NUL inside the text would end it early")
bad_info("info_delete", [{"id": "ICMT", "text": "\u007f"}], "0x7F is not printable")

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

info_recs = []  # (name, bytes, expected [(id, text)] or None, why)


def good_info(name, data, tags, why):
    info_recs.append((f"info_{name}", data, tags, why))


def bad_info_file(name, data, why):
    info_recs.append((f"info_{name}", data, None, why))


plain = riff([pcm, data])
good_info("after_data", tagged(plain, [(b"INAM", b"Test tone"), (b"IART", b"SignalForge"), (b"ICMT", b"")]),
          [("INAM", "Test tone"), ("IART", "SignalForge"), ("ICMT", "")],
          "after data, as write_wav puts it; each text up to its NUL")
good_info("before_fmt", riff([info_chunk([(b"ISFT", b"Lavf")]), pcm, data]), [("ISFT", "Lavf")],
          "LIST may come anywhere, here before fmt")
good_info("none", plain, [], "no LIST chunk: no tags")
good_info("empty_list", riff([pcm, data, chunk(b"LIST", b"INFO")]), [], "a LIST/INFO with no subchunks")
good_info("short_list", riff([pcm, data, chunk(b"LIST", b"IN")]), [], "a LIST body under 4 bytes has no form type: skipped")
good_info("no_nul", riff([pcm, data, chunk(b"LIST", b"INFO" + chunk(b"INAM", b"ab"))]), [("INAM", "ab")],
          "a text without a NUL is all of its body")
good_info("after_nul", riff([pcm, data, chunk(b"LIST", b"INFO" + chunk(b"ICMT", b"abc\0\0junk"))]),
          [("ICMT", "abc")], "the text stops at the first NUL; the rest of the body is ignored")
good_info("latin1", riff([pcm, data, info_chunk([(b"INAM", b"caf\xe9"), (b"IART", b"caf\xc3\xa9")])]),
          [("INAM", "caf\u00e9"), ("IART", "caf\u00c3\u00a9")],
          "each byte is the character with that code: 0xE9 is e-acute, UTF-8 C3 A9 is two characters")
good_info("two_lists", riff([info_chunk([(b"INAM", b"a")]), pcm, data, info_chunk([(b"IART", b"b")])]),
          [("INAM", "a"), ("IART", "b")], "tags from every LIST/INFO, in file order")
adtl = chunk(b"LIST", b"adtl" + chunk(b"labl", struct.pack("<I", 1) + b"INAM\0"))
good_info("adtl_skipped", riff([pcm, data, adtl, info_chunk([(b"INAM", b"x")])]), [("INAM", "x")],
          "a LIST of another type is skipped")
good_info("tags_only", riff([info_chunk([(b"ICMT", b"no audio")])]), [("ICMT", "no audio")],
          "fmt and data are not needed to read tags")
odd = riff([pcm, data, b"LIST" + struct.pack("<I", 15) + b"INFO" + b"IART" + struct.pack("<I", 3) + b"ab\0"])
good_info("odd_no_pad", odd, [("IART", "ab")],
          "the last subchunk and the LIST chunk are odd, and the file ends without their pad bytes")
good_info("trailing_bytes", riff([pcm, data, info_chunk([(b"INAM", b"t")])]) + b"\0\0\0\0\0\0\0",
          [("INAM", "t")], "7 bytes left at the end: fewer than 8, ignored")
good_info("lowercase_id", riff([pcm, data, info_chunk([(b"inam", b"low")])]), [("inam", "low")],
          "IDs are not checked on read")
good_info("u8_odd_data", riff([fmt_chunk(1, 1, 8000, 8), chunk(b"data", u8), info_chunk([(b"INAM", b"u")])]),
          [("INAM", "u")], "after the pad byte of an odd data chunk")
bad_info_file("not_wave", tagged(plain, [(b"INAM", b"a")]).replace(b"WAVE", b"AVI ", 1), "a RIFF file that is not WAVE")
bad_info_file("rifx", b"RIFX" + tagged(plain, [(b"INAM", b"a")])[4:], "RIFX is not RIFF")
bad_info_file("too_short", b"RIFF\4\0\0\0WAV", "11 bytes: no full form type")
bad_info_file("dup_same_list", riff([pcm, data, info_chunk([(b"INAM", b"a"), (b"INAM", b"b")])]),
              "INAM twice in one LIST")
bad_info_file("dup_two_lists", riff([info_chunk([(b"INAM", b"a")]), pcm, data, info_chunk([(b"INAM", b"b")])]),
              "INAM in two LIST chunks")
bad_info_file("sub_past_list", riff([pcm, data, chunk(b"LIST", b"INFO" + b"INAM" + struct.pack("<I", 9) + b"abc\0")]),
              "the INAM subchunk says 9 bytes, its LIST has 4 left")
bad_info_file("list_past_end", riff([pcm, data]) + b"LIST" + struct.pack("<I", 100) + b"INFO",
              "the LIST chunk says 100 bytes, the file has 4 left")
bad_info_file("data_past_end", riff([pcm, b"data" + struct.pack("<I", 100) + i16]),
              "the data chunk runs past the end of the file")

for name, _, expected, why in info_recs:
    c = {"id": f"read_wav_info.{name}", "op": "read_wav_info", "args": {"file": f"{name}.wav"}}
    c.update({"error": "invalid_argument", "source": why} if expected is None
             else {"expected": [{"id": i, "text": t} for i, t in expected], "source": why})
    cases.append(c)

def cue_point(cue_id, pos, play=None, cid=b"data", cstart=0, bstart=0):
    """One 24-byte cue point: ID, play order, chunk ID, chunk start, block start, sample offset."""
    return struct.pack("<II4sIII", cue_id, pos if play is None else play, cid, cstart, bstart, pos)


def cue_chunk(points):
    return chunk(b"cue ", struct.pack("<I", len(points)) + b"".join(points))


def adtl_chunk(labels):
    """A LIST/adtl chunk of labl subchunks from (cue ID, text bytes) pairs."""
    return chunk(b"LIST", b"adtl" + b"".join(chunk(b"labl", struct.pack("<I", i) + t + b"\0")
                                             for i, t in labels))


def cue_bytes(cues):
    """The chunks write_wav adds for (position, label) cues: IDs 1, 2, ... in order."""
    if not cues:
        return b""
    out = cue_chunk([cue_point(i, p) for i, (p, _) in enumerate(cues, 1)])
    labels = [(i, t.encode("ascii")) for i, (_, t) in enumerate(cues, 1) if t]
    return out + (adtl_chunk(labels) if labels else b"")


def with_chunks(base, extra):
    body = base[8:] + extra
    return b"RIFF" + struct.pack("<I", len(body)) + body


def case_cues(name, channels, rate, fmt, cues, why, tags=()):
    expected = with_chunks(wav(channels, rate, fmt), cue_bytes(cues) + (info_chunk(tags) if tags else b""))
    if fmt in ("i16", "u8") and len(channels[0]) % 2 == 0:
        with wave.open(io.BytesIO(expected)) as w:
            assert w.readframes(w.getnframes()) == frames(channels, fmt), name
    args = {"channels": channels, "sample_rate": rate, "sample_format": fmt,
            "cues": [{"position": p, "label": t} for p, t in cues]}
    if tags:
        args["info"] = [{"id": i.decode(), "text": t.decode()} for i, t in tags]
    cases.append({"id": f"write_wav.{name}", "op": "write_wav", "args": args,
                  "expected": expected.hex(), "tol": TOL, "source": why})


def bad_cues(name, cues, why):
    cases.append({"id": f"write_wav.{name}", "op": "write_wav",
                  "args": {"channels": [[0.0, 0.0]], "sample_rate": 1000, "sample_format": "i16",
                           "cues": [{"position": p, "label": t} for p, t in cues]},
                  "error": "invalid_argument", "source": why})


case_cues("cues_i16", [X[:4]], 8000, "i16", [(0, "start"), (2, "burst")],
          "cue size 52 (4 + 2 x 24), IDs 1 and 2, play order = sample offset; LIST/adtl with labl "
          "sizes 10 (4 + 5 + NUL) and 10; the wave module still reads the frames")
case_cues("cues_unlabelled", [X[:2]], 1000, "i16", [(1, "")], "no label: a cue chunk and no LIST/adtl")
case_cues("cues_some_labels", [X[:4]], 1000, "i16", [(3, ""), (0, "a"), (3, "")],
          "only the labelled point gets a labl, keyed by its ID 2; positions in the order given, "
          "a position may repeat")
case_cues("cues_at_end", [X[:3], X[3:]], 44100, "f32", [(3, "end")],
          "a position equal to the length is the end of the data; after fmt, fact and data")
case_cues("cues_u8_odd_data", [[0.5, -0.5, 0.0]], 8000, "u8", [(1, "ab")],
          "after the data pad byte; labl size 7 (4 + 2 + NUL), padded to 8")
case_cues("cues_and_info", [X[:2]], 1000, "i16", [(1, "mark")],
          "cue, then LIST/adtl, then LIST/INFO", tags=[(b"INAM", b"tone")])
case_cues("cues_empty", [X[:2]], 1000, "i16", [], "no cues: the bytes of a plain file")
bad_cues("cue_negative", [(-1, "")], "a position is at least 0")
bad_cues("cue_past_end", [(3, "")], "2 samples: a position is at most 2")
bad_cues("cue_label_non_ascii", [(0, "café")], "labels are printable ASCII: no e-acute")
bad_cues("cue_label_newline", [(0, "a\nb")], "a line feed is not printable")
bad_cues("cue_label_nul", [(0, "a\u0000b")], "a NUL inside the label would end it early")

cue_recs = []  # (name, bytes, expected [(position, label)] or None, why)


def good_cues(name, data, cues, why):
    cue_recs.append((f"cues_{name}", data, cues, why))


def bad_cues_file(name, data, why):
    cue_recs.append((f"cues_{name}", data, None, why))


def labl(cue_id, body):
    return chunk(b"labl", struct.pack("<I", cue_id) + body)


stereo = fmt_chunk(1, 2, 1000, 16)  # with the 6 bytes of i16: 1 frame of 4 bytes, 2 left over
one = cue_chunk([cue_point(1, 0)])
good_cues("as_written", with_chunks(plain, cue_bytes([(0, "start"), (3, "end")])),
          [(0, "start"), (3, "end")], "the chunks write_wav adds; 3 frames, so 3 is the end")
good_cues("none", plain, [], "no cue chunk: no cues")
good_cues("zero_points", riff([pcm, data, cue_chunk([])]), [], "a cue chunk with a count of 0")
good_cues("before_fmt", riff([cue_chunk([cue_point(5, 1)]), adtl_chunk([(5, b"x")]), pcm, data]),
          [(1, "x")], "cue and LIST/adtl may come before fmt; ID 5 links the label")
good_cues("ids_any_order", riff([pcm, data, cue_chunk([cue_point(9, 2), cue_point(3, 0)]),
                                 adtl_chunk([(3, b"three"), (9, b"nine")])]),
          [(2, "nine"), (0, "three")], "points in the cue chunk's order, labels matched by ID")
good_cues("play_order_zero", riff([pcm, data, cue_chunk([cue_point(1, 2, play=0)])]), [(2, "")],
          "the play-order field is ignored; the sample offset is the position")
good_cues("labels_partial", riff([pcm, data, cue_chunk([cue_point(1, 0), cue_point(2, 1)]),
                                  adtl_chunk([(2, b"b")])]),
          [(0, ""), (1, "b")], "a point without a labl has an empty label")
good_cues("label_no_nul", riff([pcm, data, one, chunk(b"LIST", b"adtl" + labl(1, b"ab"))]),
          [(0, "ab")], "a label without a NUL is the rest of its body")
good_cues("label_after_nul", riff([pcm, data, one, chunk(b"LIST", b"adtl" + labl(1, b"ab\0junk"))]),
          [(0, "ab")], "a label stops at the first NUL")
good_cues("label_empty_body", riff([pcm, data, one, chunk(b"LIST", b"adtl" + labl(1, b""))]),
          [(0, "")], "a labl of just the ID is an empty label")
good_cues("label_latin1", riff([pcm, data, one, adtl_chunk([(1, b"caf\xe9")])]),
          [(0, "café")], "labels are read byte for byte as Latin-1")
note = chunk(b"note", struct.pack("<I", 1) + b"a note\0")
ltxt = chunk(b"ltxt", struct.pack("<II4sHHHH", 1, 2, b"rgn ", 0, 0, 0, 0))
good_cues("note_ltxt_skipped", riff([pcm, data, one, chunk(b"LIST", b"adtl" + note + ltxt + labl(1, b"L\0"))]),
          [(0, "L")], "note and ltxt subchunks are skipped, even ones naming the same ID")
good_cues("two_adtl_lists", riff([pcm, data, cue_chunk([cue_point(1, 0), cue_point(2, 1)]),
                                  adtl_chunk([(1, b"a")]), adtl_chunk([(2, b"b")])]),
          [(0, "a"), (1, "b")], "labels from every LIST/adtl")
good_cues("frames_round_down", riff([stereo, data, cue_chunk([cue_point(1, 1)])]), [(1, "")],
          "stereo i16: 6 data bytes are 1 whole frame, so 1 is the end")
good_cues("with_info", riff([pcm, data, cue_chunk([cue_point(1, 2)]), info_chunk([(b"INAM", b"t")])]),
          [(2, "")], "a LIST/INFO is not read for labels")
bad_cues_file("not_wave", with_chunks(plain, cue_bytes([(0, "")])).replace(b"WAVE", b"AVI ", 1),
              "a RIFF file that is not WAVE")
bad_cues_file("no_fmt", riff([data, one]), "no fmt chunk to give the block align")
bad_cues_file("no_data", riff([pcm, one]), "no data chunk to give the frames")
bad_cues_file("fmt_short", riff([chunk(b"fmt ", struct.pack("<HHII", 1, 1, 1000, 2000)), data]),
              "a fmt chunk of 12 bytes has no block align")
bad_cues_file("block_align_zero", riff([fmt_chunk(1, 1, 1000, 16, block=0), data]), "a block align of 0")
bad_cues_file("two_cue_chunks", riff([pcm, data, one, cue_chunk([cue_point(2, 1)])]), "two cue chunks")
bad_cues_file("cue_size_wrong", riff([pcm, data, chunk(b"cue ", struct.pack("<I", 2) + cue_point(1, 0))]),
              "a count of 2 with 1 point: the size must be 4 + 24 x 2")
bad_cues_file("cue_too_short", riff([pcm, data, chunk(b"cue ", b"\0\0")]), "a cue chunk under 4 bytes has no count")
bad_cues_file("cue_slnt", riff([pcm, data, cue_chunk([cue_point(1, 0, cid=b"slnt")])]),
              "a point in a slnt chunk of a wavl list")
bad_cues_file("cue_chunk_start", riff([pcm, data, cue_chunk([cue_point(1, 0, cstart=12)])]),
              "a non-zero chunk start")
bad_cues_file("cue_block_start", riff([pcm, data, cue_chunk([cue_point(1, 0, bstart=2)])]),
              "a non-zero block start")
bad_cues_file("cue_dup_id", riff([pcm, data, cue_chunk([cue_point(4, 0), cue_point(4, 1)])]), "ID 4 twice")
bad_cues_file("cue_past_end", riff([pcm, data, cue_chunk([cue_point(1, 4)])]), "position 4 of 3 frames")
bad_cues_file("cue_past_end_stereo", riff([stereo, data, cue_chunk([cue_point(1, 2)])]),
              "stereo i16 with 6 data bytes has 1 frame: position 2 is past it")
bad_cues_file("label_no_point", riff([pcm, data, one, adtl_chunk([(2, b"x")])]),
              "a label for ID 2, which has no cue point")
bad_cues_file("label_no_cue_chunk", riff([pcm, data, adtl_chunk([(1, b"x")])]), "a label and no cue chunk")
bad_cues_file("label_twice", riff([pcm, data, one, adtl_chunk([(1, b"a"), (1, b"b")])]), "two labels for ID 1")
bad_cues_file("labl_short", riff([pcm, data, one, chunk(b"LIST", b"adtl" + chunk(b"labl", b"\1\0"))]),
              "a labl of 2 bytes has no full cue ID")
bad_cues_file("labl_past_list", riff([pcm, data, one,
                                      chunk(b"LIST", b"adtl" + b"labl" + struct.pack("<I", 20) + b"\1\0\0\0")]),
              "the labl subchunk says 20 bytes, its LIST has 4 left")
for name, raw, expected, _ in cue_recs:
    if expected is not None and pcm in raw:  # the cue chunks leave the mono i16 audio readable
        with wave.open(io.BytesIO(raw)) as w:
            assert w.readframes(w.getnframes()) == i16, name

for name, _, expected, why in cue_recs:
    c = {"id": f"read_wav_cues.{name}", "op": "read_wav_cues", "args": {"file": f"{name}.wav"}}
    c.update({"error": "invalid_argument", "source": why} if expected is None
             else {"expected": [{"position": p, "label": t} for p, t in expected], "source": why})
    cases.append(c)

doc = {
    "schema": 1,
    "suite": "wav",
    "description": "Writing WAV files in every sample format, and reading WAV files laid out as "
    "SignalForge and other tools write them, from vectors/files, with LIST/INFO text tags and "
    "cue points with LIST/adtl labels (conventions: Signal files, WAV).",
    "cases": cases,
}
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
outputs = {ROOT / "cases" / "wav.json": (head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n").encode()}
for name, data, _, _ in recs + info_recs + cue_recs:
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
