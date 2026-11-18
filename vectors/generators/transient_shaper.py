"""Writes vectors/cases/transient_shaper.json, stdlib only.

Transient shaper (conventions: Transient shaper; ADR 0281): each sample times
(e_fast/e_slow)^amount, 1 where either envelope is 0. The ADR 0238 envelopes are computed in
exact rationals and rounded to floats; the gain is the stdlib ** of their float ratio.

Run from the repo root: python vectors/generators/transient_shaper.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-12}
cases = []


def envelope(mags, c):
    out, prev = [], Fr(0)
    for m in mags:
        m = Fr(m)
        prev = m + Fr(c) * (prev - m)
        out.append(float(prev))
    return out


def gains(mags, fast, slow, amount):
    ef, es = envelope(mags, fast), envelope(mags, slow)
    return [(f / s) ** amount if f > 0 and s > 0 else 1.0 for f, s in zip(ef, es)]


def add(cid, x, fast, slow, amount, why):
    g = gains([abs(v) for v in x], fast, slow, amount)
    cases.append({"id": f"transient_shaper.{cid}", "op": "transient_shaper",
                  "args": {"samples": x, "fast": fast, "slow": slow, "amount": amount},
                  "expected": [v * k for v, k in zip(x, g)], "tol": TOL, "source": why})


BURST = [0.0, 0.0, 1.0, 0.9, -0.8, 0.85, -0.9, 0.8, 0.0, 0.0, 0.5, -0.5]
add("sharpen", BURST, 0.25, 0.875, 1.0, "fast 1/4, slow 7/8, amount 1: onsets raised")
add("soften", BURST, 0.25, 0.875, -0.5, "amount -1/2: onsets lowered")
add("square", BURST, 0.5, 0.75, 2.0, "amount 2")
add("zero_amount", BURST, 0.25, 0.875, 0.0, "amount 0: the input, gain 1 everywhere")
add("instant_fast", [0.5, 1.0, -0.25, 0.0, 2.0], 0.0, 0.5, 1.0,
    "fast 0 follows |x| exactly; a zero sample keeps gain 1")

cre, cim = [0.0, 1.0, 0.5, -0.75, 0.25], [0.0, -1.0, 0.25, 0.5, 0.0]
g = gains([abs(complex(a, b)) for a, b in zip(cre, cim)], 0.25, 0.75, 1.5)
cases.append({"id": "transient_shaper.complex", "op": "transient_shaper",
              "args": {"samples": {"re": cre, "im": cim}, "fast": 0.25, "slow": 0.75,
                       "amount": 1.5},
              "expected": {"re": [v * k for v, k in zip(cre, g)],
                           "im": [v * k for v, k in zip(cim, g)]},
              "tol": TOL, "source": "complex: envelopes of |x|, real gain on both parts"})


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "fast": 0.25, "slow": 0.75, "amount": 1.0}
    base.update(args)
    cases.append({"id": f"transient_shaper.{cid}", "op": "transient_shaper", "args": base,
                  "error": "invalid_argument", "source": why})


err("fast_one", "fast must be below 1", fast=1.0)
err("slow_negative", "slow must be at least 0", slow=-0.5)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "transient_shaper",
    "description": "Transient shaper (conventions: Transient shaper; ADR 0281).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "transient_shaper.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/transient_shaper.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
