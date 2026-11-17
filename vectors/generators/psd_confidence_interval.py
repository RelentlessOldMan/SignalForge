"""Writes vectors/cases/psd_confidence_interval.json, stdlib only.

PSD confidence interval (conventions: PSD confidence interval; ADR 0201): lower = nu P / q((1+c)/2),
upper = nu P / q((1-c)/2), q the chi-squared quantile. Each quantile here is solved by plain
bisection on a closed-form chi-squared CDF (or, for nu = 7.5, a stdlib series written here), not
by SignalForge's method.

Run from the repo root: python vectors/generators/psd_confidence_interval.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-13, "rel": 1e-11}
cases = []


def cdf_series(nu, x):
    a, y = nu / 2, x / 2
    total, n = 0.0, 0
    while True:
        term = math.exp((a + n) * math.log(y) - y - math.lgamma(a + n + 1))
        total += term
        n += 1
        if term < 1e-18 * total and n > y:
            return total


CDF = {
    1: lambda x: math.erf(math.sqrt(x / 2)),
    2: lambda x: -math.expm1(-x / 2),
    3: lambda x: math.erf(math.sqrt(x / 2)) - math.sqrt(2 * x / math.pi) * math.exp(-x / 2),
    4: lambda x: 1 - math.exp(-x / 2) * (1 + x / 2),
    7.5: lambda x: cdf_series(7.5, x),
}


def quantile(nu, p):
    lo, hi = 0.0, 1.0
    while CDF[nu](hi) < p:
        hi *= 2
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if CDF[nu](mid) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def add(cid, psd, nu, c, why, give_c=True):
    q_hi, q_lo = quantile(nu, (1 + c) / 2), quantile(nu, (1 - c) / 2)
    if nu == 2:
        assert abs(q_hi + 2 * math.log((1 - c) / 2)) < 1e-12 and abs(q_lo + 2 * math.log((1 + c) / 2)) < 1e-14
    args = {"psd": psd, "dof": float(nu)}
    if give_c:
        args["confidence"] = c
    cases.append({"id": f"psd_confidence_interval.{cid}", "op": "psd_confidence_interval",
                  "args": args,
                  "expected": {"lower": [nu * p / q_hi for p in psd],
                               "upper": [nu * p / q_lo for p in psd]},
                  "tol": TOL, "source": why})


add("two_dof", [1.0, 2.0, 0.0], 2, 0.9,
    "nu = 2: CDF 1 - e^{-x/2}, q(p) = -2 ln(1 - p); q(0.95) = 2 ln 20, q(0.05) = -2 ln 0.95; "
    "a zero bin gives [0, 0]")
add("default_level", [0.5], 2, 0.95, "confidence defaults to 0.95; nu = 2: q = -2 ln(1 - p)",
    give_c=False)
add("one_dof", [1.0, 3.0], 1, 0.95, "nu = 1: CDF erf(sqrt(x/2)), quantiles by bisection")
add("three_dof", [1.0], 3, 0.8,
    "nu = 3: CDF erf(sqrt(x/2)) - sqrt(2x/pi) e^{-x/2}, quantiles by bisection")
add("four_dof", [2.0], 4, 0.99, "nu = 4: CDF 1 - e^{-x/2}(1 + x/2), quantiles by bisection")
add("fractional_dof", [1.0, 0.25], 7.5, 0.95,
    "nu = 7.5: CDF sum_n y^(a+n) e^-y / Gamma(a+n+1), y = x/2, a = 3.75 (math.lgamma), by bisection")


def err(cid, why, **args):
    cases.append({"id": f"psd_confidence_interval.{cid}", "op": "psd_confidence_interval",
                  "args": args, "error": "invalid_argument", "source": why})


err("negative_psd", "psd must be non-negative", psd=[1.0, -0.5], dof=2.0)
err("nan_psd", "psd must be finite", psd=[1.0, "nan"], dof=2.0)
err("zero_dof", "dof must be positive", psd=[1.0], dof=0.0)
err("nan_dof", "dof must be finite", psd=[1.0], dof="nan")
err("confidence_one", "confidence must be below 1", psd=[1.0], dof=2.0, confidence=1.0)
err("confidence_zero", "confidence must be above 0", psd=[1.0], dof=2.0, confidence=0.0)

doc = {
    "schema": 1,
    "suite": "psd_confidence_interval",
    "description": "PSD confidence interval (conventions: PSD confidence interval; ADR 0201).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "psd_confidence_interval.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/psd_confidence_interval.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
