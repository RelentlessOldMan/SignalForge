"""Writes vectors/cases/mean_log_deviation.json, stdlib only.

The mean log deviation (conventions: the mean log deviation; ADR 0514): the mean of dyadic
values exact in rationals, each ln(mean/x) in 40-digit decimals.

Run from the repo root: python vectors/generators/mean_log_deviation.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from decimal import Decimal as D
from decimal import getcontext
from fractions import Fraction as Fr

getcontext().prec = 40

TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def add(cid, x, why):
    v = [Fr(a) for a in x]
    n = len(v)
    mean = sum(v) / n
    q = D(0)
    for a in v:
        ratio = mean / a
        q += (D(ratio.numerator) / D(ratio.denominator)).ln()
    q /= n
    cases.append(
        {
            "id": f"mean_log_deviation.{cid}",
            "op": "mean_log_deviation",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def close(a, b):
    return abs(a - b) < D(10) ** -35


got = add("equal", [2.0, 2.0, 2.0], "every value equal: 0")
assert got == 0
got = add("single", [5.0], "one value: 0")
assert got == 0
got = add("two", [1.0, 3.0], "mean 2: (ln 2 + ln(2/3))/2 = (2 ln 2 - ln 3)/2")
assert close(got, (2 * D(2).ln() - D(3).ln()) / 2)
got = add("ramp", [1.0, 2.0, 3.0, 4.0], "mean 5/2: (4 ln(5/2) - ln 24)/4")
assert close(got, (4 * (D(5) / 2).ln() - D(24).ln()) / 4)
got = add("halves", [0.5, 0.25, 0.25, 1.0], "mean 1/2: (0 + ln 2 + ln 2 - ln 2)/4 = ln 2/4")
assert close(got, D(2).ln() / 4)
got = add(
    "powers",
    [1.0, 4.0, 16.0, 0.25],
    "mean 85/16: ln(85/16) less the mean of the logs, (0 + 2 + 4 - 2) ln 2/4 = ln 2",
)
assert close(got, (D(85) / 16).ln() - D(2).ln())
rng = random.Random(514)
x = [rng.randint(1, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(514).randint(1, 64)")
add(
    "huge",
    [1e308, 9e307, 1e300],
    "values whose sum overflows a double: the result is that of the values scaled down",
)


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"mean_log_deviation.{cid}",
            "op": "mean_log_deviation",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("zero", "a value of 0 makes it infinite", samples=[1.0, 0.0, 2.0])
err("negative", "values must be greater than 0", samples=[1.0, -0.5, 2.0])

doc = {
    "schema": 1,
    "suite": "mean_log_deviation",
    "description": "The mean log deviation (conventions: the mean log deviation; ADR 0514).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "mean_log_deviation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/mean_log_deviation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
