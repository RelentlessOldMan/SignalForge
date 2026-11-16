"""Writes vectors/cases/inharmonicity.json, stdlib only.

Each case is worked by hand in Fractions from the definition (conventions: Spectra,
Inharmonicity; ADR 0140): `(2/f0)·Σ h|t − m·f0| / Σ h` over the tones with order `m ≥ 1`.

Run from the repo root: python vectors/generators/inharmonicity.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def case(cid, tones, heights, f0, orders, want, why):
    args = {"frequencies": tones, "heights": heights, "fundamental": f0, "orders": orders}
    cases.append({"id": f"inharmonicity.{cid}", "op": "inharmonicity", "args": args,
                  "expected": float(want), "tol": TOL, "source": why})


def err(cid, args, why):
    cases.append({"id": f"inharmonicity.{cid}", "op": "inharmonicity", "args": args,
                  "error": "invalid_argument", "source": why})


case("exact", [100.0, 200.0, 300.0], [1.0, 1.0, 1.0], 100.0, [1, 2, 3], 0,
     "exact multiples of 100 Hz: no spread")
case("detuned", [100.0, 202.0, 297.0], [4.0, 2.0, 1.0], 100.0, [1, 2, 3], F(2, 100),
     "spreads 0, 2, 3 weighted 4, 2, 1: (0 + 4 + 3)/7 = 1 Hz, times 2/100")
case("unmatched", [100.0, 150.0, 205.0], [1.0, 9.0, 1.0], 100.0, [1, 0, 2], F(5, 100),
     "the order-0 tone at 150 Hz is left out: spreads 0 and 5, mean 5/2, times 2/100")
case("zero_height", [100.0, 230.0], [1.0, 0.0], 100.0, [1, 2], 0,
     "the 230 Hz tone has no weight")
case("half_fundamental", [150.0], [3.0], 100.0, [1], 1,
     "a partial half a fundamental from its harmonic: 2/100 times 50")

T = {"frequencies": [100.0, 200.0], "heights": [1.0, 1.0], "fundamental": 100.0}
err("none_matched", {**T, "orders": [0, 0]}, "no tone has order >= 1")
err("matched_silent", {**T, "heights": [0.0, 1.0], "orders": [1, 0]},
    "the matched tone's height is 0")
err("length_mismatch", {**T, "orders": [1, 2, 3]}, "orders is longer than frequencies")
err("negative_height", {**T, "heights": [1.0, -1.0], "orders": [1, 2]},
    "heights must be non-negative")
err("zero_fundamental", {**T, "fundamental": 0.0, "orders": [1, 2]}, "fundamental must be > 0")
err("negative_order", {**T, "orders": [1, -2]}, "orders must be >= 0")
err("zero_tone", {**T, "frequencies": [0.0, 200.0], "orders": [1, 2]},
    "frequencies must be positive")

doc = {
    "schema": 1,
    "suite": "inharmonicity",
    "description": "Inharmonicity (conventions: Spectra, Inharmonicity; ADR 0140).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "inharmonicity.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/inharmonicity.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
