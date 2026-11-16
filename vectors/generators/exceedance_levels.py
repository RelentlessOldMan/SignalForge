"""Writes vectors/cases/exceedance_levels.json, stdlib only.

Exceedance levels (conventions: Exceedance levels; ADR 0169): L_N is the 1 - N/100 quantile of
the powers by linear interpolation between order statistics (Hyndman-Fan type 7), worked in
exact fractions on hand-sorted series.

Run from the repo root: python vectors/generators/exceedance_levels.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def quantiles(powers, percents):
    s = sorted(F(v) for v in powers)
    out = []
    for n in percents:
        h = (len(s) - 1) * (1 - F(n) / 100)
        k = int(h)
        out.append(float(s[k] if k == len(s) - 1 else s[k] + (h - k) * (s[k + 1] - s[k])))
    return out


def case(cid, powers, percents, why, expected=None):
    got = quantiles(powers, percents)
    if expected is not None:
        assert got == expected, (cid, got)
    cases.append({"id": f"exceedance_levels.{cid}", "op": "exceedance_levels",
                  "args": {"powers": powers, "percents": percents},
                  "expected": got, "tol": TOL, "source": why})


case("odd_length", [5.0, 1.0, 4.0, 2.0, 3.0], [10.0, 50.0, 90.0],
     "sorted 1..5, h = 4(1 - N/100): L10 at h = 3.6 is 4.6, L50 at h = 2 is 3, L90 at h = 0.4 is 1.4",
     [4.6, 3.0, 1.4])
case("even_length", [0.25, 1.0, 0.5, 2.0], [50.0, 25.0],
     "sorted 0.25, 0.5, 1, 2: L50 at h = 1.5 is 0.75, L25 at h = 2.25 is 1.25", [0.75, 1.25])
case("extremes", [3.0, 9.0, 1.0], [0.0, 100.0], "L0 is the maximum 9, L100 the minimum 1",
     [9.0, 1.0])
case("repeats", [2.0, 2.0, 2.0, 8.0], [10.0, 90.0],
     "sorted 2, 2, 2, 8: L10 at h = 2.7 is 2 + 0.7(6) = 6.2, L90 at h = 0.3 is 2", [6.2, 2.0])
case("single", [0.125], [0.0, 37.5, 100.0], "one value: every level is that value",
     [0.125, 0.125, 0.125])
case("zeros", [0.0, 0.0, 1.0], [75.0], "sorted 0, 0, 1: L75 at h = 0.5 is 0", [0.0])
case("no_percents", [1.0, 2.0], [], "no percents give an empty result", [])


def err(cid, change, why):
    args = {"powers": [1.0, 2.0], "percents": [50.0]}
    args.update(change)
    cases.append({"id": f"exceedance_levels.{cid}", "op": "exceedance_levels", "args": args,
                  "error": "invalid_argument", "source": why})


err("empty_powers", {"powers": []}, "powers must not be empty")
err("negative_power", {"powers": [1.0, -0.5]}, "powers must be non-negative")
err("nan_power", {"powers": ["nan", 1.0]}, "powers must be finite")
err("inf_power", {"powers": ["inf", 1.0]}, "powers must be finite")
err("percent_above", {"percents": [100.5]}, "percents must be at most 100")
err("percent_below", {"percents": [-1.0]}, "percents must be at least 0")
err("percent_nan", {"percents": ["nan"]}, "percents must be finite")

doc = {
    "schema": 1,
    "suite": "exceedance_levels",
    "description": "Exceedance (percentile) levels (conventions: Exceedance levels; ADR 0169).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "exceedance_levels.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/exceedance_levels.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
