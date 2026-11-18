"""Writes vectors/cases/dispersion_entropy.json, stdlib only.

Dispersion entropy (conventions: Dispersion entropy; ADR 0341): the mean and the population
variance exact in rationals; y = erfc(-(x - mu)/(sigma sqrt 2))/2 with math.erfc; the class
min(c, floor(c y) + 1), asserting every c y is at least 1e-9 from an integer so the classes
cannot differ; exact pattern counts, then -sum p ln p / (m ln c) in float.

Run from the repo root: python vectors/generators/dispersion_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from collections import Counter
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def classes_of(x, c):
    q = [Fr(v) for v in x]
    mu = sum(q, Fr(0)) / len(q)
    sigma = math.sqrt(float(sum(((v - mu) ** 2 for v in q), Fr(0)) / len(q)))
    z = []
    for v in q:
        cy = c * 0.5 * math.erfc(-float(v - mu) / (sigma * math.sqrt(2)))
        assert abs(cy - round(cy)) > 1e-9 or cy < 1e-9, (v, cy)
        z.append(min(c, math.floor(cy) + 1))
    return z


def add(cid, x, m, c, delay, why):
    z = classes_of(x, c)
    windows = len(x) - (m - 1) * delay
    counts = Counter(tuple(z[i + l * delay] for l in range(m)) for i in range(windows))
    h = -math.fsum(n / windows * math.log(n / windows) for n in counts.values())
    v = h / (m * math.log(c))
    args = {"samples": x, "m": m, "classes": c}
    if delay != 1:
        args["delay"] = delay
    cases.append({"id": f"dispersion_entropy.{cid}", "op": "dispersion_entropy", "args": args,
                  "expected": v, "tol": TOL, "source": why})
    return z, v


z, v = add("two_levels", [1.0, -1.0] * 4, 1, 2, 1, "+-1: half the samples in each of two "
           "classes, so 1 exactly")
assert z == [2, 1] * 4 and v == 1.0, (z, v)
z, v = add("alternating_pairs", [1.0, -1.0] * 6, 2, 2, 1, "+-1, m = 2: patterns (2,1) and "
           "(1,2), 6 and 5 times")
assert sorted(Counter(zip(z, z[1:])).values()) == [5, 6]
add("mixed", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75, 0.1,
              1.5, -0.75, 2.0, 0.5, -1.0], 2, 6, 1, "eighteen arbitrary samples, c = 6")
rng = random.Random(341)
add("noise", [rng.randint(-64, 64) / 16 for _ in range(300)], 3, 5, 2,
    "300 random sixteenths from random.Random(341), m = 3, c = 5, delay 2")
add("one_pattern", [0.3, -0.7, 1.1], 3, 3, 1, "three samples, m = 3: one pattern, so 0")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5], "m": 2, "classes": 3}
    base.update(args)
    cases.append({"id": f"dispersion_entropy.{cid}", "op": "dispersion_entropy", "args": base,
                  "error": "invalid_argument", "source": why})


err("m_zero", "m must be at least 1", m=0)
err("m_eleven", "m must be at most 10", m=11)
err("one_class", "classes must be at least 2", classes=1)
err("classes_65", "classes must be at most 64", classes=65)
err("delay_zero", "delay must be at least 1", delay=0)
err("too_short", "no pattern fits", m=3, delay=3)
err("constant", "the samples must vary", samples=[2.0, 2.0, 2.0, 2.0])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "dispersion_entropy",
    "description": "Dispersion entropy (conventions: Dispersion entropy; ADR 0341).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "dispersion_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/dispersion_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
