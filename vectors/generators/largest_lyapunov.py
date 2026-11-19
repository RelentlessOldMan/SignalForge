"""Writes vectors/cases/largest_lyapunov.json, stdlib only.

Largest Lyapunov exponent (conventions: Largest Lyapunov exponent; ADR 0354): the nearest
neighbours (lowest index on a tie) and the Chebyshev distances of dyadic samples exact in
rationals; then the mean log distance at each step and its least-squares slope in float.

Run from the repo root: python vectors/generators/largest_lyapunov.py [--check]
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


def add(cid, x, m, steps, delay, theiler, why):
    q = [Fr(v) for v in x]
    w = len(q) - (m - 1) * delay
    p = w - steps

    def dist(a, b):
        return max(abs(q[a + l * delay] - q[b + l * delay]) for l in range(m))

    near = []
    for j in range(p):
        cands = [(dist(i, j), i) for i in range(p) if abs(i - j) > theiler]
        near.append(min(cands)[1])
    div = []
    for s in range(steps + 1):
        d = [dist(j + s, near[j] + s) for j in range(p)]
        logs = [math.log(u) for u in d if u > 0]
        assert logs
        div.append(math.fsum(logs) / len(logs))
    ks = range(steps + 1)
    mx, my = steps / 2, math.fsum(div) / len(div)
    slope = (math.fsum((k - mx) * (v - my) for k, v in zip(ks, div))
             / math.fsum((k - mx) ** 2 for k in ks))
    args = {"samples": x, "m": m, "steps": steps}
    if delay != 1:
        args["delay"] = delay
    if theiler != 0:
        args["theiler"] = theiler
    cases.append({"id": f"largest_lyapunov.{cid}", "op": "largest_lyapunov", "args": args,
                  "expected": {"divergence": div, "exponent": slope}, "tol": TOL,
                  "source": why})
    return near, div, slope


near, div, slope = add("doubling_by_hand", [0.0, 1.0, 1.25, 3.0, 3.5, 7.0], 1, 2, 1, 0,
                       "P = 4 points 0, 1, 1.25, 3: neighbours 1, 2, 1, 2 (ties to the "
                       "lowest); distances at k = 0, 1, 2 checked by hand in the generator")
assert near == [1, 2, 1, 2], near
assert div[0] == math.fsum(map(math.log, [1, 0.25, 0.25, 1.75])) / 4
add("mixed", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75, 0.0,
              1.5, -0.75, 2.0, 0.5, -1.0], 2, 3, 2, 1,
    "eighteen arbitrary dyadic samples, m = 2, delay 2, Theiler window 1, three steps")
rng = random.Random(354)
add("noise", [rng.randint(-32, 32) / 16 for _ in range(120)], 3, 5, 1, 4,
    "120 random sixteenths from random.Random(354), m = 3, five steps, Theiler window 4")
# A dyadic tent map 2 min(x, 1 - x) stays exact; start from an odd multiple of 2^-20.
tent = [Fr(rng.randrange(1, 2**20, 2), 2**20)]
for _ in range(15):
    t = tent[-1]
    tent.append(2 * min(t, 1 - t))
add("tent", [float(t) for t in tent], 1, 3, 1, 1,
    "sixteen exact iterates of the tent map 2 min(x, 1 - x) from a random odd multiple of "
    "2^-20 (random.Random(354))")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5, 0.25, 3.0], "m": 2, "steps": 2}
    base.update(args)
    cases.append({"id": f"largest_lyapunov.{cid}", "op": "largest_lyapunov", "args": base,
                  "error": "invalid_argument", "source": why})


err("m_zero", "m must be at least 1", m=0)
err("steps_zero", "steps must be at least 1", steps=0)
err("delay_zero", "delay must be at least 1", delay=0)
err("theiler_negative", "theiler must be at least 0", theiler=-1)
err("too_few_points", "P = 4 needs a Theiler window of at most 1", theiler=2)
err("all_zero_distance", "a constant record has distance 0 everywhere",
    samples=[1.0, 1.0, 1.0, 1.0, 1.0])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0, 2.0, 3.0])

doc = {
    "schema": 1,
    "suite": "largest_lyapunov",
    "description": "Largest Lyapunov exponent (conventions: Largest Lyapunov exponent; "
    "ADR 0354).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "largest_lyapunov.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/largest_lyapunov.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
