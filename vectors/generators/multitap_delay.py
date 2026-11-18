"""Writes vectors/cases/multitap_delay.json, stdlib only.

Multi-tap delay (conventions: Multi-tap delay; ADR 0300): y[n] = x[n] + sum_k g_k x[n - d_k],
zero before the start, summed in exact rationals and rounded once.

Run from the repo root: python vectors/generators/multitap_delay.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def add(cid, x, delays, gains, why):
    y = []
    for n in range(len(x)):
        v = Fr(x[n])
        for d, g in zip(delays, gains):
            if n >= d:
                v += Fr(g) * Fr(x[n - d])
        y.append(float(v))
    cases.append({"id": f"multitap_delay.{cid}", "op": "multitap_delay",
                  "args": {"samples": x, "delays": delays, "gains": gains},
                  "expected": y, "tol": TOL, "source": why})
    return y


IMP = [1.0] + [0.0] * 11
y = add("impulse", IMP, [3, 5, 8], [0.5, -0.25, 0.125], "an impulse shows each tap at its delay")
assert y == [1.0, 0, 0, 0.5, 0, -0.25, 0, 0, 0.125, 0, 0, 0]
M = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05, 0.9, -0.4, 0.6, -1.0]
add("mixed", M, [2, 7, 11], [0.6, 0.35, -0.2], "three taps on a mixed signal")
add("repeat", M, [4, 4], [0.3, 0.2], "a repeated delay adds its gains")
add("long", M, [1, 40], [0.5, 0.9], "a tap longer than the signal adds nothing")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "delays": [1, 2], "gains": [0.5, 0.25]}
    base.update(args)
    cases.append({"id": f"multitap_delay.{cid}", "op": "multitap_delay", "args": base,
                  "error": "invalid_argument", "source": why})


err("no_taps", "delays must hold at least one tap", delays=[], gains=[])
err("gain_count", "gains must hold one gain per delay", gains=[0.5])
err("delay_zero", "delays must be at least 1", delays=[0, 2])
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "multitap_delay",
    "description": "Multi-tap delay (conventions: Multi-tap delay; ADR 0300).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "multitap_delay.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/multitap_delay.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
