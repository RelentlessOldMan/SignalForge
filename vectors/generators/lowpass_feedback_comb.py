"""Writes vectors/cases/lowpass_feedback_comb.json, stdlib only.

Damped feedback comb (conventions: Damped feedback comb; ADR 0297), the recurrence
f[n] = (1 - d) y[n - D] + d f[n - 1], y[n] = x[n] + g f[n], zero before the start, run in exact
rationals and rounded once.

Run from the repo root: python vectors/generators/lowpass_feedback_comb.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-12}
cases = []


def run(x, dl, g, d):
    g, d = Fr(g), Fr(d)
    y, f = [], Fr(0)
    for n, v in enumerate(x):
        f = (1 - d) * (y[n - dl] if n >= dl else 0) + d * f
        y.append(Fr(v) + g * f)
    return [float(v) for v in y]


def add(cid, x, dl, g, d, why):
    y = run(x, dl, g, d)
    cases.append({"id": f"lowpass_feedback_comb.{cid}", "op": "lowpass_feedback_comb",
                  "args": {"samples": x, "delay": dl, "feedback": g, "damping": d},
                  "expected": y, "tol": TOL, "source": why})
    return y


IMP = [1.0] + [0.0] * 23
y = add("undamped", IMP, 4, 0.5, 0.0, "damping 0: the feedback comb, 0.5^k at n = 4k")
assert y == [0.5 ** (n // 4) if n % 4 == 0 else 0.0 for n in range(24)]
y = add("impulse", IMP, 3, 0.5, 0.5, "impulse, delay 3, feedback 0.5, damping 0.5")
assert y[:5] == [1.0, 0.0, 0.0, 0.25, 0.125]
M = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05, 0.9, -0.4, 0.6, -1.0]
add("mixed", M, 5, -0.8, 0.3, "a negative feedback with damping 0.3")
add("delay_one", M, 1, 0.9, 0.75, "delay 1: the low-pass and the loop share every sample")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "delay": 3, "feedback": 0.5, "damping": 0.5}
    base.update(args)
    cases.append({"id": f"lowpass_feedback_comb.{cid}", "op": "lowpass_feedback_comb",
                  "args": base, "error": "invalid_argument", "source": why})


err("delay_zero", "delay must be at least 1", delay=0)
err("feedback_one", "feedback must satisfy |feedback| < 1", feedback=-1.0)
err("damping_one", "damping must be below 1", damping=1.0)
err("damping_negative", "damping must be at least 0", damping=-0.1)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "lowpass_feedback_comb",
    "description": "Damped feedback comb (conventions: Damped feedback comb; ADR 0297).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "lowpass_feedback_comb.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/lowpass_feedback_comb.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
