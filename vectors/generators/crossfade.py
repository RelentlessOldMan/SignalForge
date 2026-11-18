"""Writes vectors/cases/crossfade.json, stdlib only.

Crossfade (conventions: Crossfade; ADR 0263). Linear cases use overlap 3 (t = 1/4, 1/2, 3/4)
in exact rationals; cosine cases use (1 - cos(pi t)) / 2 with the stdlib math.cos.

Run from the repo root: python vectors/generators/crossfade.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 0.0}
cases = []


def weight(k, length, shape):
    t = Fr(k + 1, length + 1)
    if shape == "linear":
        return t
    return (1 - math.cos(math.pi * float(t))) / 2


def join(a, b, length, shape):
    head = len(a) - length
    mid = []
    for k in range(length):
        w = weight(k, length, shape)
        mid.append(a[head + k] * (1 - w) + b[k] * w)
    return a[:head] + mid + b[length:]


def add(cid, a, b, length, why, shape=None):
    y = join([Fr(v) for v in a], [Fr(v) for v in b], length, shape or "linear")
    args = {"a": a, "b": b, "overlap": length}
    if shape is not None:
        args["shape"] = shape
    cases.append({"id": f"crossfade.{cid}", "op": "crossfade", "args": args,
                  "expected": [float(v) for v in y], "tol": TOL, "source": why})
    return y


y = add("linear", [1.0, 1.0, 1.0, 1.0, 1.0], [0.0, 0.0, 0.0, 0.0], 3,
        "linear, overlap 3: 1, 1, 3/4, 1/2, 1/4, 0")
assert y == [1, 1, Fr(3, 4), Fr(1, 2), Fr(1, 4), 0]
y = add("concatenate", [0.5, -0.25], [1.5, 2.0, -1.0], 0, "overlap 0: concatenation")
assert y == [Fr(1, 2), Fr(-1, 4), Fr(3, 2), 2, -1]
add("full_overlap", [2.0, -2.0, 4.0], [1.0, 3.0, -1.0], 3, "overlap the whole of both")
y = add("cosine", [1.0, 1.0, 1.0, 1.0], [-1.0, -1.0, -1.0, -1.0, -1.0], 3,
        "cosine, overlap 3: middle sample 1/2 of each", shape="cosine")
assert abs(float(y[2])) < 1e-15
add("cosine_signal", [0.25, -1.0, 1.5, 2.0, -0.5, 0.75], [1.0, -1.25, 0.5, 0.125, 3.0], 4,
    "cosine on two signals", shape="cosine")

are, aim = [1.0, 2.0, -3.0], [0.5, -1.0, 4.0]
bre, bim = [0.0, 1.0, 2.0], [2.0, 0.0, -2.0]
ya = join([complex(r, i) for r, i in zip(are, aim)], [complex(r, i) for r, i in zip(bre, bim)],
          1, "linear")
assert ya[2] == complex(-1.5, 3.0)
cases.append({"id": "crossfade.complex", "op": "crossfade",
              "args": {"a": {"re": are, "im": aim}, "b": {"re": bre, "im": bim}, "overlap": 1},
              "expected": {"re": [v.real for v in ya], "im": [v.imag for v in ya]},
              "tol": TOL, "source": "complex, overlap 1: the shared sample is (a + b)/2"})
ym = join([Fr(1), Fr(1)], [complex(0, 2), complex(0, 2)], 1, "linear")
cases.append({"id": "crossfade.mixed", "op": "crossfade",
              "args": {"a": [1.0, 1.0], "b": {"re": [0.0, 0.0], "im": [2.0, 2.0]}, "overlap": 1},
              "expected": {"re": [complex(v).real for v in ym],
                           "im": [complex(v).imag for v in ym]},
              "tol": TOL, "source": "real a, complex b: complex out, 1, 1/2 + i, 2i"})


def err(cid, why, **args):
    base = {"a": [1.0, 2.0], "b": [3.0, 4.0], "overlap": 1}
    base.update(args)
    cases.append({"id": f"crossfade.{cid}", "op": "crossfade", "args": base,
                  "error": "invalid_argument", "source": why})


err("overlap_negative", "overlap must be at least 0", overlap=-1)
err("overlap_too_long", "overlap must be at most the length of each input", b=[1.0], overlap=2)
err("bad_shape", "shape must be linear or cosine", shape="square")
err("empty_a", "a must not be empty", a=[], overlap=0)
err("nan_b", "b must be finite", b=[1.0, "nan"])

doc = {
    "schema": 1,
    "suite": "crossfade",
    "description": "Crossfade (conventions: Crossfade; ADR 0263).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "crossfade.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/crossfade.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
