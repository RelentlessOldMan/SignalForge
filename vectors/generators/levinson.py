"""Writes vectors/cases/levinson.json, stdlib only.

Each case is solved by hand in Fractions (conventions: Pulse shaping, Linear prediction;
ADR 0149). The generator checks every hand value without the Levinson recursion. For each order
m it solves the normal equations sum_j a[j] r[i-j] = 0 (i = 1..m, a[0] = 1, r[-k] = conj r[k])
by exact Gaussian elimination over complex Fractions. Then k_m is that solution's last tap, and
the error is sum_j a[j] conj r[j].

Run from the repo root: python vectors/generators/levinson.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


class C:
    """An exact complex number with Fraction parts."""

    def __init__(self, re, im=0):
        self.re, self.im = F(re), F(im)

    def __add__(self, o):
        return C(self.re + o.re, self.im + o.im)

    def __sub__(self, o):
        return C(self.re - o.re, self.im - o.im)

    def __mul__(self, o):
        return C(self.re * o.re - self.im * o.im, self.re * o.im + self.im * o.re)

    def __truediv__(self, o):
        d = o.re * o.re + o.im * o.im
        return C((self.re * o.re + self.im * o.im) / d, (self.im * o.re - self.re * o.im) / d)

    def conj(self):
        return C(self.re, -self.im)

    def __eq__(self, o):
        return self.re == o.re and self.im == o.im

    def zero(self):
        return self.re == 0 and self.im == 0


def lag(r, k):
    return r[k] if k >= 0 else r[-k].conj()


def solve(r, m):
    """a[1..m] from sum_{j=1}^{m} a[j] r[i-j] = -r[i], i = 1..m, by Gaussian elimination."""
    rows = [[lag(r, i - j) for j in range(1, m + 1)] + [C(0) - r[i]] for i in range(1, m + 1)]
    for c in range(m):
        piv = next(i for i in range(c, m) if not rows[i][c].zero())
        rows[c], rows[piv] = rows[piv], rows[c]
        for i in range(m):
            if i != c and not rows[i][c].zero():
                f = rows[i][c] / rows[c][c]
                rows[i] = [x - f * y for x, y in zip(rows[i], rows[c], strict=True)]
    return [C(1)] + [rows[i][m] / rows[i][i] for i in range(m)]


def check(r, p, a, k, e):
    full = solve(r, p)
    assert full == a, [(x.re, x.im) for x in full]
    assert [solve(r, m)[m] for m in range(1, p + 1)] == k
    err = C(0)
    for j in range(p + 1):
        err = err + a[j] * r[j].conj()
    assert err == C(e), (err.re, err.im)


def cx(v):
    return v if isinstance(v, C) else C(v)


def case(cid, r, order, a, k, e, why):
    r, a, k = [cx(v) for v in r], [cx(v) for v in a], [cx(v) for v in k]
    check(r, order, a, k, e)
    complex_ = any(v.im != 0 for v in r)

    def out(vs):
        if complex_:
            return {"re": [float(v.re) for v in vs], "im": [float(v.im) for v in vs]}
        return [float(v.re) for v in vs]

    cases.append({"id": f"levinson.{cid}", "op": "levinson",
                  "args": {"r": out(r), "order": order},
                  "expected": {"coefficients": out(a), "reflection": out(k), "error": float(e)},
                  "tol": TOL, "source": why})


def err(cid, args, why):
    full = {"r": [4.0, 2.0, 3.0], "order": 2}
    full.update(args)
    cases.append({"id": f"levinson.{cid}", "op": "levinson", "args": full,
                  "error": "invalid_argument", "source": why})


h = F(1, 2)
case("first_order", [1, h], 1, [1, -h], [-h], F(3, 4),
     "r = 1, 1/2: k1 = -1/2, a = 1, -1/2, E = 1 - 1/4 = 3/4")
case("ar1_order2", [1, h, F(1, 4)], 2, [1, -h, 0], [-h, 0], F(3, 4),
     "r = (1/2)^k, an AR(1): k2 = -(1/4 - 1/4)/(3/4) = 0, so a = 1, -1/2, 0 and E stays 3/4")
case("second_order", [4, 2, 3], 2, [1, F(-1, 6), F(-2, 3)], [-h, F(-2, 3)], F(5, 3),
     "r = 4, 2, 3: k1 = -1/2, E1 = 3; acc = 3 - 1 = 2, k2 = -2/3; a1 = -1/2 + (-2/3)(-1/2) "
     "= -1/6; E = 3(1 - 4/9) = 5/3")
case("extra_lags", [4, 2, 3, 7], 2, [1, F(-1, 6), F(-2, 3)], [-h, F(-2, 3)], F(5, 3),
     "the second-order case with an unused fourth lag")
case("complex_first_order", [2, C(1, 1)], 1, [1, C(-h, -h)], [C(-h, -h)], F(1),
     "r = 2, 1+i: k1 = -(1+i)/2, E = 2(1 - 1/2) = 1")
case("complex_second_order", [4, C(0, 2), 1], 2, [1, C(0, F(-5, 6)), F(-2, 3)],
     [C(0, -h), F(-2, 3)], F(5, 3),
     "r = 4, 2i, 1: k1 = -i/2, E1 = 3; acc = 1 + (-i/2)(2i) = 2, k2 = -2/3; "
     "a1 = -i/2 + (-2/3)conj(-i/2) = -5i/6; E = 3(1 - 4/9) = 5/3")

err("order_zero", {"order": 0}, "order must be at least 1")
err("too_few_lags", {"order": 3}, "r needs order + 1 = 4 lags")
err("r0_zero", {"r": [0.0, 0.0, 0.0]}, "r[0] must be positive")
err("r0_negative", {"r": [-1.0, 0.0, 0.0]}, "r[0] must be positive")
err("r0_complex", {"r": {"re": [4.0, 2.0, 3.0], "im": [1.0, 0.0, 0.0]}}, "r[0] must be real")
err("unit_reflection", {"r": [1.0, 1.0, 1.0]}, "k1 = -1: not positive definite")
err("large_reflection", {"r": [1.0, 2.0, 0.0], "order": 1}, "k1 = -2: not positive definite")
err("nan", {"r": [4.0, "nan", 3.0]}, "r must be finite")

doc = {
    "schema": 1,
    "suite": "levinson",
    "description": "Linear prediction by Levinson-Durbin (conventions: Pulse shaping, Linear "
    "prediction; ADR 0149).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "levinson.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/levinson.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
