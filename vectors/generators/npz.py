"""Writes vectors/cases/npz.json and the .npz files in vectors/files/, using only the standard library.

It does not import NumPy or SignalForge. The ZIP structures are packed here with struct, CRC-32 is
zlib.crc32 and deflated members come from zlib, following conventions: Signal files, NumPy .npz
(ADR 0089). The member .npy bytes are laid out as conventions: Signal files, NumPy .npy describes,
with values from struct. The local and central headers numpy.savez writes (ZIP64 extra fields, a
version needed of 45) are rebuilt here from the ZIP layout; the Python tests also read real
numpy.savez output. 2-D members (ADR 0093) are packed row by row (C order) or column by column
(Fortran order); their expected values are listed flat in C order with the shape.

Run from the repo root: python vectors/generators/npz.py [--check]
With --check it writes nothing and exits 1 unless every file matches what it would write.
"""

import json
import math
import pathlib
import struct
import sys
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOL = {"abs": 0, "rel": 0}
LOCAL, CENTRAL, END = b"PK\x03\x04", b"PK\x01\x02", b"PK\x05\x06"
DATE = 0x0021  # 1980-01-01


def parts(x):
    out = []
    for v in x:
        out += [v.real, v.imag] if isinstance(v, complex) else [v]
    return out


def npy(x, is_complex, descr=None, fmt="<d"):
    """A .npy file: write_npy's layout, or another descr with data packed by fmt."""
    descr = descr or ("<c16" if is_complex else "<f8")
    text = f"{{'descr': '{descr}', 'fortran_order': False, 'shape': ({len(x)},), }}"
    head = (text.ljust(117) + "\n").encode("ascii")
    return b"\x93NUMPY\x01\x00" + struct.pack("<H", 118) + head + b"".join(
        struct.pack(fmt, v) for v in parts(x))


def arg(x):
    def one(v):
        return "nan" if math.isnan(v) else "inf" if v == math.inf else "-inf" if v == -math.inf else v
    if any(isinstance(v, complex) for v in x):
        return {"re": [one(complex(v).real) for v in x], "im": [one(complex(v).imag) for v in x]}
    return [one(v) for v in x]


def member(name, data, *, method=0, level=6, flags=0, version=20, time=0, date=DATE,
           local_extra=b"", central_extra=b"", zip64_local=False, zip64_central=False,
           descriptor=False, crc=None, usize=None, csize=None):
    """One member as (local header + data [+ descriptor], central header without offset)."""
    raw = name if isinstance(name, bytes) else name.encode("ascii")
    stored = data
    if method == 8:
        c = zlib.compressobj(level, zlib.DEFLATED, -15)
        stored = c.compress(data) + c.flush()
    crc = zlib.crc32(data) if crc is None else crc
    usize = len(data) if usize is None else usize
    csize = len(stored) if csize is None else csize
    if descriptor:
        flags |= 8
    lsizes = (0, 0, 0) if descriptor else (crc, csize, usize)
    lextra = local_extra
    if zip64_local:  # numpy.savez's force_zip64: 0xFFFFFFFF sizes and a ZIP64 extra field
        lsizes = (crc, 0xFFFFFFFF, 0xFFFFFFFF)
        lextra = struct.pack("<HHQQ", 1, 16, usize, csize) + local_extra
    local = LOCAL + struct.pack("<HHHHHIIIHH", version, flags, method, time, date, *lsizes,
                                len(raw), len(lextra)) + raw + lextra + stored
    if descriptor:
        local += b"PK\x07\x08" + struct.pack("<III", crc, csize, usize)
    return local, (raw, flags, method, time, date, crc, csize, usize, version, central_extra,
                   zip64_central)


def archive(members, comment=b"", end=None):
    body, central = b"", b""
    for local, (raw, flags, method, time, date, crc, csize, usize, version, cextra, z64) in members:
        offset = len(body)
        body += local
        sizes = (csize, usize)
        if z64:  # every field from the ZIP64 extra: uncompressed size, compressed size, offset
            cextra = struct.pack("<HHQQQ", 1, 24, usize, csize, offset) + cextra
            sizes, offset = (0xFFFFFFFF, 0xFFFFFFFF), 0xFFFFFFFF
        central += CENTRAL + struct.pack("<HHHHHHIIIHHHHHII", version, version, flags, method,
                                         time, date, crc, *sizes, len(raw), len(cextra), 0, 0,
                                         0, 0, offset) + raw + cextra
    n = len(members)
    fields = end or (0, 0, n, n, len(central), len(body))
    return body + central + END + struct.pack("<HHHHIIH", *fields, len(comment)) + comment


