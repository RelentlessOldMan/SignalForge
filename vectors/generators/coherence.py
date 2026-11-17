"""Writes vectors/cases/coherence.json, stdlib only.

Magnitude-squared coherence (conventions: Coherence; ADR 0192): over Welch's segments,
C = min(1, |sum X conj Y|^2 / (sum |X|^2 sum |Y|^2)) per one-sided bin, NaN where the
denominator is 0. Expected values are worked by hand in each source (y = c x gives 1 by
Cauchy-Schwarz equality); each is checked here against a direct DFT of the segments.

Run from the repo root: python vectors/generators/coherence.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def direct(x, y, nperseg, noverlap, window, detrend):
    n = nperseg
    step = n - noverlap
    if window == "hann":
        w = [0.5 - 0.5 * math.cos(2 * math.pi * i / n) for i in range(n)]
    else:
        w = [1.0] * n
    m = n // 2 + 1
    sxy = [0j] * m
    sxx = [0.0] * m
    syy = [0.0] * m
    for s in range((len(x) - n) // step + 1):
        def spec(v):
            seg = v[s * step : s * step + n]
            if detrend == "constant":
                mu = sum(seg) / n
                seg = [t - mu for t in seg]
            return [sum(seg[i] * w[i] * cmath.exp(-2j * math.pi * k * i / n) for i in range(n))
                    for k in range(m)]
        fx, fy = spec(x), spec(y)
        for k in range(m):
            sxy[k] += fx[k] * fy[k].conjugate()
            sxx[k] += abs(fx[k]) ** 2
            syy[k] += abs(fy[k]) ** 2
    return [abs(sxy[k]) ** 2 / (sxx[k] * syy[k]) if sxx[k] * syy[k] > 1e-20 else math.nan
            for k in range(m)]


def add(cid, x, y, fs, nperseg, noverlap, window, values, segs, why, detrend="none",
        give_segments=True):
    got = direct(x, y, nperseg, noverlap, window, detrend)
    for g, h in zip(got, values):
        assert (math.isnan(g) and math.isnan(h)) or abs(g - h) < 1e-12, (cid, got)
    args = {"x": x, "y": y, "sample_rate": fs, "window": window}
    if give_segments:
        args["nperseg"] = nperseg
        args["noverlap"] = noverlap
    if detrend != "none":
        args["detrend"] = detrend
    cases.append({"id": f"coherence.{cid}", "op": "coherence", "args": args,
                  "expected": {"frequencies": [k * fs / nperseg for k in range(nperseg // 2 + 1)],
                               "values": ["nan" if math.isnan(v) else v for v in values],
                               "num_segments": segs},
                  "tol": TOL, "source": why})


add("two_segments", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 0.0, 1.0], 2.0, 2, 0, "rectangular",
    [1.0, 0.0], 2,
    "rectangular, 2-sample segments: X = [1, 1] twice; Y = [1, 1] then [1, -1]. Bin 0: |1 + 1|^2 "
    "/ (2 * 2) = 1; bin 1: |1 - 1|^2 / 4 = 0")
add("three_segments", [1.0, 0.0] * 3, [1.0, 0.0, 1.0, 0.0, 0.0, 1.0], 2.0, 2, 0, "rectangular",
    [1.0, 1.0 / 9.0], 3,
    "X = [1, 1] thrice; Y = [1, 1], [1, 1], [1, -1]. Bin 0: 9 / 9 = 1; bin 1: |1 + 1 - 1|^2 / "
    "(3 * 3) = 1/9")
add("zero_bin", [1.0, 1.0, 1.0, 1.0], [1.0, 0.0, 0.0, 1.0], 2.0, 2, 0, "rectangular",
    [1.0, math.nan], 2,
    "X = [2, 0] twice, so Sxx = 0 at bin 1: NaN. Bin 0: |2 + 2|^2 / (8 * 2) = 1")
add("single_segment", [1.0, 0.0], [0.0, 1.0], 2.0, 2, 1, "rectangular", [1.0, 1.0], 1,
    "defaults: one segment of the whole input, so C = |X conj Y|^2 / (|X|^2 |Y|^2) = 1 wherever "
    "both are non-zero: X = [1, 1], Y = [1, -1]", give_segments=False)
add("scaled_hann", [0.0, 1.0, 2.0, 0.0, -1.0, 0.0, 3.0, 1.0],
    [-0.0, -3.0, -6.0, -0.0, 3.0, -0.0, -9.0, -3.0], 8.0, 4, 2, "hann", [1.0, 1.0, 1.0], 3,
    "y = -3x, Hann, nperseg 4, overlap 2: Sxy = -3 Sxx, Syy = 9 Sxx, so C = 9 Sxx^2 / (9 Sxx^2) "
    "= 1 at every bin with Sxx > 0 (segment 0 windowed is [0, 0.5, 2, 0], X = [2.5, -2 - 0.5j, "
    "1.5], all non-zero)")
add("constant_y", [1.0, 2.0, 1.0, 2.0], [5.0, 5.0, 5.0, 5.0], 2.0, 2, 0, "rectangular",
    [math.nan, math.nan], 2,
    "detrend constant: each y segment becomes [0, 0], so Syy = 0 at every bin: NaN",
    detrend="constant")


def err(cid, x, y, why, **extra):
    args = {"x": x, "y": y, "sample_rate": 1.0}
    args.update(extra)
    cases.append({"id": f"coherence.{cid}", "op": "coherence", "args": args,
                  "error": "invalid_argument", "source": why})


err("lengths", [1.0, 2.0], [1.0], "x and y differ in length")
err("nan", [1.0, "nan"], [1.0, 2.0], "not finite")
err("zero_rate", [1.0, 2.0], [1.0, 2.0], "sample_rate must be positive", sample_rate=0.0)
err("long_segment", [1.0, 2.0], [1.0, 2.0], "fewer samples than nperseg", nperseg=3)

doc = {
    "schema": 1,
    "suite": "coherence",
    "description": "Magnitude-squared coherence (conventions: Coherence; ADR 0192).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "coherence.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/coherence.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
