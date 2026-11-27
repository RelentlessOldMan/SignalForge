"""Writes vectors/cases/moving_rms.json, stdlib only.

Moving RMS (conventions: Moving RMS; ADR 0239). The expected values are the exact rational mean
of |x|^2 over each trailing window (zeros before 0, always divided by N), then a square root;
a constant a gives |a| sqrt(min(n + 1, N) / N).

Run from the repo root: python vectors/generators/moving_rms.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def rms(sq, n_w):
    return [math.sqrt(sum(sq[max(0, n - n_w + 1) : n + 1]) / n_w) for n in range(len(sq))]


def add(cid, x, n_w, why, im=None):
    re = [Fr(v) for v in x]
    iv = [Fr(v) for v in im] if im is not None else [Fr(0)] * len(x)
    y = rms([a * a + b * b for a, b in zip(re, iv)], n_w)
    args = {"samples": x if im is None else {"re": x, "im": im}, "length": n_w}
    cases.append({"id": f"moving_rms.{cid}", "op": "moving_rms", "args": args, "expected": y,
                  "tol": TOL, "source": why})
    return y


y = add("constant", [-3.0] * 7, 4, "constant -3: 3 sqrt(min(n + 1, 4) / 4)")
assert all(abs(v - 3 * math.sqrt(min(n + 1, 4) / 4)) < 1e-15 for n, v in enumerate(y))
add("mixed", [0.5, 1.5, -1.0, 2.25, 0.0, -0.75, 1.0, 3.0, -2.0, 0.25], 3, "mixed data, N = 3")
y = add("length_one", [1.5, -2.0, 0.0], 1, "N = 1: |x|")
assert y == [1.5, 2.0, 0.0]
add("long_window", [1.0, 2.0, 3.0], 8, "window longer than the input")
add("complex", [3.0, 0.0, -1.0, 2.0], 2, "complex samples", im=[4.0, 1.0, 1.0, -2.0])


REL = {"abs": 0.0, "rel": 1e-13}  # values near 2^-1000: an absolute tolerance would pass anything
MIXED = [0.5, 1.5, -1.0, 2.25, 0.0, -0.75, 1.0, 3.0, -2.0, 0.25]
base = rms([Fr(v) ** 2 for v in MIXED], 3)
for word, k, how in (("huge", 1000, "overflow a double"), ("tiny", -1000, "underflow to 0")):
    assert all(v * 2.0**k / 2.0**k == v for v in MIXED)
    cases.append({"id": f"moving_rms.{word}", "op": "moving_rms",
                  "args": {"samples": [v * 2.0**k for v in MIXED], "length": 3},
                  "expected": [v * 2.0**k for v in base], "tol": REL,
                  "source": f"mixed times 2^{k}: the squares {how}, but an RMS scales with the "
                  "samples and a power of 2 scales exactly, so mixed's values times 2^" + str(k)})
B = 2.0**1000
cases.append({"id": "moving_rms.wide", "op": "moving_rms",
              "args": {"samples": [B, B, 3 / B, 4 / B], "length": 2},
              "expected": [B * math.sqrt(0.5), B, B * math.sqrt(0.5), 5 / B * math.sqrt(0.5)],
              "tol": REL,
              "source": "N = 2 over 2^1000, 2^1000, 3 x 2^-1000, 4 x 2^-1000: windows "
              "2^1000/sqrt 2, 2^1000, 2^1000/sqrt 2 (the 3 x 2^-1000 is below the last bit), and "
              "5 x 2^-1000/sqrt 2; no one scale keeps both the first and last windows in range"})


def err(cid, why, **args):
    cases.append({"id": f"moving_rms.{cid}", "op": "moving_rms", "args": args,
                  "error": "invalid_argument", "source": why})


err("length_zero", "length must be at least 1", samples=[1.0], length=0)
err("empty", "samples must not be empty", samples=[], length=2)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], length=2)

doc = {
    "schema": 1,
    "suite": "moving_rms",
    "description": "Moving RMS (conventions: Moving RMS; ADR 0239).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "moving_rms.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/moving_rms.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