cases = []
iq = [1 + 2j, -0.5j, complex(math.inf, 0.25)]
taps = [0.5, -0.25, 0.125]


def write_case(name, arrays, why, error=False):
    c = {"id": f"write_npz.{name}", "op": "write_npz",
         "args": {"arrays": [{"name": k, "x": arg(x)} for k, x in arrays]}}
    if error:
        c.update({"error": "invalid_argument", "source": why})
    else:
        ms = [member(k + ".npy", npy(x, any(isinstance(v, complex) for v in x))) for k, x in arrays]
        c.update({"expected": archive(ms).hex(), "tol": TOL, "source": why})
    cases.append(c)


write_case("two_arrays", [("iq", iq), ("taps", taps)],
           "two stored members in order, then the central directory and the end record")
write_case("empty_archive", [], "no members: the end record alone, 22 bytes")
write_case("empty_array", [("e", [])], "a member of shape (0,)")
write_case("long_name", [("n" * 250, [1.0])], "a 250-character name")
write_case("printable", [("a b~!.x", [2.0])], "spaces and punctuation are allowed")
for n, (bad_name, why) in enumerate((("", "an empty name"), ("a/b", "no /"),
                                     ("a\\b", "no backslash"), ("é", "not ASCII"),
                                     ("n" * 251, "over 250 characters"),
                                     ("tab\there", "a control character"))):
    write_case(f"bad_name_{n}", [(bad_name, [1.0])], why, error=True)

recs = []  # (name, bytes, expected or None, why)


def good(name, raw, arrays, why):
    recs.append((name, raw, [{"name": k, "x": arg(x)} for k, x in arrays], why))


def bad(name, raw, why):
    recs.append((name, raw, None, why))


A, B = npy(taps, False), npy(iq, True)
good("stored", archive([member("taps.npy", A), member("iq.npy", B)]), [("taps", taps), ("iq", iq)],
     "the layout write_npz writes; member order is kept")
good("savez_like", archive([member("taps.npy", A, version=45, time=0x6000, date=0x5A6E,
                                   zip64_local=True)]), [("taps", taps)],
     "as numpy.savez writes: version 45, a timestamp, 0xFFFFFFFF sizes and a ZIP64 extra field "
     "in the local header, real sizes in the central one")
good("deflated", archive([member("taps.npy", A, method=8, level=9, flags=2),
                          member("iq.npy", B, method=8, level=1, flags=6)]),
     [("taps", taps), ("iq", iq)], "deflate at levels 9 and 1 from zlib, as numpy.savez_compressed")
good("central_zip64", archive([member("taps.npy", A, version=45, zip64_central=True)]),
     [("taps", taps)], "every size and the offset from the central ZIP64 extra field, in order")
good("data_descriptor", archive([member("iq.npy", B, method=8, descriptor=True)]), [("iq", iq)],
     "flag bit 3: the local header has no sizes; the central directory has them")
good("utf8_name", archive([member("été.npy".encode(), A, flags=0x800)]),
     [("été", taps)], "flag bit 11: the name is UTF-8")
good("comment", archive([member("taps.npy", A)], comment=b"written by hand"),
     [("taps", taps)], "an archive comment after the end record")
good("other_extra", archive([member("taps.npy", A, local_extra=struct.pack("<HHBI", 0x5455, 5, 1, 0),
                                    central_extra=struct.pack("<HHBI", 0x5455, 5, 1, 0))]),
     [("taps", taps)], "an extended-timestamp extra field, skipped by its lengths")
x32 = [0.5, -1.5, 2.0**-149]
good("narrow_dtypes", archive([member("f.npy", npy(x32, False, "<f4", "<f")),
                               member("z.npy", npy([complex(0.25, -2.0**-149)], True, ">c8", ">f"))]),
     [("f", x32), ("z", [complex(0.25, -2.0**-149)])], "members of '<f4' and '>c8', as read_npy reads them")
good("empty", archive([]), [], "the end record alone: no arrays")

