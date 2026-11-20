"""Writes vectors/cases/tetrachoric_approximation.json, stdlib only.

The tetrachoric approximation (conventions: the tetrachoric approximation; ADR 0492): the
2x2 table counted directly, cos(pi / (1 + sqrt(OR))) in 40-digit decimals, pi from Machin's
formula and the cosine from its Taylor series.

Run from the repo root: python vectors/generators/tetrachoric_approximation.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 40

TOL = {"abs": 1e-13, "rel": 1e-13}
cases = []


def atan_inv(m):
    """atan(1/m) for an integer m > 1, by its series."""
    total, power, k = D(0), D(1) / m, 0
    while power > D(10) ** -45:
        term = power / (2 * k + 1)
        total += -term if k % 2 else term
        power /= m * m
        k += 1
    return total


PI = 16 * atan_inv(5) - 4 * atan_inv(239)
assert str(PI).startswith("3.14159265358979323846264338327950288419")


def cos(x):
    total, term, k = D(1), D(1), 0
    while abs(term) > D(10) ** -45:
        term = -term * x * x / ((2 * k + 1) * (2 * k + 2))
        total += term
        k += 1
    return total


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    tn = len(t) - tp - fn - fp
    assert tp + fn + fp + tn == len(t)
    q = cos(PI / (1 + (D(tp * tn) / (fn * fp)).sqrt())).quantize(D(10) ** -38)
    cases.append(
        {
            "id": f"tetrachoric_approximation.{cid}",
            "op": "tetrachoric_approximation",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def close(a, b):
    return abs(a - b) < D(10) ** -35


got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "OR 16: cos(pi/5) = (1 + sqrt 5)/4",
)
assert close(got, (1 + D(5).sqrt()) / 4)
got = add("independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "OR 1: cos(pi/2) = 0")
assert close(got, D(0))
got = add(
    "third",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
    "TP 2, FN 1, FP 1, TN 2: OR 4, cos(pi/3) = 1/2",
)
assert close(got, D(1) / 2)
got = add(
    "opposite_lean",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 1.0, 1.0, 0.0],
    "TP 1, FN 2, FP 2, TN 1: OR 1/4, cos(2 pi/3) = -1/2",
)
assert close(got, D(-1) / 2)
got = add(
    "opposite", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0], "OR 0: cos(pi) = -1, the least value"
)
assert close(got, D(-1))
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "TP 2, FN 1, FP 3, TN 1: OR 2/3, cos(pi/(1 + sqrt(2/3)))",
)
rng = random.Random(492)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(492), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"tetrachoric_approximation.{cid}",
            "op": "tetrachoric_approximation",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("no_fp", "equal records: FP = 0", truth=[1.0, 0.0, 1.0, 0.0], decision=[1.0, 0.0, 1.0, 0.0])
err(
    "no_fn",
    "every truth 1 caught: FN = 0",
    truth=[1.0, 0.0, 1.0, 0.0],
    decision=[1.0, 1.0, 1.0, 0.0],
)
err("truth_all_zero", "truth has no 1: FN = 0", truth=[0.0, 0.0, 0.0], decision=[1.0, 0.0, 1.0])


doc = {
    "schema": 1,
    "suite": "tetrachoric_approximation",
    "description": "The tetrachoric approximation (conventions: the tetrachoric"
    " approximation; ADR 0492).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "tetrachoric_approximation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/tetrachoric_approximation.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
