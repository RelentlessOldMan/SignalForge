"""Writes vectors/cases/noise_figure_cascade.json by hand, using only the Python standard library.

Friis' formula for matched stages (conventions: Noise figure, Cascade; ADR 0106), worked in exact
rationals where the dB values are multiples of 10, and in floats from the formula otherwise.

Run from the repo root: python vectors/generators/noise_figure_cascade.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction

OP = "noise_figure_cascade"
cases = []


def lin(db):
    return Fraction(10) ** (int(db) // 10) if db % 10 == 0 else 10 ** (db / 10)


def expected(nf, g):
    c, before = [], 1
    for i, (a, b) in enumerate(zip(nf, g)):
        f = lin(a)
        c.append(f if i == 0 else (f - 1) / before)
        before *= lin(b)
    total = sum(c)
    return {"noise_factor": float(total), "noise_figure_db": 10 * math.log10(float(total)),
            "noise_temperature": float(290 * (total - 1)), "gain_db": float(sum(g)),
            "contributions": [float(x) for x in c]}


for cid, nf, g, why in (
    ("single_stage", [3.0], [10.0], "a single stage is itself: F = 10^0.3, gain 10 dB"),
    ("lna_then_mixer", [1.0, 10.0], [20.0, -7.0],
     "textbook: LNA NF 1 dB, 20 dB gain, then a 10 dB mixer: F = 10^0.1 + 9/100"),
    ("three_exact", [10.0, 20.0, 10.0], [10.0, 20.0, 0.0],
     "by hand: F = 10 + 99/10 + 9/1000 = 19.909"),
    ("loss_before_amp", [6.0, 2.0], [-6.0, 20.0],
     "by hand: a matched loss L at T0 in front gives F = L*F2: 10^0.6 * 10^0.2, NF 8 dB"),
    ("noiseless_stages", [0.0, 0.0, 0.0], [-10.0, 30.0, 5.0],
     "by hand: F = 1 for every stage: the chain has F = 1, NF 0 dB, 25 dB gain"),
    ("late_stage_matters_little", [2.0, 30.0], [40.0, 10.0],
     "by hand: F = 10^0.2 + 999/10000"),
):
    cases.append({"id": f"{OP}.{cid}", "op": OP, "args": {"noise_figures_db": nf, "gains_db": g},
                  "expected": expected(nf, g), "tol": {"abs": 1e-12, "rel": 1e-12},
                  "source": why})
for cid, nf, g, why in (
    ("empty", [], [], "at least one stage"),
    ("length_mismatch", [1.0, 2.0], [10.0], "one gain per stage"),
    ("negative_nf", [1.0, -0.1], [10.0, 10.0], "a noise figure below 0 dB is not physical"),
    ("nan_nf", ["nan"], [10.0], "noise figures must be finite"),
    ("inf_gain", [1.0, 2.0], ["inf", 1.0], "gains must be finite"),
    ("gain_underflows", [1.0, 3.0], [-4000.0, 0.0],
     "by hand: G1 = 10^-400 is 0 in double, so (F2 - 1)/G1 is not finite"),
    ("nf_overflows", [4000.0], [0.0], "F = 10^400 overflows, so F is not finite"),
):
    cases.append({"id": f"{OP}.{cid}", "op": OP, "args": {"noise_figures_db": nf, "gains_db": g},
                  "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": OP,
    "description": "Cascaded noise figure by Friis' formula (conventions: Noise figure, Cascade; "
    "ADR 0106).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / f"{OP}.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/{OP}.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