one = [member("taps.npy", A)]
CD, AT = 46 + 8, 30 + 8 + len(A)  # the central directory's size and offset for one taps.npy
bad("not_zip", A, "a .npy file is not an archive: no end record")
bad("truncated", archive(one)[:-1], "the end record is cut short")
bad("encrypted", archive([member("taps.npy", A, flags=1)]), "flag bit 0: encrypted")
bad("bzip2", archive([member("taps.npy", A, method=12)]), "method 12 (bzip2) is not read")
bad("deflate64", archive([member("taps.npy", A, method=9)]), "method 9 (Deflate64) is not read")
bad("multi_disk", archive(one, end=(1, 0, 1, 1, CD, AT)),
    "disk number 1")
bad("counts_differ", archive(one, end=(0, 0, 0, 1, CD, AT)), "counts 0 and 1")
bad("zip64_end", archive(one, end=(0, 0, 0xFFFF, 0xFFFF, CD, AT)),
    "a count of 0xFFFF needs the ZIP64 end record")
bad("cd_past_end", archive(one, end=(0, 0, 1, 1, CD + 1, AT)),
    "the central directory runs into the end record")
bad("bad_crc", archive([member("taps.npy", A, crc=zlib.crc32(A) ^ 1)]), "the CRC-32 is off by one bit")
bad("stored_size", archive([member("taps.npy", A, usize=len(A) + 1)]),
    "a stored member whose sizes differ")
bad("deflate_short", archive([member("taps.npy", A, method=8, usize=len(A) + 1)]),
    "inflates to one byte fewer than its size")
bad("deflate_long", archive([member("taps.npy", A, method=8, usize=len(A) - 1)]),
    "inflates to one byte more than its size")
garbage = b"\xff" * 16  # BFINAL 1, block type 3: reserved
loc, cen = member("taps.npy", A)
loc = loc[:8] + struct.pack("<H", 8) + loc[10:18] + struct.pack("<I", 16) + loc[22:38] + garbage
cen = cen[:2] + (8,) + cen[3:6] + (16,) + cen[7:]
bad("invalid_deflate", archive([(loc, cen)]), "block type 3 is reserved: not valid deflate data")
bad("not_npy", archive([member("taps.txt", A)]), "a member that is not a .npy array")
bad("empty_key", archive([member(".npy", A)]), "a member named just .npy")
bad("duplicate", archive([member("taps.npy", A), member("taps.npy", B)]), "taps twice")
bad("latin1_name", archive([member("é.npy".encode("latin-1"), A)]),
    "a non-ASCII name without flag bit 11")
bad("bad_utf8", archive([member(b"\xc3.npy", A, flags=0x800)]), "flag bit 11 with invalid UTF-8")
bad("bad_member", archive([member("b.npy", npy([1], False, "|b1", "<B"))]),
    "a boolean member: read_npy rejects it")
bad("zip64_no_extra", archive([member("taps.npy", A, csize=0xFFFFFFFF)]),
    "a 0xFFFFFFFF size with no ZIP64 extra field")
loc, cen = member("taps.npy", A)
bad("no_local_header", archive([(b"XX" + loc[2:], cen)]), "the offset does not point at a local header")


def npy2(rows, ncols, descr=None, fmt="<d", fortran=False):
    """A 2-D .npy file: write_npy's layout for C order, or another descr or Fortran order."""
    is_complex = any(isinstance(v, complex) for r in rows for v in r)
    descr = descr or ("<c16" if is_complex else "<f8")
    text = (f"{{'descr': '{descr}', 'fortran_order': {fortran}, "
            f"'shape': ({len(rows)}, {ncols}), }}")
    head = (text.ljust(117) + "\n").encode("ascii")
    items = ([rows[i][j] for j in range(ncols) for i in range(len(rows))] if fortran
             else [v for r in rows for v in r])
    return b"\x93NUMPY\x01\x00" + struct.pack("<H", 118) + head + b"".join(
        struct.pack(fmt, v) for v in parts(items))


def rec2(name, rows, ncols):
    return {"name": name, "shape": [len(rows), ncols], "x": arg([v for r in rows for v in r])}


def write2(name, arrays, why):
    """arrays: (key, 1-D list) or (key, rows, ncols) for a 2-D member."""
    args, ms = [], []
    for a in arrays:
        if len(a) == 2:
            args.append({"name": a[0], "x": arg(a[1])})
            ms.append(member(a[0] + ".npy", npy(a[1], any(isinstance(v, complex) for v in a[1]))))
        else:
            args.append(rec2(*a))
            ms.append(member(a[0] + ".npy", npy2(a[1], a[2])))
    cases.append({"id": f"write_npz.{name}", "op": "write_npz", "args": {"arrays": args},
                  "expected": archive(ms).hex(), "tol": TOL, "source": why})


