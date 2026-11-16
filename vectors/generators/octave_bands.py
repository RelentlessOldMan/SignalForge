"""Writes vectors/cases/octave_bands.json, stdlib only.

IEC 61260-1 base-10 fractional-octave bands (conventions: Fractional-octave bands; ADR 0167):
G = 10^(3/10), mid-band 1000 G^(x/b) (odd b) or 1000 G^((2x + 1)/(2b)) (even b), edges
f_m G^(-+1/(2b)), in 50-digit decimal. As an independent check it asserts that the octave and
third-octave mid-band frequencies lie within 1.5 % of the standard's nominal names.

Run from the repo root: python vectors/generators/octave_bands.py [--check]
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


def power10(e):
    return D(10) ** (D(3) * e / 10)


def bands(b, lo, hi):
    shift = D(1) / 2 if b % 2 == 0 else D(0)
    rows = []
    for x in range(-2000, 2000):
        e = (x + shift) / b
        fm = 1000 * power10(e)
        if D(lo) <= fm <= D(hi):
            half = power10(D(1) / (2 * b))
            rows.append([fm / half, fm, fm * half])
    return rows


NOMINAL = {
    1: [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000],
    3: [25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250,
        1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000, 20000],
}
for b, names in NOMINAL.items():
    got = [row[1] for row in bands(b, 22, 22000)]
    assert len(got) == len(names), (b, len(got))
    assert all(abs(f / D(n) - 1) < D("0.015") for f, n in zip(got, names)), b


def case(cid, b, lo, hi, why):
    rows = bands(b, lo, hi)
    assert rows
    cases.append({"id": f"octave_bands.{cid}", "op": "octave_bands",
                  "args": {"fraction": b, "min_frequency": lo, "max_frequency": hi},
                  "expected": [[float(v) for v in r] for r in rows], "tol": TOL, "source": why})


case("octaves_audio", 1, 20.0, 20000.0, "octaves, 1000 G^x, G = 10^0.3: x = -5 .. 4 (31.6 Hz to 15.8 kHz)")
case("thirds", 3, 100.0, 1000.0, "thirds, 1000 G^(x/3): x = -10 .. 0, the last exactly 1000")
case("halves", 2, 500.0, 2000.0, "even b = 2: 1000 G^((2x + 1)/4), none at 1000")
case("sixths", 6, 900.0, 1200.0, "even b = 6: 1000 G^((2x + 1)/12)")
case("single", 3, 1000.0, 1000.0, "min = max = 1000 = G^0: the one band, edges 1000 G^(-+1/6)")


def err(cid, change, why):
    args = {"fraction": 3, "min_frequency": 100.0, "max_frequency": 1000.0}
    args.update(change)
    cases.append({"id": f"octave_bands.{cid}", "op": "octave_bands", "args": args,
                  "error": "invalid_argument", "source": why})


err("zero_fraction", {"fraction": 0}, "fraction must be at least 1")
err("zero_min", {"min_frequency": 0.0}, "min_frequency must be positive")
err("min_above_max", {"min_frequency": 2000.0}, "min_frequency must not exceed max_frequency")
err("inf_max", {"max_frequency": "inf"}, "max_frequency must be finite")
err("nan_min", {"min_frequency": "nan"}, "min_frequency must be finite")

doc = {
    "schema": 1,
    "suite": "octave_bands",
    "description": "IEC 61260-1 fractional-octave bands (conventions: Fractional-octave bands; ADR 0167).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "octave_bands.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/octave_bands.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
