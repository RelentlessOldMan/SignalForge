"""Writes vectors/cases/octave_up.json, stdlib only.

Octave-up effect (conventions: Octave-up effect; ADR 0289). The DC blocker recurrence of
ADR 0236, y[n] = (r[n] - r[n-1]) + pole y[n-1] from rest, runs on r = |x| in exact rationals and
is rounded once; the dry/wet blend x (1 - mix) + wet mix is stdlib floats.

Run from the repo root: python vectors/generators/octave_up.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-12}
cases = []


def blocker(r, pole):
    p, xp, yp, out = Fr(pole), Fr(0), Fr(0), []
    for v in r:
        v = Fr(v)
        yp = (v - xp) + p * yp
        xp = v
        out.append(float(yp))
    return out


def add(cid, x, pole, mix, why):
    wet = blocker([abs(v) for v in x], pole)
    y = [v * (1 - mix) + w * mix for v, w in zip(x, wet)]
    cases.append({"id": f"octave_up.{cid}", "op": "octave_up",
                  "args": {"samples": x, "pole": pole, "mix": mix},
                  "expected": y, "tol": TOL, "source": why})
    return wet


# A sine at fs/8: |x| repeats every 4 samples, so its spectrum is at fs/4, an octave up.
S8 = [math.sin(2 * math.pi * n / 8) for n in range(16)]
wet = add("sine_wet", S8, 0.0, 1.0, "sine at fs/8, pole 0: first difference of |x|, period 4")
assert all(abs(wet[n] - wet[n + 4]) < 1e-15 for n in range(1, 12))
add("sine_blend", S8, 0.9, 0.5, "sine at fs/8, pole 0.9, half wet")
M = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05]
add("mixed", M, 0.995, 0.75, "pole 0.995, three-quarters wet")
assert add("dry", M, 0.5, 0.0, "mix 0: the input") is not None


def err(cid, why, **args):
    base = {"samples": [1.0, -2.0], "pole": 0.5, "mix": 0.5}
    base.update(args)
    cases.append({"id": f"octave_up.{cid}", "op": "octave_up", "args": base,
                  "error": "invalid_argument", "source": why})


err("pole_one", "pole must be below 1", pole=1.0)
err("mix_negative", "mix must be at least 0", mix=-0.1)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "octave_up",
    "description": "Octave-up effect (conventions: Octave-up effect; ADR 0289).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "octave_up.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/octave_up.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
