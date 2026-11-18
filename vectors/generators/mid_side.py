"""Writes vectors/cases/mid_side.json, stdlib only.

Mid/side coding (conventions: Mid/side coding; ADR 0264). The inputs are binary fractions, so
the expected values, computed in exact rationals, are exact doubles.

Run from the repo root: python vectors/generators/mid_side.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 0.0}
cases = []


def enc(cid, left, right, why):
    a, b = [Fr(v) for v in left], [Fr(v) for v in right]
    mid = [(p + q) / 2 for p, q in zip(a, b)]
    side = [(p - q) / 2 for p, q in zip(a, b)]
    cases.append({"id": f"mid_side.{cid}", "op": "mid_side_encode",
                  "args": {"left": left, "right": right},
                  "expected": {"mid": [float(v) for v in mid], "side": [float(v) for v in side]},
                  "tol": TOL, "source": why})
    return mid, side


def dec(cid, mid, side, why):
    m, s = [Fr(v) for v in mid], [Fr(v) for v in side]
    left = [p + q for p, q in zip(m, s)]
    right = [p - q for p, q in zip(m, s)]
    cases.append({"id": f"mid_side.{cid}", "op": "mid_side_decode",
                  "args": {"mid": mid, "side": side},
                  "expected": {"left": [float(v) for v in left],
                               "right": [float(v) for v in right]},
                  "tol": TOL, "source": why})
    return left, right


L = [1.0, -0.5, 0.25, 3.0, 0.0]
R = [1.0, 0.5, -0.75, 1.0, -2.0]
mid, side = enc("encode", L, R, "mid = (l + r)/2, side = (l - r)/2")
assert mid[0] == 1 and side[0] == 0 and mid[1] == 0 and side[1] == Fr(-1, 2)
left, right = dec("round_trip", [float(v) for v in mid], [float(v) for v in side],
                  "decoding the encode case gives back left and right")
assert left == [Fr(v) for v in L] and right == [Fr(v) for v in R]
enc("mono", [0.5, -1.5], [0.5, -1.5], "identical channels: side is zero")
enc("opposite", [2.0, -0.25], [-2.0, 0.25], "opposite channels: mid is zero")
dec("decode", [1.0, 0.0, -0.5], [0.25, -1.0, -0.5], "left = m + s, right = m - s")


def err(cid, op, why, **args):
    cases.append({"id": f"mid_side.{cid}", "op": op, "args": args,
                  "error": "invalid_argument", "source": why})


err("encode_lengths", "mid_side_encode", "left and right must have the same length",
    left=[1.0, 2.0], right=[1.0])
err("encode_empty", "mid_side_encode", "left must not be empty", left=[], right=[])
err("encode_nan", "mid_side_encode", "right must be finite", left=[1.0], right=["nan"])
err("decode_lengths", "mid_side_decode", "mid and side must have the same length",
    mid=[1.0], side=[1.0, 2.0])
err("decode_inf", "mid_side_decode", "mid must be finite", mid=["inf"], side=[1.0])

doc = {
    "schema": 1,
    "suite": "mid_side",
    "description": "Mid/side coding (conventions: Mid/side coding; ADR 0264).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "mid_side.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/mid_side.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
