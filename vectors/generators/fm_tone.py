"""Writes vectors/cases/fm_tone.json, stdlib only.

Two-operator FM tone (conventions: FM tone; ADR 0306), transcribed from the formula:
y[n] = A cos(2 pi fc (n/fs) + I sin(2 pi fm (n/fs))), with 2 pi f formed first.

Run from the repo root: python vectors/generators/fm_tone.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def add(cid, fs, size, fc, fm, i, why, amplitude=None):
    a = 1.0 if amplitude is None else amplitude
    y = []
    for n in range(size):
        t = n / fs
        y.append(a * math.cos(2.0 * math.pi * fc * t + i * math.sin(2.0 * math.pi * fm * t)))
    args = {"sample_rate": fs, "num_samples": size, "carrier": fc, "modulator": fm, "index": i}
    if amplitude is not None:
        args["amplitude"] = amplitude
    cases.append({"id": f"fm_tone.{cid}", "op": "fm_tone", "args": args, "expected": y,
                  "tol": TOL, "source": why})
    return y


y = add("no_index", 8000.0, 9, 1000.0, 250.0, 0.0, "index 0: cos(2 pi fc n / fs)")
assert all(abs(v - math.cos(math.pi * n / 4)) < 1e-15 for n, v in enumerate(y))
add("bell", 48000.0, 64, 440.0, 616.0, 3.5, "a 1 : 1.4 ratio, index 3.5", amplitude=0.8)
add("brass", 44100.0, 64, 220.0, 220.0, 5.0, "a 1 : 1 ratio, index 5")
add("negative_index", 8000.0, 32, 1000.0, 125.0, -2.0, "a negative index flips the sidebands")


def err(cid, why, **args):
    base = {"sample_rate": 8000.0, "num_samples": 4, "carrier": 1000.0, "modulator": 250.0,
            "index": 1.0}
    base.update(args)
    cases.append({"id": f"fm_tone.{cid}", "op": "fm_tone", "args": base,
                  "error": "invalid_argument", "source": why})


err("rate_zero", "sample_rate must be positive", sample_rate=0.0)
err("count_negative", "num_samples must be at least 0", num_samples=-1)

doc = {
    "schema": 1,
    "suite": "fm_tone",
    "description": "Two-operator FM tone (conventions: FM tone; ADR 0306).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "fm_tone.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/fm_tone.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
