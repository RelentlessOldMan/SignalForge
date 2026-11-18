"""Writes vectors/cases/tape_stop.json, stdlib only.

Tape stop (conventions: Tape stop; ADR 0296). The read position is the running sum of the
speeds 1 - j/L, summed term by term in exact rationals (not the closed form the code uses), and
the linear interpolation is exact too; each output is rounded once.

Run from the repo root: python vectors/generators/tape_stop.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def run(x, start, length):
    fx = [Fr(v) for v in x]
    y = []
    p = Fr(start)
    for n in range(len(x)):
        k = n - start
        if k < 1:
            y.append(x[n])
            continue
        if k >= length:
            y.append(0.0)
            continue
        p += 1 - Fr(k, length)
        i = math.floor(p)
        f = p - i
        y.append(float(fx[i] * (1 - f) + fx[i + 1] * f))
    return y


def add(cid, x, start, length, why):
    y = run(x, start, length)
    cases.append({"id": f"tape_stop.{cid}", "op": "tape_stop",
                  "args": {"samples": x, "start": start, "length": length},
                  "expected": y, "tol": TOL, "source": why})
    return y


RAMP = [float(n) for n in range(24)]
y = add("ramp", RAMP, 4, 8, "a ramp reads back its own position: 4, 4 + 7/8, 4 + 13/8, ...")
assert y[:7] == [0.0, 1.0, 2.0, 3.0, 4.0, 4.875, 5.625]
assert y[12:] == [0.0] * 12
M = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05, 0.9, -0.4, 0.6, -1.0,
     0.7, -0.2, 0.35, -0.85]
add("mixed", M, 2, 13, "start 2, stopping over 13 samples")
add("from_zero", M, 0, 20, "the slowdown starts at the first sample")
assert add("length_one", M, 5, 1, "length 1: silent right after start")[6:] == [0.0] * 14
assert add("past_end", M, 30, 4, "start past the end: the input") == M


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "start": 0, "length": 4}
    base.update(args)
    cases.append({"id": f"tape_stop.{cid}", "op": "tape_stop", "args": base,
                  "error": "invalid_argument", "source": why})


err("length_zero", "length must be at least 1", length=0)
err("start_negative", "start must be at least 0", start=-1)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "tape_stop",
    "description": "Tape stop (conventions: Tape stop; ADR 0296).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "tape_stop.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/tape_stop.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
