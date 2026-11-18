"""Writes vectors/cases/hard_sync_sawtooth.json, stdlib only.

Hard-synced sawtooth (conventions: Hard-synced sawtooth; ADR 0315), from the rule in exact
rationals: m = frac(sync n / fs); u = frac((f / sync) m); y = A(2u - 1). Each case keeps both
frac arguments at least 1e-9 from an integer unless they are exact binary fractions, so no
rounding can move a sample across a jump.

Run from the repo root: python vectors/generators/hard_sync_sawtooth.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def frac(x, cid, n):
    k = math.floor(x)
    near = min(x - k, k + 1 - x)
    assert near > Fr(1, 10**9) or (x.denominator & (x.denominator - 1)) == 0, (cid, n, x)
    return x - k


def add(cid, fs, size, f, sync, why, amplitude=None):
    a = Fr(1 if amplitude is None else amplitude)
    y = []
    for n in range(size):
        m = frac(Fr(sync) * n / Fr(fs), cid, n)
        u = frac(Fr(f) / Fr(sync) * m, cid, n)
        y.append(float(a * (2 * u - 1)))
    args = {"sample_rate": fs, "num_samples": size, "frequency": f, "sync_frequency": sync}
    if amplitude is not None:
        args["amplitude"] = amplitude
    cases.append({"id": f"hard_sync_sawtooth.{cid}", "op": "hard_sync_sawtooth", "args": args,
                  "expected": y, "tol": TOL, "source": why})
    return y


y = add("unsynced", 8000.0, 8, 1000.0, 1000.0, "slave = master: the naive sawtooth")
assert y == [-1 + k / 4 for k in range(8)], y
y = add("one_and_half", 8000.0, 16, 1500.0, 1000.0, "slave 1.5 x master: the slave wraps once "
        "mid-cycle, then the master restarts it")
assert y[:8] == [-1.0, -0.625, -0.25, 0.125, 0.5, 0.875, -0.75, -0.375], y
add("swept_ratio", 44100.0, 96, 1234.5 * 2.37, 1234.5, "ratio 2.37 at 1234.5 Hz, 44.1 kHz",
    amplitude=0.6)
add("below_master", 48000.0, 48, 700.0, 3000.0, "a slave slower than the master never "
    "finishes a cycle")
add("backwards", 48000.0, 40, -4100.0, 2500.0, "a negative slave runs down from each restart")
add("still_slave", 8000.0, 4, 0.0, 1000.0, "a slave at 0 Hz holds -A")


def err(cid, why, **args):
    base = {"sample_rate": 8000.0, "num_samples": 4, "frequency": 1500.0,
            "sync_frequency": 1000.0}
    base.update(args)
    cases.append({"id": f"hard_sync_sawtooth.{cid}", "op": "hard_sync_sawtooth", "args": base,
                  "error": "invalid_argument", "source": why})


err("sync_zero", "sync_frequency must be positive", sync_frequency=0.0)
err("sync_negative", "sync_frequency must be positive", sync_frequency=-1000.0)
err("rate_zero", "sample_rate must be positive", sample_rate=0.0)

doc = {
    "schema": 1,
    "suite": "hard_sync_sawtooth",
    "description": "Hard-synced sawtooth (conventions: Hard-synced sawtooth; ADR 0315).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hard_sync_sawtooth.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hard_sync_sawtooth.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
