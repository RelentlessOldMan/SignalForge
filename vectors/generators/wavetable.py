"""Writes vectors/cases/wavetable.json, stdlib only.

Wavetable oscillator (conventions: Wavetable oscillator; ADR 0308), from the read in exact
rationals: u = frac(f n / fs + phase), p = u L, i = floor(p), r = p - i,
y = T[i](1 - r) + T[(i + 1) mod L] r, rounded once.

Run from the repo root: python vectors/generators/wavetable.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def add(cid, table, fs, size, f, why, phase=None):
    big = len(table)
    p0 = Fr(0 if phase is None else phase)
    y = []
    for n in range(size):
        t = Fr(f) * n / Fr(fs) + p0
        p = (t - math.floor(t)) * big
        i = math.floor(p)
        r = p - i
        y.append(float(Fr(table[i]) * (1 - r) + Fr(table[(i + 1) % big]) * r))
    args = {"table": table, "sample_rate": fs, "num_samples": size, "frequency": f}
    if phase is not None:
        args["phase"] = phase
    cases.append({"id": f"wavetable.{cid}", "op": "wavetable", "args": args, "expected": y,
                  "tol": TOL, "source": why})
    return y


y = add("on_the_points", [0.0, 1.0, 0.0, -1.0], 8000.0, 8, 2000.0,
        "one table entry per sample: the table itself")
assert y == [0.0, 1.0, 0.0, -1.0] * 2
y = add("halfway", [0.0, 1.0, 0.0, -1.0], 8000.0, 8, 1000.0,
        "two samples per entry: the midpoints, wrapping from the last entry to the first")
assert y == [0.0, 0.5, 1.0, 0.5, 0.0, -0.5, -1.0, -0.5]
SHAPE = [0.1, 0.9, 0.4, -0.3, -0.8, -0.2, 0.6]
add("odd_table", SHAPE, 48000.0, 40, 1234.5, "a 7-entry table at 1234.5 Hz", phase=0.3)
add("backwards", SHAPE, 8000.0, 24, -700.0, "a negative frequency reads backwards")
add("constant", [0.25], 8000.0, 4, 1000.0, "a one-entry table is a constant")


def err(cid, why, **args):
    base = {"table": [0.0, 1.0], "sample_rate": 8000.0, "num_samples": 4, "frequency": 1000.0}
    base.update(args)
    cases.append({"id": f"wavetable.{cid}", "op": "wavetable", "args": base,
                  "error": "invalid_argument", "source": why})


err("empty_table", "table must hold at least one entry", table=[])
err("rate_zero", "sample_rate must be positive", sample_rate=0.0)

doc = {
    "schema": 1,
    "suite": "wavetable",
    "description": "Wavetable oscillator (conventions: Wavetable oscillator; ADR 0308).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "wavetable.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/wavetable.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
