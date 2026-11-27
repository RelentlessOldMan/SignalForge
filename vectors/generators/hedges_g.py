"""Writes vectors/cases/hedges_g.json, stdlib only.

Hedges' g (conventions: Hedges' g; ADR 0398): Cohen's d from exact rational means and sums of
squares, the correction J(m) exact from factorials and sqrt(pi), all in 40-digit decimal.

Run from the repo root: python vectors/generators/hedges_g.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import math
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-12}
decimal.getcontext().prec = 40
D = decimal.Decimal
PI = D("3.14159265358979323846264338327950288419716939937510")
SQRT_PI = PI.sqrt()
cases = []


def dec(q):
    return D(q.numerator) / D(q.denominator)


def gamma_half(n):
    """Gamma(n + 1/2) / sqrt(pi) = (2n)! / (4^n n!), exact."""
    return Fr(math.factorial(2 * n), 4**n * math.factorial(n))


def j_factor(m):
    """J(m) = Gamma(m/2) / (sqrt(m/2) Gamma((m - 1)/2))."""
    if m % 2 == 0:
        k = m // 2
        ratio = dec(Fr(math.factorial(k - 1)) / gamma_half(k - 1)) / SQRT_PI
    else:
        k = (m - 1) // 2
        ratio = dec(gamma_half(k) / math.factorial(k - 1)) * SQRT_PI
    return ratio / dec(Fr(m, 2)).sqrt()


assert abs(j_factor(2) - 1 / SQRT_PI) < D("1e-35")
assert abs(j_factor(3) - SQRT_PI / 2 / D("1.5").sqrt()) < D("1e-35")


def add(cid, x, y, why):
    fx, fy = [Fr(v) for v in x], [Fr(v) for v in y]
    mx, my = sum(fx) / len(fx), sum(fy) / len(fy)
    ss = sum((v - mx) ** 2 for v in fx) + sum((v - my) ** 2 for v in fy)
    m = len(x) + len(y) - 2
    d = dec(mx - my) / dec(ss / m).sqrt()
    g = j_factor(m) * d
    cases.append(
        {
            "id": f"hedges_g.{cid}",
            "op": "hedges_g",
            "args": {"x": x, "y": y},
            "expected": float(g),
            "tol": TOL,
            "source": why,
        }
    )
    return g


got = add(
    "smallest", [1.0, 3.0], [0.0, 2.0], "d = 1/sqrt 2, m = 2: J = 1/sqrt(pi), g = 1/sqrt(2 pi)"
)
assert abs(got - 1 / (2 * PI).sqrt()) < D("1e-35")
got = add(
    "two",
    [4.0, 6.0, 8.0],
    [0.0, 2.0, 4.0],
    "d = 2, m = 4: J = Gamma(2)/(sqrt 2 Gamma(3/2)) = 2/sqrt(2 pi), g = 4/sqrt(2 pi)",
)
assert abs(got - 4 / (2 * PI).sqrt()) < D("1e-35")
add(
    "odd_m",
    [4.0, 6.0, 8.0],
    [1.0, 3.0],
    "d from means 6 and 2, m = 3: J = sqrt(pi)/2 over sqrt(3/2)",
)
rng = random.Random(398)
x = [rng.gauss(10.5, 2.0) for _ in range(40)]
y = [rng.gauss(10.0, 2.0) for _ in range(60)]
add("gaussian", x, y, "40 and 60 values from random.Random(398), N(10.5, 2) and N(10, 2): m = 98")


def scaled(cid, base, k, why):
    """Case ``base`` with x and y times 2**k: the measure is unchanged when both records are
    scaled alike, and a power of 2 scales every value exactly, so the expected value is the
    base case's."""
    c = next(c for c in cases if c["id"] == "hedges_g." + base)
    s = 2.0**k
    args = {name: [v * s for v in c["args"][name]] for name in ("x", "y")}
    assert all(v * s / s == v for name in ("x", "y")
               for v in c["args"][name]), cid
    cases.append({**c, "id": "hedges_g." + cid, "args": args, "source": why})


scaled("huge", "two", 1000, "case two times 2^1000: squares of the deviations overflow a "
       "double, but the measure is unchanged by a common scale, so the same value")
scaled("tiny", "two", -1000, "case two times 2^-1000: squares of the deviations underflow "
       "to 0, but the measure is unchanged by a common scale, so the same value")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [2.0, 4.0]}
    base.update(args)
    cases.append(
        {
            "id": f"hedges_g.{cid}",
            "op": "hedges_g",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("x_too_short", "each sample needs 2 values", x=[1.0])
err("not_finite", "values must be finite", y=[2.0, "inf"])
err("no_spread", "s = 0: every value at its mean", x=[2.0, 2.0], y=[5.0, 5.0, 5.0])

doc = {
    "schema": 1,
    "suite": "hedges_g",
    "description": "Hedges' g (conventions: Hedges' g; ADR 0398).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hedges_g.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hedges_g.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
