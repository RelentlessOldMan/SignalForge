"""Writes vectors/cases/blomqvist_beta.json, stdlib only.

Blomqvist's beta (conventions: Blomqvist's beta; ADR 0375): the medians and the quadrant
counts exact in rationals.

Run from the repo root: python vectors/generators/blomqvist_beta.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def median(v):
    s = sorted(Fr(u) for u in v)
    k = len(s) // 2
    return s[k] if len(s) % 2 == 1 else (s[k - 1] + s[k]) / 2


def add(cid, x, y, why):
    mx, my = median(x), median(y)
    agree = disagree = 0
    for a, b in zip(x, y):
        p = (Fr(a) - mx) * (Fr(b) - my)
        if p > 0:
            agree += 1
        elif p < 0:
            disagree += 1
    beta = Fr(agree - disagree, agree + disagree)
    cases.append({"id": f"blomqvist_beta.{cid}", "op": "blomqvist_beta",
                  "args": {"x": x, "y": y}, "expected": float(beta), "tol": TOL,
                  "source": why})
    return agree, disagree, beta


got = add("odd_hand", [1.0, 2.0, 3.0, 4.0, 5.0], [1.0, 3.0, 2.0, 5.0, 4.0],
          "medians 3 and 3: (2, 3) and (3, 2) lie on a median and drop; (1, 1), (4, 5), "
          "(5, 4) agree; 3/3 = 1")
assert got == (3, 0, 1)
got = add("even_hand", [1.0, 2.0, 3.0, 4.0], [4.0, 1.0, 3.0, 2.0],
          "medians 2.5 and 2.5: (2, 1) and (3, 3) agree, (1, 4) and (4, 2) disagree; 0/4 = 0")
assert got == (2, 2, 0)
got = add("reversed", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], [6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
          "medians 3.5 and 3.5: every sample on opposite sides; -6/6 = -1")
assert got == (0, 6, -1)
got = add("ties_on_median", [0.0, 1.0, 1.0, 1.0, 2.0, 3.0], [5.0, 0.0, 2.0, 2.0, 2.0, 4.0],
          "medians 1 and 2: four samples lie on a median and drop; (0, 5) disagrees, "
          "(3, 4) agrees; 0/2 = 0")
assert got == (1, 1, 0)
rng = random.Random(375)
xs = [rng.randint(-40, 40) / 8 for _ in range(41)]
ys = [v + rng.randint(-24, 24) / 8 for v in xs]
add("noisy_eighths", xs, ys,
    "41 random eighths from random.Random(375), y = x plus random eighths: with ties")
xs = [rng.randint(-40, 40) / 8 for _ in range(50)]
ys = [-v + rng.randint(-40, 40) / 8 for v in xs]
add("even_negative", xs, ys, "50 random eighths, y = -x plus random eighths")


def err(cid, why, **args):
    base = {"x": [0.0, 1.0, 0.5, 2.0, 3.0], "y": [2.0, 1.0, 3.0, 0.0, 1.0]}
    base.update(args)
    cases.append({"id": f"blomqvist_beta.{cid}", "op": "blomqvist_beta", "args": base,
                  "error": "invalid_argument", "source": why})


err("lengths_differ", "x and y must be the same length", y=[1.0, 2.0, 3.0, 4.0])
err("empty", "x and y must not be empty", x=[], y=[])
err("one_sample", "one sample lies on both medians", x=[1.0], y=[2.0])
err("all_on_median", "every x equals its median", x=[1.0, 1.0, 1.0], y=[1.0, 2.0, 3.0])
err("nan", "samples must be finite", y=[0.0, "nan", 1.0, 2.0, 3.0])

doc = {
    "schema": 1,
    "suite": "blomqvist_beta",
    "description": "Blomqvist's beta (conventions: Blomqvist's beta; ADR 0375).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "blomqvist_beta.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/blomqvist_beta.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
