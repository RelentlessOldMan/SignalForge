"""Writes vectors/cases/harmonic_to_noise.json, stdlib only.

Each case lists by hand which bins are harmonic (conventions: Spectra, Harmonic-to-noise ratio;
ADR 0143). The generator sums the bin powers `psd·Δ` of each set in Fractions and checks the
listed bins against the rule `m = ⌊f/f0 + 1/2⌋ ≥ 1`, `|f − m·f0| ≤ half_width`.

Run from the repo root: python vectors/generators/harmonic_to_noise.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
FREQS = [10.0 * k for k in range(10)]  # 0..90 Hz, spacing 10
cases = []


def case(cid, psd, f0, half_width, harmonic_bins, why, freqs=FREQS):
    delta = (F(freqs[-1]) - F(freqs[0])) / (len(freqs) - 1)
    rule = []
    for k, f in enumerate(freqs):
        m = math.floor(F(f) / F(f0) + F(1, 2))
        if m >= 1 and abs(F(f) - m * F(f0)) <= F(half_width):
            rule.append(k)
    assert rule == harmonic_bins, (cid, rule, harmonic_bins)
    harmonic = sum((F(psd[k]) * delta for k in harmonic_bins), F(0))
    noise = sum((F(p) * delta for k, p in enumerate(psd) if k not in harmonic_bins), F(0))
    if noise == 0:
        ratio, db = "inf", "inf"
    elif harmonic == 0:
        ratio, db = 0.0, "-inf"
    else:
        ratio, db = float(harmonic / noise), 10 * math.log10(harmonic / noise)
    args = {"frequencies": freqs, "psd": psd, "fundamental": f0, "half_width": half_width}
    cases.append({"id": f"harmonic_to_noise.{cid}", "op": "harmonic_to_noise", "args": args,
                  "expected": {"harmonic": float(harmonic), "noise": float(noise),
                               "ratio": ratio, "ratio_db": db},
                  "tol": TOL, "source": why})


def err(cid, args, why):
    full = {"frequencies": FREQS, "psd": [1.0] * 10, "fundamental": 30.0, "half_width": 0.0}
    full.update(args)
    cases.append({"id": f"harmonic_to_noise.{cid}", "op": "harmonic_to_noise", "args": full,
                  "error": "invalid_argument", "source": why})


MIX = [1.0, 1.0, 1.0, 4.0, 1.0, 1.0, 2.0, 1.0, 1.0, 3.0]
case("exact", MIX, 30.0, 0.0, [3, 6, 9],
     "bins at 30, 60, 90 Hz: harmonic (4 + 2 + 3)·10 = 90, noise 7·10 = 70, ratio 9/7")
case("wide", MIX, 30.0, 10.0, [2, 3, 4, 5, 6, 7, 8, 9],
     "within 10 Hz of 30, 60, 90 is every bin from 20 Hz up; DC and 10 Hz are noise "
     "(10 Hz rounds to order 0): harmonic 14·10, noise 2·10, ratio 7")
case("between_bins", [1.0] * 10, 25.0, 4.0, [5],
     "f0 = 25 Hz: only 50 Hz is within 4 Hz of a harmonic (30, 70, 80 are 5 Hz off): "
     "harmonic 10, noise 90, ratio 1/9")
case("no_noise", [0.0, 0.0, 0.0, 4.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0], 30.0, 0.0, [3, 6, 9],
     "all power on harmonics: ratio and dB +inf")
case("no_harmonic", [5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0], 30.0, 0.0, [3, 6, 9],
     "power only at DC and 70 Hz: ratio 0, dB -inf")

err("silent", {"psd": [0.0] * 10}, "the spectrum has no power")
err("half_width_half_f0", {"half_width": 15.0}, "half_width must be below f0/2")
err("negative_half_width", {"half_width": -1.0}, "half_width must be >= 0")
err("zero_fundamental", {"fundamental": 0.0}, "fundamental must be > 0")
err("length_mismatch", {"psd": [1.0] * 9}, "psd is shorter than frequencies")
err("uneven", {"frequencies": [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 95.0]},
    "frequencies must be evenly spaced")
err("negative_psd", {"psd": [1.0] * 9 + [-1.0]}, "psd must be non-negative")

doc = {
    "schema": 1,
    "suite": "harmonic_to_noise",
    "description": "Harmonic-to-noise ratio (conventions: Spectra, Harmonic-to-noise ratio; "
    "ADR 0143).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "harmonic_to_noise.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/harmonic_to_noise.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