BANK = [[0.5, -0.25, 0.125], [1.0, 0.0, -1.0]]
CBANK = [[1 + 1j, -2.0 + 0j], [0.5j, complex(math.inf, -1)]]
write2("matrix_member", [("bank", BANK, 3)], "a (2, 3) member in C order, numpy.savez's layout")
write2("mixed_members", [("taps", taps), ("bank", CBANK, 2)],
       "a 1-D member, then a complex (2, 2) member, in order")
write2("empty_matrix", [("e", [], 3), ("f", [[], []], 0)], "members of shape (0, 3) and (2, 0)")


def good2(name, raw, records, why):
    recs.append((name, raw, records, why))


good2("matrix", archive([member("bank.npy", npy2(BANK, 3))]), [rec2("bank", BANK, 3)],
      "a stored (2, 3) float64 member")
good2("mixed_fortran", archive([member("taps.npy", A),
                                member("bank.npy", npy2(CBANK, 2, ">c8", ">f", True), method=8)]),
      [{"name": "taps", "x": arg(taps)}, rec2("bank", CBANK, 2)],
      "a 1-D member next to a deflated big-endian complex64 member in Fortran order")
I16 = [[1, -2], [32767, -32768], [0, 5]]
good2("savez_like_matrix", archive([member("m.npy", npy2(I16, 2, "<i2", "<h"), version=45,
                                           zip64_central=True)]),
      [rec2("m", [[float(v) for v in r] for r in I16], 2)],
      "an int16 (3, 2) member with numpy.savez's ZIP64 central extra field")
good2("zero_rows_member", archive([member("z.npy", npy2([], 4))]), [rec2("z", [], 4)],
      "a member of shape (0, 4): no data")


def odd_npy(shape, items):
    text = f"{{'descr': '<f8', 'fortran_order': False, 'shape': {shape}, }}"
    return b"\x93NUMPY\x01\x00" + struct.pack("<H", 118) + (text.ljust(117) + "\n").encode() + b"".join(
        struct.pack("<d", v) for v in items)


bad("three_dim_member", archive([member("taps.npy", A), member("c.npy", odd_npy("(1, 2, 2)", [0.0] * 4))]),
    "a (1, 2, 2) member: only 1-D and 2-D members are read")
bad("zero_dim_member", archive([member("s.npy", odd_npy("()", [0.5]))]), "a 0-D member")
bad("member_dimension_too_big", archive([member("w.npy", odd_npy("(0, 2147483592)", []))]),
    "a dimension one beyond 2147483591")
bad("matrix_data_short", archive([member("m.npy", odd_npy("(2, 3)", [0.0] * 5))]),
    "40 data bytes for shape (2, 3)")

for name, _, expected, why in recs:
    c = {"id": f"read_npz.{name}", "op": "read_npz", "args": {"file": f"{name}.npz"}}
    c.update({"error": "invalid_argument", "source": why} if expected is None
             else {"expected": expected, "tol": TOL, "source": why})
    cases.append(c)

doc = {
    "schema": 1,
    "suite": "npz",
    "description": "Writing NumPy .npz archives, and reading them as numpy.savez, "
    "numpy.savez_compressed and other ZIP writers lay them out, from vectors/files, 1-D and "
    "2-D members (conventions: Signal files, NumPy .npz).",
    "cases": cases,
}
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
outputs = {ROOT / "cases" / "npz.json": (head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n").encode()}
for name, raw, _, _ in recs:
    outputs[ROOT / "files" / f"{name}.npz"] = raw

if "--check" in sys.argv[1:]:
    stale = [p for p, b in outputs.items() if not p.is_file() or p.read_bytes() != b]
    stale += [p for p in (ROOT / "files").glob("*.npz") if p not in outputs]
    if stale:
        sys.exit("out of date (run python vectors/generators/npz.py): "
                 + ", ".join(str(p.relative_to(ROOT)) for p in stale))
    print(f"{len(outputs)} files are up to date")
    sys.exit(0)
for p, b in outputs.items():
    p.write_bytes(b)
print(f"wrote {len(outputs)} files ({len(cases)} cases)")
