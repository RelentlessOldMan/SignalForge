"""Writes vectors/cases/block_leq.json, stdlib only.

Short Leq series and sound exposure (conventions: Short Leq series and sound exposure; ADR
0170): block means of |x|^2 over N = floor(duration fs + 1/2) samples, a partial last block
dropped, and the exposure sum |x|^2 / fs, as exact hand sums in fractions.

Run from the repo root: python vectors/generators/block_leq.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def powers(samples):
    if isinstance(samples, dict):
        return [F(r) ** 2 + F(i) ** 2 for r, i in zip(samples["re"], samples["im"])]
    return [F(v) ** 2 for v in samples]


def blocks(cid, samples, fs, duration, n, why, expected):
    p = powers(samples)
    got = [float(sum(p[i * n:(i + 1) * n]) / n) for i in range(len(p) // n)]
    assert got == expected, (cid, got)
    cases.append({"id": f"block_leq.{cid}", "op": "block_leq",
                  "args": {"samples": samples, "sample_rate": fs, "duration": duration},
                  "expected": got, "tol": TOL, "source": why})


def exposure(cid, samples, fs, why, expected):
    got = float(sum(powers(samples), F(0)) / F(fs))
    assert got == expected, (cid, got)
    cases.append({"id": f"block_leq.{cid}", "op": "sound_exposure",
                  "args": {"samples": samples, "sample_rate": fs},
                  "expected": got, "tol": TOL, "source": why})


blocks("exact", [1.0, -1.0, 2.0, 0.0, 0.5, 0.5], 4.0, 0.5, 2,
       "N = 0.5 * 4 = 2: means of 1, 1 / 4, 0 / 0.25, 0.25", [1.0, 2.0, 0.25])
blocks("rounded", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], 10.0, 0.26, 3,
       "N = floor(2.6 + 0.5) = 3: (1 + 4 + 9)/3, (16 + 25 + 36)/3, the 7 dropped", [14 / 3, 77 / 3])
blocks("half_up", [2.0, 0.0, 0.0, 4.0, 0.0, 0.0], 1.0, 2.5, 3,
       "N = floor(2.5 + 0.5) = 3: 4/3 and 16/3", [4 / 3, 16 / 3])
blocks("complex", {"re": [3.0, 0.0, 1.0, 1.0], "im": [4.0, 1.0, 1.0, 0.0]}, 8.0, 0.25, 2,
       "N = 2: |x|^2 = 25, 1, 2, 1: means 13 and 1.5", [13.0, 1.5])
blocks("too_short", [1.0, 2.0], 100.0, 0.05, 5, "N = 5 > 2 samples: no whole block", [])
blocks("single_samples", [0.5, -2.0, 1.5], 1000.0, 0.001, 1, "N = 1: each sample's power",
       [0.25, 4.0, 2.25])
exposure("exposure", [1.0, -2.0, 3.0, 0.5], 4.0, "(1 + 4 + 9 + 0.25)/4 = 3.5625", 3.5625)
exposure("exposure_complex", {"re": [3.0, 0.0], "im": [4.0, 2.0]}, 10.0, "(25 + 4)/10 = 2.9", 2.9)
exposure("exposure_empty", [], 48000.0, "an empty input has zero exposure", 0.0)


def err(cid, op, change, why):
    args = {"samples": [1.0, 2.0], "sample_rate": 8.0}
    if op == "block_leq":
        args["duration"] = 0.25
    args.update(change)
    cases.append({"id": f"block_leq.{cid}", "op": op, "args": args,
                  "error": "invalid_argument", "source": why})


err("nan_sample", "block_leq", {"samples": [1.0, "nan"]}, "samples must be finite")
err("zero_duration", "block_leq", {"duration": 0.0}, "duration must be positive")
err("inf_duration", "block_leq", {"duration": "inf"}, "duration must be finite")
err("rounds_to_zero", "block_leq", {"duration": 0.05}, "0.05 * 8 + 0.5 = 0.9 rounds down to 0 samples")
err("zero_rate", "block_leq", {"sample_rate": 0.0}, "sample_rate must be positive")
err("exposure_nan", "sound_exposure", {"samples": ["nan"]}, "samples must be finite")
err("exposure_zero_rate", "sound_exposure", {"sample_rate": 0.0}, "sample_rate must be positive")
err("exposure_inf_rate", "sound_exposure", {"sample_rate": "inf"}, "sample_rate must be finite")

doc = {
    "schema": 1,
    "suite": "block_leq",
    "description": "Short Leq series and sound exposure (conventions: Short Leq series and sound exposure; ADR 0170).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "block_leq.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/block_leq.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
