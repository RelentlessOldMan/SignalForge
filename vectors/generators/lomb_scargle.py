"""Writes vectors/cases/lomb_scargle.json from first principles, using only the Python standard
library.

It does not import NumPy or SignalForge, and it does not use Scargle's time offset tau.

- Closed forms on even samples: a sinusoid of amplitude A at bin k of N samples has P = A^2 N/4
  and standard value 1; other bins hold nothing; at Nyquist the sine term drops out by hand.
- Uneven times: the least-squares fit of a cos(wt) + b sin(wt) to y, solved from its 2x2 normal
  equations with math.fsum, gives P = (sum y^2 - chi2_min) / 2 = (a sum(y cos) + b sum(y sin)) / 2.
  An exact sinusoid (center off) fits with chi2_min = 0, so its standard value is 1.

Run from the repo root: python vectors/generators/lomb_scargle.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import json
import math
import pathlib
import random
import sys

cases = []
TOL = {"abs": 1e-12, "rel": 1e-9}


def add(cid, args, expected, source):
    cases.append({"id": f"lomb_scargle.{cid}", "op": "lomb_scargle", "args": args,
                  "expected": expected, "tol": TOL, "source": source})


def err(cid, args, source):
    cases.append({"id": f"lomb_scargle.{cid}", "op": "lomb_scargle", "args": args,
                  "error": "invalid_argument", "source": source})


def fit_power(t, y, f):
    """(sum y^2 - chi2_min) / 2 of the least-squares fit a cos(wt) + b sin(wt)."""
    w = 2 * math.pi * f
    c = [math.cos(w * v) for v in t]
    s = [math.sin(w * v) for v in t]
    gcc = math.fsum(x * x for x in c)
    gss = math.fsum(x * x for x in s)
    gcs = math.fsum(x * z for x, z in zip(c, s))
    bc = math.fsum(v * x for v, x in zip(y, c))
    bs = math.fsum(v * x for v, x in zip(y, s))
    det = gcc * gss - gcs * gcs
    a = (gss * bc - gcs * bs) / det
    b = (gcc * bs - gcs * bc) / det
    return (a * bc + b * bs) / 2


def centered(y):
    m = math.fsum(y) / len(y)
    return [v - m for v in y]


# ---- even samples, closed forms
n32 = list(range(32))
tone = [1.5 * math.cos(2 * math.pi * 3 / 32 * k + 0.4) for k in n32]
add("even_bin_power", {"times": n32, "values": tone, "frequencies": [3 / 32, 5 / 32, 7 / 32],
                       "normalization": "power"}, [1.5**2 * 32 / 4, 0.0, 0.0],
    "closed form: A^2 N/4 = 18 at the tone's bin, 0 at other bins")
add("even_bin_standard", {"times": n32, "values": tone, "frequencies": [3 / 32, 11 / 32]},
    [1.0, 0.0], "closed form: the tone explains all of its sum of squares at its bin, none at "
    "another")
add("even_sample_rate", {"times": [k / 8000 for k in n32], "values": tone,
                         "frequencies": [3 / 32 * 8000], "normalization": "power"}, [18.0],
    "closed form: the same samples at 8 kHz, the bin at 750 Hz")
alt = [(-1.0) ** k for k in range(16)]
add("nyquist", {"times": list(range(16)), "values": alt, "frequencies": [0.5],
                "normalization": "power", "center": False}, [8.0],
    "by hand: tau = 0, the cosines are all +1 or -1 so C = 16 and CC = 16; every sine is 0, so "
    "SS < 1e-12 N drops out: P = 16^2/16/2 = 8")

# ---- uneven times
rng = random.Random(59)
t40 = sorted(rng.uniform(0, 10) for _ in range(40))
sine = [0.8 * math.cos(2 * math.pi * 0.7 * v + 1.0) for v in t40]
add("uneven_exact_fit", {"times": t40, "values": sine, "frequencies": [0.7], "center": False},
    [1.0], "by analysis: a sinusoid at the trial frequency fits exactly (chi2_min = 0)")
add("uneven_exact_fit_power", {"times": t40, "values": sine, "frequencies": [0.7],
                               "center": False, "normalization": "power"},
    [math.fsum(v * v for v in sine) / 2], "by analysis: P = sum(y^2)/2 when the fit is exact")

t50 = [rng.uniform(-3, 17) for _ in range(50)]  # unsorted on purpose
noisy = [0.6 * math.sin(2 * math.pi * 0.37 * v) + rng.gauss(0, 0.5) + 0.3 for v in t50]
grid = [0.05, 0.2, 0.37, 0.5, 0.81, 1.3, 2.9]
for center in (True, False):
    y = centered(noisy) if center else noisy
    total = math.fsum(v * v for v in y)
    p = [fit_power(t50, y, f) for f in grid]
    tag = "centered" if center else "raw"
    add(f"uneven_{tag}_power", {"times": t50, "values": noisy, "frequencies": grid,
                                "center": center, "normalization": "power"}, p,
        "least-squares fit of a cos(wt) + b sin(wt) from its normal equations")
    add(f"uneven_{tag}_standard", {"times": t50, "values": noisy, "frequencies": grid,
                                   "center": center}, [2 * v / total for v in p],
        "least-squares fit, times 2/sum(y^2)")
yc = centered(noisy)
add("time_shift", {"times": [v + 1000 for v in t50], "values": noisy, "frequencies": grid,
                   "normalization": "power"}, [fit_power(t50, yc, f) for f in grid],
    "least-squares fit on the unshifted times: the periodogram ignores where time zero is")
rep = [0.0, 0.5, 0.5, 1.25, 2.0, 2.0, 3.5]
rv = [1.0, -0.4, 0.2, 0.9, -1.1, -0.7, 0.3]
add("repeated_times", {"times": rep, "values": rv, "frequencies": [0.3, 0.45],
                       "normalization": "power"},
    [fit_power(rep, centered(rv), f) for f in (0.3, 0.45)],
    "least-squares fit; repeated times are just more equations")
add("empty_frequencies", {"times": [0, 1], "values": [1, 2], "frequencies": []}, [],
    "no frequencies, no values")
add("constant_power", {"times": [0, 1, 2], "values": [2, 2, 2], "frequencies": [0.25],
                       "normalization": "power"}, [0.0],
    "by hand: a constant minus its mean is zero, so P = 0")

# ---- bad arguments
err("one_sample", {"times": [0], "values": [1], "frequencies": [0.1]}, "N must be at least 2")
err("length_mismatch", {"times": [0, 1, 2], "values": [1, 2], "frequencies": [0.1]},
    "one value per time")
err("zero_frequency", {"times": [0, 1, 2], "values": [1, 2, 0], "frequencies": [0.1, 0]},
    "frequencies must be positive: tau is undefined at 0")
err("negative_frequency", {"times": [0, 1, 2], "values": [1, 2, 0], "frequencies": [-0.1]},
    "frequencies must be positive")
err("nan_time", {"times": [0, "nan", 2], "values": [1, 2, 0], "frequencies": [0.1]},
    "times must be finite")
err("inf_value", {"times": [0, 1, 2], "values": [1, "inf", 0], "frequencies": [0.1]},
    "values must be finite")
err("inf_frequency", {"times": [0, 1, 2], "values": [1, 2, 0], "frequencies": ["inf"]},
    "frequencies must be finite")
err("bad_normalization", {"times": [0, 1, 2], "values": [1, 2, 0], "frequencies": [0.1],
                          "normalization": "psd"}, "standard or power only")
err("constant_standard", {"times": [0, 1, 2], "values": [2, 2, 2], "frequencies": [0.1]},
    "the standard normalization divides by sum(y^2) = 0")

doc = {
    "schema": 1,
    "suite": "lomb_scargle",
    "description": "Lomb-Scargle periodogram of unevenly sampled real data (conventions: Spectra, "
    "Lomb-Scargle periodogram).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "lomb_scargle.json"


def same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, int | float) and isinstance(b, int | float) and not isinstance(a, bool):
        return abs(a - b) <= 1e-14 * max(1.0, abs(b))
    return a == b


if "--check" in sys.argv[1:]:
    if not same(json.loads(out.read_text(encoding="utf-8")), json.loads(json.dumps(doc))):
        sys.exit(f"{out} is out of date: run python vectors/generators/lomb_scargle.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
