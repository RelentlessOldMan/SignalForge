"""Writes vectors/cases/coherent_output_power.json, stdlib only.

Coherent output power (conventions: Coherent output power; ADR 0198): Pyy as welch_psd(y),
coherent = gamma^2 Pyy, noncoherent = Pyy - coherent, gamma^2 taken as 0 where Sxx Syy = 0.
Rectangular windows, so sum w^2 = nperseg and Pyy = d Syy / (K fs nperseg), with d = 2 on the
one-sided bins strictly between 0 and Nyquist. Expected values are hand DFTs worked in each
source, each checked here against a direct DFT of the segments.

Run from the repo root: python vectors/generators/coherent_output_power.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def direct(x, y, fs, n):
    is_complex = any(isinstance(v, complex) for v in x + y)
    count = len(x) // n
    sxy, sxx, syy = [0j] * n, [0.0] * n, [0.0] * n
    for s in range(count):
        def spec(v):
            seg = v[s * n : s * n + n]
            return [sum(complex(seg[i]) * cmath.exp(-2j * math.pi * k * i / n) for i in range(n))
                    for k in range(n)]
        fx, fy = spec(x), spec(y)
        for k in range(n):
            sxy[k] += fx[k].conjugate() * fy[k]
            sxx[k] += abs(fx[k]) ** 2
            syy[k] += abs(fy[k]) ** 2
    if is_complex:
        bins = [(i + (n + 1) // 2) % n for i in range(n)]
        dbl = [1.0] * n
    else:
        bins = list(range(n // 2 + 1))
        dbl = [2.0 if 0 < k < n / 2 else 1.0 for k in bins]
    coh, non = [], []
    for k, d in zip(bins, dbl):
        pyy = d * syy[k] / (count * fs * n)
        den = sxx[k] * syy[k]
        gamma = min(1.0, abs(sxy[k]) ** 2 / den) if den > 1e-12 else 0.0
        coh.append(gamma * pyy)
        non.append(pyy - gamma * pyy)
    return coh, non, is_complex


def enc(v):
    if all(isinstance(c, float) for c in v):
        return v
    v = [complex(c) for c in v]
    return {"re": [c.real for c in v], "im": [c.imag for c in v]}


def add(cid, x, y, fs, n, coherent, noncoherent, why):
    coh, non, is_complex = direct(x, y, fs, n)
    assert all(abs(a - b) < 1e-12 for a, b in zip(coh + non, coherent + noncoherent)), (cid, coh, non)
    freqs = ([(i - n // 2) * fs / n for i in range(n)] if is_complex
             else [k * fs / n for k in range(n // 2 + 1)])
    cases.append({"id": f"coherent_output_power.{cid}", "op": "coherent_output_power",
                  "args": {"x": enc(x), "y": enc(y), "sample_rate": fs, "nperseg": n,
                           "noverlap": 0, "window": "rectangular"},
                  "expected": {"frequencies": freqs, "coherent": coherent,
                               "noncoherent": noncoherent, "num_segments": len(x) // n},
                  "tol": TOL, "source": why})


add("scaled", [1.0, 2.0, 3.0, 4.0], [-2.0, -4.0, -6.0, -8.0], 2.0, 2, [29.0, 1.0], [0.0, 0.0],
    "y = -2x: X = [3, -1], [7, -1]; Syy = 4 [9 + 49, 1 + 1] = [232, 8], Pyy = Syy / (2 * 2 * 2) = "
    "[29, 1] (nfft 2 doubles no bin); gamma^2 = 1, so all coherent")
add("three_segments", [1.0, 0.0] * 3, [1.0, 0.0, 1.0, 0.0, 0.0, 1.0], 2.0, 2,
    [0.25, 0.25 / 9], [0.0, 0.25 * 8 / 9],
    "X = [1, 1] thrice; Y = [1, 1], [1, 1], [1, -1]: Sxx = Syy = [3, 3], Sxy = [3, 1], gamma^2 = "
    "[1, 1/9]; Pyy = 3 / (3 * 2 * 2) = 0.25 per bin")
add("doubled_bin", [1.0, 0.0, 0.0, 0.0], [1.0, 1.0, 0.0, 0.0], 4.0, 4, [0.25, 0.25, 0.0],
    [0.0, 0.0, 0.0],
    "X = 1, Y = 1 + e^{-j pi k/2} = [2, 1 - j, 0]: |Y|^2 = [4, 2, 0], Pyy = [4, 2 * 2, 0] / (4 * "
    "4) = [0.25, 0.25, 0]; one segment, gamma^2 = 1 where Syy > 0; at bin 2 both parts are 0")
add("silent_input", [0.0, 0.0], [1.0, 0.0], 2.0, 2, [0.0, 0.0], [0.25, 0.25],
    "Sxx = 0, so gamma^2 = 0: Y = [1, 1], Pyy = 1 / (2 * 2) = 0.25, all noncoherent")
add("silent_output", [1.0, 0.0], [0.0, 0.0], 2.0, 2, [0.0, 0.0], [0.0, 0.0],
    "Syy = 0, so Pyy = 0 and both parts are 0")
add("complex", [1.0, 1j, 1.0, 1j], [1.0, 0.0, 0.0, 1.0], 2.0, 2, [0.0, 0.25], [0.25, 0.0],
    "X = [1 + j, 1 - j] twice, Y = [1, 1], [1, -1]: Syy = [2, 2], Sxy = [2 - 2j, 0], Sxx = [4, 4]; "
    "gamma^2 = [8/8, 0]; Pyy = 2 / (2 * 2 * 2) = 0.25, two-sided; shifted [bin 1, bin 0]")


def err(cid, x, y, why, **extra):
    args = {"x": x, "y": y, "sample_rate": 1.0}
    args.update(extra)
    cases.append({"id": f"coherent_output_power.{cid}", "op": "coherent_output_power",
                  "args": args, "error": "invalid_argument", "source": why})


err("lengths", [1.0, 2.0], [1.0], "x and y differ in length")
err("nan", [1.0, "nan"], [1.0, 2.0], "not finite")
err("zero_rate", [1.0, 2.0], [1.0, 2.0], "sample_rate must be positive", sample_rate=0.0)

doc = {
    "schema": 1,
    "suite": "coherent_output_power",
    "description": "Coherent output power (conventions: Coherent output power; ADR 0198).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "coherent_output_power.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/coherent_output_power.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
