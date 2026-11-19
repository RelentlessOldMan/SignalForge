"""Writes vectors/cases/recurrence_quantification.json, stdlib only.

Recurrence quantification (conventions: Recurrence quantification; ADR 0350): the recurrence
plot of dyadic samples built exactly in rationals, its diagonal runs counted exactly; the
values are ratios of integers.

Run from the repo root: python vectors/generators/recurrence_quantification.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, x, m, radius, delay, min_line, theiler, why):
    q = [Fr(v) for v in x]
    eps = Fr(radius)
    w = len(q) - (m - 1) * delay
    points = recurrent = on_lines = longest = 0
    for s in range(theiler + 1, w):
        row = [max(abs(q[i + s + l * delay] - q[i + l * delay]) for l in range(m)) < eps
               for i in range(w - s)]
        points += len(row)
        runs, run = [], 0
        for hit in row + [False]:
            if hit:
                run += 1
            elif run:
                runs.append(run)
                run = 0
        recurrent += sum(runs)
        on_lines += sum(r for r in runs if r >= min_line)
        longest = max([longest] + runs)
    assert recurrent > 0
    args = {"samples": x, "m": m, "radius": radius}
    if delay != 1:
        args["delay"] = delay
    if min_line != 2:
        args["min_line"] = min_line
    if theiler != 0:
        args["theiler"] = theiler
    expected = {"rate": float(Fr(recurrent, points)),
                "determinism": float(Fr(on_lines, recurrent)), "longest": longest}
    cases.append({"id": f"recurrence_quantification.{cid}", "op": "recurrence_quantification",
                  "args": args, "expected": expected, "tol": TOL, "source": why})
    return expected


e = add("period_three", [0.0, 1.0, 2.0] * 4, 1, 0.5, 1, 2, 0,
        "period 3, twelve samples, m = 1: only the diagonals s = 3, 6, 9 recur, all of them, "
        "with 9 + 6 + 3 = 18 of the 66 points; each is one line, so determinism 1, longest 9")
assert e == {"rate": 18 / 66, "determinism": 1.0, "longest": 9}, e
e = add("isolated", [0.0, 4.0, 1.0, 5.0, 0.25], 1, 0.5, 1, 2, 0,
        "only the pair (0, 4) recurs, alone on its diagonal: rate 1/10, determinism 0, "
        "longest 1")
assert e == {"rate": 0.1, "determinism": 0.0, "longest": 1}, e
add("radius_on_a_distance", [0.0, 1.0, 0.0, 1.0, 0.5, 2.0], 1, 1.0, 1, 2, 0,
    "distances of exactly 1 must not recur")
add("mixed_delay", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75,
                    0.0, 1.5, -0.75, 2.0, 0.5, -1.0], 2, 1.5, 2, 2, 0,
    "eighteen arbitrary dyadic samples, m = 2, delay 2")
rng = random.Random(350)
walk = [0.0]
for _ in range(149):
    walk.append(walk[-1] + rng.choice([-0.25, 0.0, 0.25]))
add("walk", walk, 3, 0.5, 1, 3, 2,
    "a 150-step random walk of quarter steps from random.Random(350), m = 3, lines of 3, "
    "Theiler window 2")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5, 0.0], "m": 2, "radius": 1.0}
    base.update(args)
    cases.append({"id": f"recurrence_quantification.{cid}", "op": "recurrence_quantification",
                  "args": base, "error": "invalid_argument", "source": why})


err("m_zero", "m must be at least 1", m=0)
err("delay_zero", "delay must be at least 1", delay=0)
err("min_line_zero", "min_line must be at least 1", min_line=0)
err("theiler_negative", "theiler must be at least 0", theiler=-1)
err("radius_zero", "radius must be positive", radius=0.0)
err("no_point", "the Theiler window leaves no point", theiler=4)
err("no_recurrence", "nothing is closer than 0.25", samples=[0.0, 1.0, 2.0, 3.0], m=1,
    radius=0.25)
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "recurrence_quantification",
    "description": "Recurrence quantification (conventions: Recurrence quantification; "
    "ADR 0350).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "recurrence_quantification.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/recurrence_quantification.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
