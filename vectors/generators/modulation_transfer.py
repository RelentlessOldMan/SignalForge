"""Writes vectors/cases/modulation_transfer.json, stdlib only.

Modulation transfer function (conventions: Modulation transfer function; ADR 0176):
m(F) = |sum |h[n]|^2 e^(-j 2 pi F n/fs)| / sum |h[n]|^2. For h[n] = r^n over L samples it is the
closed form |(1 - (q z)^L)/(1 - q z)| / ((1 - q^L)/(1 - q)), q = r^2, z = e^(-j 2 pi F/fs),
evaluated with cmath (independent of the direct sum); hand cases are exact.

Run from the repo root: python vectors/generators/modulation_transfer.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-14, "rel": 1e-11}
cases = []


def add(cid, ir, fs, freqs, expected, why):
    cases.append({"id": f"modulation_transfer.{cid}", "op": "modulation_transfer",
                  "args": {"impulse_response": ir, "sample_rate": fs, "frequencies": freqs},
                  "expected": expected, "tol": TOL, "source": why})


def geometric(r, length, fs, f):
    q = r * r
    z = cmath.exp(-2j * math.pi * f / fs)
    return abs((1 - (q * z) ** length) / (1 - q * z)) / ((1 - q ** length) / (1 - q))


FREQS = [0.63, 1.0, 2.5, 6.3, 12.5]
add("geometric", [0.999 ** n for n in range(3000)], 1000.0, FREQS,
    [geometric(0.999, 3000, 1000.0, f) for f in FREQS],
    "h = 0.999^n, 3000 samples at 1 kHz: the closed form at the STI octave-centre modulations")
add("geometric_fast", [0.9 ** n for n in range(60)], 100.0, [0.0, 10.0, 50.0],
    [geometric(0.9, 60, 100.0, f) for f in [0.0, 10.0, 50.0]],
    "h = 0.9^n, 60 samples at 100 Hz: F = 0 gives 1, F = fs/2 the alternating sum")
add("hand", [1.0, 1.0], 4.0, [0.0, 1.0, 2.0], [1.0, math.sqrt(2) / 2, 0.0],
    "|h|^2 = 1, 1 at 4 Hz: |1 + e^(-j pi/2)|/2 = sqrt(2)/2, |1 + e^(-j pi)|/2 = 0")
add("above_nyquist", [1.0, 1.0], 4.0, [5.0], [math.sqrt(2) / 2],
    "F = 5 at fs 4 aliases to F = 1: sqrt(2)/2")
add("complex", {"re": [3.0, 0.0], "im": [4.0, 5.0]}, 4.0, [1.0], [math.sqrt(2) / 2],
    "|h|^2 = 25, 25: the same as the hand pair")
add("impulse", [0.0, 2.0, 0.0], 10.0, [3.0], [1.0], "a single delayed impulse: |e^(-j phi)| = 1")


def err(cid, change, why):
    args = {"impulse_response": [1.0, 0.5], "sample_rate": 10.0, "frequencies": [1.0]}
    args.update(change)
    cases.append({"id": f"modulation_transfer.{cid}", "op": "modulation_transfer", "args": args,
                  "error": "invalid_argument", "source": why})


err("empty", {"impulse_response": []}, "impulse_response must not be empty")
err("all_zero", {"impulse_response": [0.0, 0.0]}, "impulse_response must not be all zero")
err("nan", {"impulse_response": [1.0, "nan"]}, "impulse_response must be finite")
err("no_frequencies", {"frequencies": []}, "frequencies must not be empty")
err("negative_frequency", {"frequencies": [-1.0]}, "frequencies must be non-negative")
err("inf_frequency", {"frequencies": ["inf"]}, "frequencies must be finite")
err("zero_rate", {"sample_rate": 0.0}, "sample_rate must be positive")

def scaled(cid, base, k, why):
    """Case ``base`` with the responses times 2**k: the measure is a ratio of energies,
    unchanged by a common scale, and a power of 2 scales every value exactly, so the
    expected value is the base case's."""
    c = next(c for c in cases if c["id"] == "modulation_transfer." + base)
    s = 2.0**k

    def times(v):
        if isinstance(v, dict):
            return {part: times(v[part]) for part in ("re", "im")}
        assert all(u * s / s == u for u in v), cid
        return [u * s for u in v]

    args = {name: times(v) if name in ("impulse_response", "reference") else v
            for name, v in c["args"].items()}
    cases.append({**c, "id": "modulation_transfer." + cid, "args": args, "source": why})


scaled("huge", "hand", 1000,
       "case hand times 2^1000: squares of the samples overflow a double, but the "
       "measure is a ratio of energies, so the same value")
scaled("tiny", "hand", -1000,
       "case hand times 2^-1000: squares of the samples underflow to 0, but the "
       "measure is a ratio of energies, so the same value")
scaled("huge_complex", "complex", 1000,
       "case complex times 2^1000: squares of the samples overflow a double, but the "
       "measure is a ratio of energies, so the same value")
scaled("tiny_complex", "complex", -1000,
       "case complex times 2^-1000: squares of the samples underflow to 0, but the "
       "measure is a ratio of energies, so the same value")


doc = {
    "schema": 1,
    "suite": "modulation_transfer",
    "description": "Modulation transfer function (conventions: Modulation transfer function; ADR 0176).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "modulation_transfer.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/modulation_transfer.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
