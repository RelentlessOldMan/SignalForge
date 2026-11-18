"""Writes vectors/cases/a_law.json, stdlib only.

A-law companding (conventions: A-law companding; ADR 0249). Exact anchors: 0 -> 0, +-1 -> +-1,
and A = 1 is the identity. Other values are the closed-form two-branch curve (L = 1 + ln A)
evaluated with the standard library's log and exp, checked as a round trip and for continuity
at the knee |x| = 1/A, |y| = 1/L.

Run from the repo root: python vectors/generators/a_law.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def sign(v):
    return (v > 0) - (v < 0)


def comp(v, a):
    big = 1 + math.log(a)
    m = abs(v)
    return sign(v) * (a * m / big if m < 1 / a else (1 + math.log(a * m)) / big)


def expd(v, a):
    big = 1 + math.log(a)
    m = abs(v)
    return sign(v) * (m * big / a if m < 1 / big else math.exp(m * big - 1) / a)


def add(op, cid, x, expected, why, a=None):
    args = {"samples": x}
    if a is not None:
        args["a"] = a
    cases.append({"id": f"a_law.{cid}", "op": op, "args": args, "expected": expected,
                  "tol": TOL, "source": why})


add("a_law_compress", "compress_anchors", [0.0, 1.0, -1.0], [0.0, 1.0, -1.0],
    "0 -> 0, +-1 -> (1 + ln A) / L = +-1 analytically (default A)")
add("a_law_expand", "expand_anchors", [0.0, 1.0, -1.0], [0.0, 1.0, -1.0],
    "the inverse of the anchors (default A)")
ident = [0.5, -0.25, 0.875, -1.0]
add("a_law_compress", "identity", ident, ident, "A = 1: L = 1, every sample linear", a=1.0)
add("a_law_expand", "identity_expand", ident, ident, "A = 1: the identity", a=1.0)
xs = [0.001, -0.005, 0.011, -0.02, 0.1, -0.5, 0.9]
add("a_law_compress", "compress_curve", xs, [comp(v, 87.6) for v in xs],
    "closed-form curve, A = 87.6, both branches", a=87.6)
ys = [0.05, -0.15, 0.17, -0.4, 0.75, 0.99]
add("a_law_expand", "expand_curve", ys, [expd(v, 87.6) for v in ys],
    "closed-form inverse, A = 87.6, both branches", a=87.6)
for a in (87.6, 1.0, 10.0):
    for v in xs + ident:
        assert abs(expd(comp(v, a), a) - v) < 1e-15
    big = 1 + math.log(a)
    assert abs(a * (1 / a) / big - (1 + math.log(a * (1 / a))) / big) < 1e-16
assert abs(comp(1.0, 87.6) - 1) <= 4e-16 and abs(expd(1.0, 87.6) - 1) <= 4e-16
assert any(abs(v) < 1 / 87.6 for v in xs) and any(abs(v) > 1 / 87.6 for v in xs)
assert any(abs(v) < 1 / (1 + math.log(87.6)) for v in ys)


def err(op, cid, why, **args):
    cases.append({"id": f"a_law.{cid}", "op": op, "args": args, "error": "invalid_argument",
                  "source": why})


err("a_law_compress", "a_below_one", "a must be at least 1", samples=[0.5], a=0.5)
err("a_law_compress", "out_of_range", "samples must be within [-1, 1]", samples=[1.5])
err("a_law_expand", "out_of_range_expand", "samples must be within [-1, 1]", samples=[-1.25])
err("a_law_expand", "empty", "samples must not be empty", samples=[])
err("a_law_compress", "nan_sample", "samples must be finite", samples=[0.5, "nan"])

doc = {
    "schema": 1,
    "suite": "a_law",
    "description": "A-law companding (conventions: A-law companding; ADR 0249).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "a_law.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/a_law.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
