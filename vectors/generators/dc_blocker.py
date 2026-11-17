"""Writes vectors/cases/dc_blocker.json, stdlib only.

DC blocker (conventions: DC blocker; ADR 0236). The expected values are the input convolved with
the impulse response h[0] = 1, h[k] = (p - 1) p^(k - 1), in exact rational arithmetic, with
poles that are exact binary fractions.

Run from the repo root: python vectors/generators/dc_blocker.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def direct(x, p):
    h = [Fr(1)] + [(p - 1) * p ** (k - 1) for k in range(1, len(x))]
    return [sum(h[k] * x[n - k] for k in range(n + 1)) for n in range(len(x))]


def add(cid, x, p, why, im=None):
    p = Fr(p)
    re = direct([Fr(v) for v in x], p)
    args = {"samples": [float(v) for v in x] if im is None else {"re": x, "im": im}, "pole": float(p)}
    if im is None:
        expected = [float(v) for v in re]
    else:
        iv = direct([Fr(v) for v in im], p)
        expected = {"re": [float(v) for v in re], "im": [float(v) for v in iv]}
    cases.append({"id": f"dc_blocker.{cid}", "op": "dc_blocker", "args": args,
                  "expected": expected, "tol": TOL, "source": why})
    return re


y = add("constant", [2.0] * 12, 0.75, "a constant 2 from rest: 2 p^n")
assert y == [2 * Fr(3, 4) ** n for n in range(12)]
y = add("pole_zero", [1.0, 3.0, -2.0, 0.5], 0.0, "p = 0: the first difference")
assert y == [1, 2, -5, Fr(5, 2)]
add("mixed", [0.5, 1.5, -1.0, 2.25, 0.0, -0.75, 1.0, 3.0, -2.0, 0.25], 0.9921875,
    "p = 127/128 on mixed data")
add("offset_sine_like", [1.0, 1.5, 1.0, 0.5, 1.0, 1.5, 1.0, 0.5, 1.0, 1.5, 1.0, 0.5], 0.875,
    "a period-4 wave on an offset of 1, p = 7/8")
add("single_sample", [3.0], 0.5, "one sample: itself")
add("complex", [1.0, 0.0, -1.0, 2.0, 0.5], 0.625, "complex samples, p = 5/8",
    im=[0.0, 1.0, 1.0, -0.5, 0.25])


def err(cid, why, **args):
    cases.append({"id": f"dc_blocker.{cid}", "op": "dc_blocker", "args": args,
                  "error": "invalid_argument", "source": why})


err("pole_one", "pole must be below 1", samples=[1.0], pole=1.0)
err("pole_negative", "pole must be at least 0", samples=[1.0], pole=-0.5)
err("empty", "samples must not be empty", samples=[], pole=0.5)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], pole=0.5)

doc = {
    "schema": 1,
    "suite": "dc_blocker",
    "description": "DC blocker (conventions: DC blocker; ADR 0236).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "dc_blocker.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/dc_blocker.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
