"""Writes vectors/cases/autocorrelation.json, stdlib only.

Each case is worked by hand in exact integers (Gaussian integers for complex cases) from the
definition (conventions: Pulse shaping, Autocorrelation; ADR 0148): r[k] = sum x[n+k] conj x[n],
then divided by N, N - k or 1. The generator checks each hand value against the definition.

Run from the repo root: python vectors/generators/autocorrelation.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def raw(x, top):
    return [sum(x[n + k] * x[n].conjugate() for n in range(len(x) - k)) for k in range(top + 1)]


def scaled(x, top, scaling):
    n = len(x)
    div = {"biased": lambda k: n, "unbiased": lambda k: n - k, "none": lambda k: 1}[scaling]
    return [(F(int(v.real)) / div(k), F(int(v.imag)) / div(k))
            for k, v in enumerate(raw([complex(c) for c in x], top))]


def case(cid, x, sums, why, *, max_lag=None, scaling=None, im=None):
    xs = x if im is None else [complex(a, b) for a, b in zip(x, im, strict=True)]
    top = len(x) - 1 if max_lag is None else max_lag
    assert [complex(c) for c in raw([complex(c) for c in xs], top)] == [complex(c) for c in sums], (
        cid, raw([complex(c) for c in xs], top))
    vals = scaled(xs, top, scaling or "biased")
    args = {"samples": [float(v) for v in x] if im is None
            else {"re": [float(v) for v in x], "im": [float(v) for v in im]}}
    if max_lag is not None:
        args["max_lag"] = max_lag
    if scaling is not None:
        args["scaling"] = scaling
    expected = ([float(re) for re, _ in vals] if im is None
                else {"re": [float(re) for re, _ in vals], "im": [float(i) for _, i in vals]})
    cases.append({"id": f"autocorrelation.{cid}", "op": "autocorrelation", "args": args,
                  "expected": expected, "tol": TOL, "source": why})


def err(cid, args, why):
    full = {"samples": [1.0, 2.0, 3.0]}
    full.update(args)
    cases.append({"id": f"autocorrelation.{cid}", "op": "autocorrelation", "args": full,
                  "error": "invalid_argument", "source": why})


R = "x = 1, 2, 3: r0 = 1 + 4 + 9 = 14, r1 = 2·1 + 3·2 = 8, r2 = 3·1 = 3"
case("biased", [1, 2, 3], [14, 8, 3], R + "; over N = 3 (the default scaling)")
case("unbiased", [1, 2, 3], [14, 8, 3], R + "; over 3, 2, 1", scaling="unbiased")
case("none", [1, 2, 3], [14, 8, 3], R + "; not scaled", scaling="none")
case("complex", [1, 2, 0], [7, 2 - 4j, -1 - 1j],
     "x = 1+i, 2, -i: r0 = 2 + 4 + 1 = 7; r1 = 2(1-i) + (-i)(2) = 2 - 4i; "
     "r2 = (-i)(1-i) = -1 - i; not scaled", scaling="none", im=[1, 0, -1])
case("complex_biased", [1, 2, 0], [7, 2 - 4j, -1 - 1j],
     "the complex case over N = 3", im=[1, 0, -1])
case("max_lag", [1, -1, 1, -1], [4, -3],
     "x = 1, -1, 1, -1 to lag 1: r0 = 4, r1 = -1 - 1 - 1 = -3; not scaled",
     max_lag=1, scaling="none")
case("single", [5], [25], "one sample: r0 = 25 over N = 1")

err("empty", {"samples": []}, "needs at least one sample")
err("max_lag_too_big", {"max_lag": 3}, "max_lag must be at most N - 1 = 2")
err("negative_max_lag", {"max_lag": -1}, "max_lag must be non-negative")
err("bad_scaling", {"scaling": "coeff"}, "scaling must be biased, unbiased or none")
err("nan", {"samples": [1.0, "nan"]}, "samples must be finite")

doc = {
    "schema": 1,
    "suite": "autocorrelation",
    "description": "Autocorrelation (conventions: Pulse shaping, Autocorrelation; ADR 0148).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "autocorrelation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/autocorrelation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
