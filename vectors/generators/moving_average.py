"""Writes vectors/cases/moving_average.json, stdlib only.

Moving average (conventions: Moving average; ADR 0241). The expected values are exact rational
means over each trailing window (zeros before 0, always divided by N); a constant a gives
a min(n + 1, N) / N and a ramp n gives n - (N - 1) / 2 once the window is full.

Run from the repo root: python vectors/generators/moving_average.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def ma(x, n_w):
    return [sum(x[max(0, n - n_w + 1) : n + 1]) / Fr(n_w) for n in range(len(x))]


def add(cid, x, n_w, why, im=None):
    re = ma([Fr(v) for v in x], n_w)
    args = {"samples": x if im is None else {"re": x, "im": im}, "length": n_w}
    if im is None:
        expected = [float(v) for v in re]
    else:
        expected = {"re": [float(v) for v in re], "im": [float(v) for v in ma([Fr(v) for v in im], n_w)]}
    cases.append({"id": f"moving_average.{cid}", "op": "moving_average", "args": args,
                  "expected": expected, "tol": TOL, "source": why})
    return re


y = add("constant", [-3.0] * 7, 4, "constant -3: -3 min(n + 1, 4) / 4")
assert y == [Fr(-3 * min(n + 1, 4), 4) for n in range(7)]
y = add("ramp", [float(n) for n in range(10)], 5, "ramp n: n - 2 once the window is full")
assert y[4:] == [Fr(n) - 2 for n in range(4, 10)]
add("mixed", [0.5, 1.5, -1.0, 2.25, 0.0, -0.75, 1.0, 3.0, -2.0, 0.25], 3, "mixed data, N = 3")
y = add("length_one", [1.5, -2.0, 0.0], 1, "N = 1: x itself")
assert y == [Fr(3, 2), -2, 0]
add("long_window", [1.0, 2.0, 3.0], 8, "window longer than the input")
add("complex", [3.0, 0.0, -1.0, 2.0], 2, "complex samples", im=[4.0, 1.0, 1.0, -2.0])


def err(cid, why, **args):
    cases.append({"id": f"moving_average.{cid}", "op": "moving_average", "args": args,
                  "error": "invalid_argument", "source": why})


err("length_zero", "length must be at least 1", samples=[1.0], length=0)
err("empty", "samples must not be empty", samples=[], length=2)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], length=2)

doc = {
    "schema": 1,
    "suite": "moving_average",
    "description": "Moving average (conventions: Moving average; ADR 0241).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "moving_average.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/moving_average.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
