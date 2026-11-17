"""Writes vectors/cases/transfer_function_h2.json, stdlib only.

Transfer function H2 (conventions: Transfer function (H2); ADR 0195): over Welch's segments,
H2[k] = sum |Y_s|^2 / sum conj Y_s X_s per one-sided bin, complex NaN where the denominator is 0.
Expected values are hand DFTs worked in each source, each checked here against a direct DFT of
the segments.

Run from the repo root: python vectors/generators/transfer_function_h2.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def direct(x, y, n, noverlap):
    step = n - noverlap
    m = n // 2 + 1
    syx = [0j] * m
    syy = [0.0] * m
    for s in range((len(x) - n) // step + 1):
        def spec(v):
            seg = v[s * step : s * step + n]
            return [sum(seg[i] * cmath.exp(-2j * math.pi * k * i / n) for i in range(n))
                    for k in range(m)]
        fx, fy = spec(x), spec(y)
        for k in range(m):
            syx[k] += fy[k].conjugate() * fx[k]
            syy[k] += abs(fy[k]) ** 2
    return [syy[k] / syx[k] if abs(syx[k]) > 1e-12 else complex(math.nan, math.nan)
            for k in range(m)]


def nan_or(v):
    return "nan" if math.isnan(v) else v


def add(cid, x, y, fs, nperseg, noverlap, response, segs, why):
    got = direct(x, y, nperseg, noverlap)
    for g, h in zip(got, response):
        assert (cmath.isnan(g) and cmath.isnan(h)) or abs(g - h) < 1e-12, (cid, got)
    cases.append({"id": f"transfer_function_h2.{cid}", "op": "transfer_function_h2",
                  "args": {"x": x, "y": y, "sample_rate": fs, "nperseg": nperseg,
                           "noverlap": noverlap, "window": "rectangular"},
                  "expected": {"frequencies": [k * fs / nperseg for k in range(nperseg // 2 + 1)],
                               "response": {"re": [nan_or(h.real) for h in response],
                                            "im": [nan_or(h.imag) for h in response]},
                               "num_segments": segs},
                  "tol": TOL, "source": why})


NAN = complex(math.nan, math.nan)
add("fir_impulse", [1.0, 0.0, 0.0, 0.0], [0.5, 0.25, 0.0, 0.0], 4.0, 4, 0,
    [0.75 + 0j, 0.5 - 0.25j, 0.25 + 0j], 1,
    "x = delta, y = h = [0.5, 0.25]: X = 1, so H2 = |Y|^2 / conj Y = Y = DFT(h): 0.75, "
    "0.5 - 0.25j, 0.25 (= H1, no noise)")
add("scaled", [1.0, 2.0, 3.0, 4.0], [-2.0, -4.0, -6.0, -8.0], 2.0, 2, 0, [-2 + 0j, -2 + 0j], 2,
    "y = -2x: Syy = 4 Sxx, Syx = -2 Sxx, so H2 = -2 (X = [3, -1], [7, -1], all non-zero)")
add("zero_bin", [1.0, 1.0], [1.0, 0.0], 2.0, 2, 0, [0.5 + 0j, NAN], 1,
    "X = [2, 0], Y = [1, 1]: bin 0: 1 / (1 * 2) = 0.5; bin 1: Syx = 1 * 0 = 0, NaN")
add("inconsistent", [1.0, 0.0] * 3, [1.0, 0.0, 1.0, 0.0, 0.0, 1.0], 2.0, 2, 0,
    [1 + 0j, 3 + 0j], 3,
    "X = [1, 1] thrice; Y = [1, 1], [1, 1], [1, -1]. Bin 0: 3 / 3 = 1; bin 1: Syy = 3, Syx = 1 + 1 "
    "- 1 = 1, H2 = 3 (H1 = 1/3, coherence 1/9)")
add("cancelling", [1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 1.0, 0.0], 2.0, 2, 0, [1 + 0j, NAN], 2,
    "X = [1, 1], [1, -1]; Y = [1, 1] twice. Bin 0: 2 / 2 = 1; bin 1: Syx = 1 - 1 = 0, NaN (H1 is 0)")


def err(cid, x, y, why, **extra):
    args = {"x": x, "y": y, "sample_rate": 1.0}
    args.update(extra)
    cases.append({"id": f"transfer_function_h2.{cid}", "op": "transfer_function_h2",
                  "args": args, "error": "invalid_argument", "source": why})


err("lengths", [1.0, 2.0], [1.0], "x and y differ in length")
err("nan", [1.0, 2.0], ["nan", 2.0], "not finite")
err("zero_rate", [1.0, 2.0], [1.0, 2.0], "sample_rate must be positive", sample_rate=0.0)

doc = {
    "schema": 1,
    "suite": "transfer_function_h2",
    "description": "Transfer function H2 (conventions: Transfer function (H2); ADR 0195).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "transfer_function_h2.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/transfer_function_h2.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
