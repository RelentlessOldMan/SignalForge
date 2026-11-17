"""Writes vectors/cases/cross_spectral_density.json, stdlib only.

Cross-spectral density (conventions: Cross-spectral density; ADR 0194): over Welch's segments,
Pxy[k] = d_k sum conj X_s Y_s / (K fs sum w^2), d_k = 2 except DC and (even M) Nyquist. Expected
values are hand DFTs worked in each source, each checked here against a direct DFT with the
rectangular window (sum w^2 = nperseg).

Run from the repo root: python vectors/generators/cross_spectral_density.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def direct(x, y, fs, n, noverlap):
    step = n - noverlap
    m = n // 2 + 1
    count = (len(x) - n) // step + 1
    sxy = [0j] * m
    for s in range(count):
        def spec(v):
            seg = v[s * step : s * step + n]
            return [sum(seg[i] * cmath.exp(-2j * math.pi * k * i / n) for i in range(n))
                    for k in range(m)]
        fx, fy = spec(x), spec(y)
        for k in range(m):
            sxy[k] += fx[k].conjugate() * fy[k]
    last = m - 1 if n % 2 == 0 else m
    return [sxy[k] / (count * fs * n) * (2 if 1 <= k < last else 1) for k in range(m)]


def add(cid, x, y, fs, nperseg, noverlap, csd, segs, why):
    got = direct(x, y, fs, nperseg, noverlap)
    assert all(abs(g - h) < 1e-12 for g, h in zip(got, csd)), (cid, got)
    cases.append({"id": f"cross_spectral_density.{cid}", "op": "cross_spectral_density",
                  "args": {"x": x, "y": y, "sample_rate": fs, "nperseg": nperseg,
                           "noverlap": noverlap, "window": "rectangular"},
                  "expected": {"frequencies": [k * fs / nperseg for k in range(nperseg // 2 + 1)],
                               "csd": {"re": [h.real for h in csd], "im": [h.imag for h in csd]},
                               "num_segments": segs},
                  "tol": TOL, "source": why})


add("fir_impulse", [1.0, 0.0, 0.0, 0.0], [0.5, 0.25, 0.0, 0.0], 4.0, 4, 0,
    [0.046875 + 0j, 0.0625 - 0.03125j, 0.015625 + 0j], 1,
    "x = delta, y = [0.5, 0.25]: conj X Y = Y = [0.75, 0.5 - 0.25j, 0.25]; scale 1/(1 * 4 * 4) = "
    "1/16, bin 1 doubled: [0.046875, 0.0625 - 0.03125j, 0.015625]")
add("same_signal", [1.0, 2.0, 0.0, -1.0], [1.0, 2.0, 0.0, -1.0], 1.0, 4, 0,
    [1 + 0j, 5 + 0j, 0j], 1,
    "y = x: X = [2, 1 - 3j, 0], |X|^2 = [4, 10, 0]; scale 1/(1 * 1 * 4), bin 1 doubled: [1, 5, 0], "
    "the hand PSD")
add("cancelling", [1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 1.0, 0.0], 2.0, 2, 0, [0.25 + 0j, 0j], 2,
    "X = [1, 1], [1, -1]; Y = [1, 1] twice: sum conj X Y = [2, 0]; scale 1/(2 * 2 * 2) = 1/8; bin 1 "
    "is Nyquist, not doubled: [0.25, 0]")


def err(cid, x, y, why, **extra):
    args = {"x": x, "y": y, "sample_rate": 1.0}
    args.update(extra)
    cases.append({"id": f"cross_spectral_density.{cid}", "op": "cross_spectral_density",
                  "args": args, "error": "invalid_argument", "source": why})


err("lengths", [1.0, 2.0], [1.0], "x and y differ in length")
err("nan", [1.0, "nan"], [1.0, 2.0], "not finite")
err("zero_rate", [1.0, 2.0], [1.0, 2.0], "sample_rate must be positive", sample_rate=0.0)
err("long_segment", [1.0, 2.0], [1.0, 2.0], "fewer samples than nperseg", nperseg=3)

doc = {
    "schema": 1,
    "suite": "cross_spectral_density",
    "description": "Cross-spectral density (conventions: Cross-spectral density; ADR 0194).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cross_spectral_density.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cross_spectral_density.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
