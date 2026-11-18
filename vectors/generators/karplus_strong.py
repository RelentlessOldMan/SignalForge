"""Writes vectors/cases/karplus_strong.json, stdlib only.

Karplus-Strong pluck (conventions: Karplus-Strong pluck; ADR 0304): the excitation zero-padded
to length, y[n] = e[n] + decay (y[n - D] + y[n - D - 1]) / 2, zero before the start, run in
exact rationals and rounded once.

Run from the repo root: python vectors/generators/karplus_strong.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-12}
cases = []


def add(cid, e, d, size, g, why):
    y = []
    for n in range(size):
        v = Fr(e[n]) if n < len(e) else Fr(0)
        a = y[n - d] if n >= d else 0
        b = y[n - d - 1] if n >= d + 1 else 0
        y.append(v + Fr(g) * (a + b) / 2)
    out = [float(v) for v in y]
    cases.append({"id": f"karplus_strong.{cid}", "op": "karplus_strong",
                  "args": {"excitation": e, "delay": d, "length": size, "decay": g},
                  "expected": out, "tol": TOL, "source": why})
    return out


y = add("impulse", [1.0], 2, 10, 1.0, "an impulse, delay 2, no loss: the averaged echoes")
assert y[:7] == [1.0, 0.0, 0.5, 0.5, 0.25, 0.5, 0.375]
NOISE = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6]
add("burst", NOISE, 8, 40, 0.98, "an 8-sample burst into an 8-sample loop, decay 0.98")
add("short_loop", NOISE[:3], 3, 24, 0.9, "a 3-sample burst into a 3-sample loop")
add("silent_loop", NOISE, 4, 12, 0.0, "decay 0: the excitation, zero-padded")
add("delay_one", [1.0, -1.0], 1, 12, 0.75, "delay 1: the shortest loop")


def err(cid, why, **args):
    base = {"excitation": [1.0, 2.0], "delay": 2, "length": 8, "decay": 0.9}
    base.update(args)
    cases.append({"id": f"karplus_strong.{cid}", "op": "karplus_strong", "args": base,
                  "error": "invalid_argument", "source": why})


err("delay_zero", "delay must be at least 1", delay=0)
err("decay_high", "decay must be at most 1", decay=1.01)
err("excitation_long", "the excitation must fit in length", length=1)
err("empty", "the excitation must not be empty", excitation=[])

doc = {
    "schema": 1,
    "suite": "karplus_strong",
    "description": "Karplus-Strong pluck (conventions: Karplus-Strong pluck; ADR 0304).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "karplus_strong.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/karplus_strong.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
