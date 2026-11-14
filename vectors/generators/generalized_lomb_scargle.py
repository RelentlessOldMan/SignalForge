"""Writes vectors/cases/generalized_lomb_scargle.json from first principles, using only the Python
standard library.

It does not import NumPy or SignalForge, and it does not use the time offset tau. At each frequency
it solves the weighted least-squares fit of a cos(wt) + b sin(wt) + c to the values, weights 1/sigma^2,
from its 3x3 normal equations (Gaussian elimination with partial pivoting, sums by math.fsum). The
explained scatter sum w (fit - weighted mean)^2 is chi2_0 - chi2, since the fit contains the
constant; the standard value is that over chi2_0 and the power is half of it (conventions: Spectra,
Generalized Lomb-Scargle; ADR 0081). By-hand cases cover exact fits, Nyquist (where the sine drops
out) and even samples at a bin.

Run from the repo root: python vectors/generators/generalized_lomb_scargle.py [--check]
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
SRC = ("vectors/generators/generalized_lomb_scargle.py (stdlib only): weighted 3x3 normal equations "
       "for a cos + b sin + c solved directly at each frequency, no tau")


def add(cid, args, expected, source=SRC):
    cases.append({"id": f"generalized_lomb_scargle.{cid}", "op": "generalized_lomb_scargle",
                  "args": args, "expected": expected, "tol": TOL, "source": source})


def err(cid, args, source):
    cases.append({"id": f"generalized_lomb_scargle.{cid}", "op": "generalized_lomb_scargle",
                  "args": args, "error": "invalid_argument", "source": source})


def solve3(a, b):
    m = [row[:] + [v] for row, v in zip(a, b)]
    for col in range(3):
        piv = max(range(col, 3), key=lambda r: abs(m[r][col]))
        m[col], m[piv] = m[piv], m[col]
        assert abs(m[col][col]) > 1e-9, "singular fit: choose another frequency"
        for r in range(col + 1, 3):
            q = m[r][col] / m[col][col]
            m[r] = [x - q * z for x, z in zip(m[r], m[col])]
    x = [0.0] * 3
    for r in (2, 1, 0):
        x[r] = (m[r][3] - sum(m[r][j] * x[j] for j in range(r + 1, 3))) / m[r][r]
    return x


def periodogram(t, y, freqs, sigma=None, normalization="standard"):
    w = [1.0] * len(t) if sigma is None else [1 / (s * s) for s in sigma]
    mean = math.fsum(a * b for a, b in zip(w, y)) / math.fsum(w)
    chi0 = math.fsum(a * (b - mean) ** 2 for a, b in zip(w, y))
    out = []
    for f in freqs:
        om = 2 * math.pi * f
        basis = [[math.cos(om * v) for v in t], [math.sin(om * v) for v in t], [1.0] * len(t)]
        g = [[math.fsum(wi * p * q for wi, p, q in zip(w, bi, bj)) for bj in basis] for bi in basis]
        r = [math.fsum(wi * p * yi for wi, p, yi in zip(w, bi, y)) for bi in basis]
        coef = solve3(g, r)
        fit = [math.fsum(coef[k] * basis[k][n] for k in range(3)) for n in range(len(t))]
        explained = math.fsum(a * (b - mean) ** 2 for a, b in zip(w, fit))
        out.append(explained / chi0 if normalization == "standard" else explained / 2)
    return out


def case(cid, t, y, freqs, sigma=None, normalization=None):
    args = {"times": t, "values": y, "frequencies": freqs}
    if sigma is not None:
        args["uncertainties"] = sigma
    if normalization is not None:
        args["normalization"] = normalization
    add(cid, args, periodogram(t, y, freqs, sigma, normalization or "standard"))


rng = random.Random(81)
t_uneven = sorted(rng.uniform(0, 20) for _ in range(40))
y_uneven = [7.0 + 1.3 * math.cos(2 * math.pi * 0.37 * v + 0.5) + 0.4 * rng.gauss(0, 1)
            for v in t_uneven]
sig = [0.2 + 0.6 * rng.random() for _ in t_uneven]
grid = [0.05 * k + 0.013 for k in range(1, 16)]
case("uneven_standard", t_uneven, y_uneven, grid)
case("uneven_power", t_uneven, y_uneven, grid, normalization="power")
case("uneven_weighted_standard", t_uneven, y_uneven, grid, sigma=sig)
case("uneven_weighted_power", t_uneven, y_uneven, grid, sigma=sig, normalization="power")
# sampled mostly near the peaks: the sample mean is far from the signal's mean
t_peaks = [k + d for k in range(12) for d in (-0.05, 0.0, 0.05)] + [5.5, 8.5]
y_peaks = [2.0 + math.cos(2 * math.pi * v) + 0.01 * math.sin(3.1 * v) for v in t_peaks]
case("peaks_biased_mean", t_peaks, y_peaks, [0.31, 0.5 + 0.017, 0.97, 1.0 + 1e-3])
t_mixed = [3.2, 0.1, 7.7, 0.1, 5.0, 2.4, 9.9, 6.1, 4.4, 8.3]
y_mixed = [math.sin(1.7 * v) - 0.3 * v for v in t_mixed]
case("unsorted_with_repeat", t_mixed, y_mixed, [0.11, 0.27, 0.43],
     sigma=[1.0, 2.0, 0.5, 1.5, 1.0, 1.0, 3.0, 0.7, 1.2, 0.9], normalization="power")

t5 = [0.0, 0.25, 0.5, 0.75, 1.0]
y5 = [3 + math.cos(2 * math.pi * v) for v in t5]
hand = "by hand: 3 + cos 2 pi t is fitted exactly, so chi2 = 0; "
add("exact_fit_standard", {"times": t5, "values": y5, "frequencies": [1.0]}, [1.0],
    hand + "standard (chi2_0 - 0)/chi2_0 = 1")
add("exact_fit_power", {"times": t5, "values": y5, "frequencies": [1.0], "normalization": "power"},
    [1.4], hand + "y = (4, 3, 2, 3, 4), mean 3.2, sum of squared deviations 2.8, half is 1.4")
add("exact_fit_weighted_power", {"times": t5, "values": y5, "frequencies": [1.0],
                                 "uncertainties": [1.0, 1.0, 1.0, 1.0, 0.5],
                                 "normalization": "power"}, [2.0],
    hand + "weights (1, 1, 1, 1, 4), weighted mean 28/8 = 3.5, chi2_0 = 0.25 + 0.25 + 2.25 + "
    "0.25 + 4 * 0.25 = 4, half is 2")
add("nyquist", {"times": [0.0, 1.0, 2.0, 3.0], "values": [3.0, 1.0, 3.0, 1.0],
                "frequencies": [0.5], "normalization": "power"}, [2.0],
    "by hand: at Nyquist sin(pi n) = 0 drops out and cos(pi n) = (1, -1, 1, -1) fits 2 + cos "
    "exactly; chi2_0 = 4, half is 2")
n32 = [float(k) for k in range(32)]
tone = [5 + 1.5 * math.cos(2 * math.pi * 3 / 32 * k + 0.4) for k in n32]
add("even_bin_power", {"times": n32, "values": tone, "frequencies": [3 / 32, 5 / 32, 11 / 32],
                       "normalization": "power"}, [1.5 ** 2 * 32 / 4, 0.0, 0.0],
    "by hand: on 32 even samples a sinusoid of amplitude 1.5 at bin 3 has power A^2 N / 4 = 18 "
    "and nothing at other bins; the offset 5 is fitted by the constant")
add("constant_power", {"times": [0.0, 1.3, 2.0], "values": [4.0, 4.0, 4.0],
                       "frequencies": [0.2, 0.7], "normalization": "power"}, [0.0, 0.0],
    "by hand: constant values have chi2_0 = 0, so nothing to explain")
add("no_frequencies", {"times": [0.0, 1.0], "values": [1.0, 2.0], "frequencies": []}, [],
    "by hand: no frequencies give an empty result")

ok = {"times": [0.0, 1.0, 2.0], "values": [1.0, 2.0, 0.5], "frequencies": [0.3]}
err("length_mismatch", ok | {"values": [1.0, 2.0]}, "times and values must match")
err("one_sample", {"times": [0.0], "values": [1.0], "frequencies": [0.3]}, "at least 2 samples")
err("time_nan", ok | {"times": [0.0, "nan", 2.0]}, "times must be finite")
err("frequency_zero", ok | {"frequencies": [0.0]}, "frequencies must be positive")
err("sigma_zero", ok | {"uncertainties": [1.0, 0.0, 1.0]}, "uncertainties must be positive")
err("sigma_negative", ok | {"uncertainties": [1.0, -1.0, 1.0]}, "uncertainties must be positive")
err("sigma_inf", ok | {"uncertainties": [1.0, "inf", 1.0]}, "uncertainties must be finite")
err("sigma_length", ok | {"uncertainties": [1.0, 1.0]}, "one uncertainty per sample")
err("normalization_unknown", ok | {"normalization": "psd"}, 'normalization "standard" or "power"')
err("standard_constant", ok | {"values": [2.0, 2.0, 2.0]},
    "the standard normalization needs values that are not all equal")

doc = {
    "schema": 1,
    "suite": "generalized_lomb_scargle",
    "description": "Generalized (floating-mean, weighted) Lomb-Scargle periodogram (conventions: "
    "Spectra, Generalized Lomb-Scargle; ADR 0081).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "generalized_lomb_scargle.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/generalized_lomb_scargle.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
