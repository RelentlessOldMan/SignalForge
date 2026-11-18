"""Writes vectors/cases/slicer.json, stdlib only.

Slicer (conventions: Slicer; ADR 0294), from the rule: with t = rate (n / fs) and
p = t - floor(t), the output is x[n] where p < duty and 0 otherwise. Every case's positions are
exact binary fractions, so the expected values are exact.

Run from the repo root: python vectors/generators/slicer.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 0.0, "rel": 0.0}
cases = []


def add(cid, x, rate, duty, fs, why):
    y = []
    for n, v in enumerate(x):
        t = Fr(rate) * Fr(n) / Fr(fs)
        assert float(t) == rate * (n / fs)
        y.append(v if t - math.floor(t) < Fr(duty) else 0.0)
    cases.append({"id": f"slicer.{cid}", "op": "slicer",
                  "args": {"samples": x, "rate": rate, "duty": duty, "sample_rate": fs},
                  "expected": y, "tol": TOL, "source": why})
    return y


X = [float(n + 1) for n in range(20)]
y = add("half", X, 0.125, 0.5, 1.0, "8-sample cycle, open for the first 4")
assert y[:8] == [1.0, 2.0, 3.0, 4.0, 0.0, 0.0, 0.0, 0.0]
add("hz", X, 2.0, 0.375, 16.0, "2 Hz at fs 16: 8-sample cycle, open for the first 3")
add("edge_closed", X, 0.25, 0.25, 1.0, "p = 0.25 = duty is closed: only the first of every 4")
add("duty_one", X, 0.125, 1.0, 1.0, "duty 1: the input")
assert add("duty_zero", X, 0.125, 0.0, 1.0, "duty 0: silence") == [0.0] * 20
add("rate_zero", X, 0.0, 0.1, 1.0, "rate 0: stays at p = 0, open")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "rate": 1.0, "duty": 0.5, "sample_rate": 8.0}
    base.update(args)
    cases.append({"id": f"slicer.{cid}", "op": "slicer", "args": base,
                  "error": "invalid_argument", "source": why})


err("duty_high", "duty must be at most 1", duty=1.5)
err("rate_negative", "rate must be at least 0", rate=-1.0)
err("sample_rate_zero", "sample_rate must be positive", sample_rate=0.0)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "slicer",
    "description": "Slicer (conventions: Slicer; ADR 0294).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "slicer.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/slicer.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
