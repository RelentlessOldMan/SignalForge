"""Writes vectors/cases/adsr.json, stdlib only.

ADSR envelope (conventions: ADSR envelope; ADR 0303), from the segments in exact rationals:
held h(n) = n/A, then 1 - (1 - S)(n - A)/D, then S; from the gate G, h(G)(1 - k/R) for
k = n - G < R, then 0. Each value is rounded once.

Run from the repo root: python vectors/generators/adsr.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def env(size, a, d, s, r, g):
    s = Fr(s)

    def held(n):
        if n < a:
            return Fr(n, a)
        if n < a + d:
            return 1 - (1 - s) * Fr(n - a, d)
        return s

    level = held(g)
    out = []
    for n in range(size):
        if n < g:
            out.append(held(n))
        elif n - g < r:
            out.append(level * (1 - Fr(n - g, r)))
        else:
            out.append(Fr(0))
    return [float(v) for v in out]


def add(cid, size, a, d, s, r, g, why):
    y = env(size, a, d, s, r, g)
    cases.append({"id": f"adsr.{cid}", "op": "adsr",
                  "args": {"num_samples": size, "attack": a, "decay": d, "sustain": s,
                           "release": r, "gate": g},
                  "expected": y, "tol": TOL, "source": why})
    return y


y = add("full", 20, 4, 4, 0.5, 4, 12, "every stage: attack 4, decay 4 to 0.5, hold, release 4")
assert y == [0, 0.25, 0.5, 0.75, 1, 0.875, 0.75, 0.625, 0.5, 0.5, 0.5, 0.5,
             0.5, 0.375, 0.25, 0.125, 0, 0, 0, 0]
add("odd_lengths", 30, 3, 5, 0.3, 7, 15, "lengths that are not powers of two")
y = add("early_release", 12, 6, 2, 0.4, 4, 3, "let go during the attack, from 1/2")
assert y[3:8] == [0.5, 0.375, 0.25, 0.125, 0.0]
add("in_decay", 14, 2, 6, 0.2, 3, 5, "let go during the decay")
assert add("instant", 6, 0, 0, 0.7, 0, 3, "no attack, decay or release") == [0.7] * 3 + [0.0] * 3
add("never_released", 10, 2, 2, 0.6, 3, 50, "a gate past the end: the key is held throughout")


def err(cid, why, **args):
    base = {"num_samples": 8, "attack": 2, "decay": 2, "sustain": 0.5, "release": 2, "gate": 5}
    base.update(args)
    cases.append({"id": f"adsr.{cid}", "op": "adsr", "args": base,
                  "error": "invalid_argument", "source": why})


err("sustain_high", "sustain must be at most 1", sustain=1.5)
err("attack_negative", "attack must be at least 0", attack=-1)
err("gate_negative", "gate must be at least 0", gate=-1)
err("no_samples", "num_samples must be at least 1", num_samples=0)

doc = {
    "schema": 1,
    "suite": "adsr",
    "description": "ADSR envelope (conventions: ADSR envelope; ADR 0303).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "adsr.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/adsr.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
