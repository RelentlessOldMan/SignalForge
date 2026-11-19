"""Writes vectors/cases/correlation_sum.json, stdlib only.

Correlation sum (conventions: Correlation sum; ADR 0349): the Chebyshev distances of the
embedded pairs of dyadic samples exact in rationals, counted strictly below each dyadic radius;
then the least-squares slope of ln C against ln r in float.

Run from the repo root: python vectors/generators/correlation_sum.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def add(cid, x, m, radii, delay, theiler, why):
    q = [Fr(v) for v in x]
    w = len(q) - (m - 1) * delay
    d = [max(abs(q[j + l * delay] - q[i + l * delay]) for l in range(m))
         for i in range(w) for j in range(i + 1 + theiler, w)]
    c = [Fr(sum(1 for u in d if u < Fr(r)), len(d)) for r in radii]
    assert all(v > 0 for v in c)
    lx = [math.log(r) for r in radii]
    ly = [math.log(v) for v in c]
    mx, my = math.fsum(lx) / len(lx), math.fsum(ly) / len(ly)
    slope = (math.fsum((a - mx) * (b - my) for a, b in zip(lx, ly))
             / math.fsum((a - mx) ** 2 for a in lx))
    args = {"samples": x, "m": m, "radii": radii}
    if delay != 1:
        args["delay"] = delay
    if theiler != 0:
        args["theiler"] = theiler
    cases.append({"id": f"correlation_sum.{cid}", "op": "correlation_sum", "args": args,
                  "expected": {"radii": radii, "values": [float(v) for v in c],
                               "dimension": slope},
                  "tol": TOL, "source": why})
    return c, slope


c, s = add("ramp_by_hand", [0.0, 1.0, 2.0, 3.0], 1, [1.5, 2.5], 1, 0,
           "0, 1, 2, 3: distances 1, 2, 3, 1, 2, 1, so C = 3/6 and 5/6; the slope is "
           "ln(5/3)/ln(5/3) = 1")
assert c == [Fr(1, 2), Fr(5, 6)] and abs(s - 1) < 1e-15
c, s = add("radius_on_a_distance", [0.0, 1.0, 2.0, 3.0], 1, [1.25, 2.0, 3.0], 1, 0,
           "r = 2 and r = 3 sit on distances, which do not count: C = 3/6, 3/6, 5/6")
assert c == [Fr(1, 2), Fr(1, 2), Fr(5, 6)]
c, s = add("theiler", [0.0, 1.0, 2.0, 3.0], 1, [2.5, 3.5], 1, 1,
           "a Theiler window of 1 drops the three neighbours: distances 2, 3, 2, so "
           "C = 2/3 and 1")
assert c == [Fr(2, 3), Fr(1)]
add("mixed_delay", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75,
                    0.0, 1.5, -0.75, 2.0, 0.5, -1.0], 2, [1.0, 2.0, 3.0, 4.5], 2, 0,
    "eighteen arbitrary dyadic samples, m = 2, delay 2")
rng = random.Random(349)
add("noise", [rng.randint(-32, 32) / 16 for _ in range(160)], 3, [0.5, 0.75, 1.0, 1.5, 2.0],
    1, 3, "160 random sixteenths from random.Random(349), m = 3, Theiler window 3")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5], "m": 2, "radii": [1.0, 2.0]}
    base.update(args)
    cases.append({"id": f"correlation_sum.{cid}", "op": "correlation_sum", "args": base,
                  "error": "invalid_argument", "source": why})


err("m_zero", "m must be at least 1", m=0)
err("delay_zero", "delay must be at least 1", delay=0)
err("theiler_negative", "theiler must be at least 0", theiler=-1)
err("one_radius", "two radii are needed", radii=[1.0])
err("radii_not_increasing", "radii must be strictly increasing", radii=[2.0, 2.0])
err("radius_zero", "radii must be positive", radii=[0.0, 1.0])
err("radius_too_small", "no pair is closer than 0.25", radii=[0.25, 1.0])
err("no_pair", "the Theiler window leaves no pair", theiler=3)
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "correlation_sum",
    "description": "Correlation sum (conventions: Correlation sum; ADR 0349).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "correlation_sum.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/correlation_sum.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
