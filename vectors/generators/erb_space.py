"""Writes vectors/cases/erb_space.json, stdlib only.

ERB-spaced frequencies (conventions: ERB-spaced frequencies; ADR 0162): equal steps of ERB rate
E = 21.4 log10(4.37 f/1000 + 1) (ADR 0160) between the endpoints, mapped back with
(10^(E/21.4) - 1) 1000/4.37, in 50-digit decimal from the float arguments; the endpoints are
the arguments themselves.

Run from the repo root: python vectors/generators/erb_space.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 50
TOL = {"abs": 1e-12, "rel": 1e-13}
cases = []
A, Q = D("21.4"), D("4.37")


def rate(f):
    return A * (Q * f / 1000 + 1).log10()


def hz(e):
    return (D(10) ** (e / A) - 1) * 1000 / Q


def space(lo, hi, n):
    if n == 1:
        return [D(lo)]
    e_lo, e_hi = rate(D(lo)), rate(D(hi))
    out = [hz(e_lo + (e_hi - e_lo) * i / (n - 1)) for i in range(n)]
    out[0], out[-1] = D(lo), D(hi)
    return out


def case(cid, lo, hi, n, why):
    cases.append({"id": f"erb_space.{cid}", "op": "erb_space",
                  "args": {"min_frequency": lo, "max_frequency": hi, "n_frequencies": n},
                  "expected": [float(v) for v in space(lo, hi, n)], "tol": TOL, "source": why})


two_decades = float(1000 / Q * 99)  # E = 42.8 at this frequency, to the rounding of the float
mid = space(0.0, two_decades, 3)[1]
assert abs(mid - 1000 / Q * 9) < D(10) ** -9, mid  # E = 21.4 halfway: f = 9000/4.37
case("two_decades", 0.0, two_decades, 3,
     "min 0, max (1000/4.37) 99 (E = 42.8): the middle point is at E = 21.4, f = 9000/4.37")
case("eight", 50.0, 8000.0, 8, "8 points from 50 Hz to 8 kHz, equal ERB-rate steps in decimal")
case("thirty_two", 100.0, 4000.0, 32, "32 points from 100 Hz to 4 kHz in decimal")
case("one", 300.0, 5000.0, 1, "n = 1 gives [min]")
case("endpoints", 20.0, 20000.0, 2, "n = 2 gives exactly [min, max]")


def err(cid, change, why):
    args = {"min_frequency": 100.0, "max_frequency": 4000.0, "n_frequencies": 8}
    args.update(change)
    cases.append({"id": f"erb_space.{cid}", "op": "erb_space", "args": args,
                  "error": "invalid_argument", "source": why})


err("zero_count", {"n_frequencies": 0}, "n_frequencies must be at least 1")
err("min_at_max", {"min_frequency": 4000.0}, "min_frequency must be below max_frequency")
err("negative_min", {"min_frequency": -1.0}, "min_frequency must be at least 0")
err("inf_max", {"max_frequency": "inf"}, "max_frequency must be finite")
err("nan_min", {"min_frequency": "nan"}, "min_frequency must be finite")

doc = {
    "schema": 1,
    "suite": "erb_space",
    "description": "ERB-spaced frequencies (conventions: ERB-spaced frequencies; ADR 0162).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "erb_space.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/erb_space.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
