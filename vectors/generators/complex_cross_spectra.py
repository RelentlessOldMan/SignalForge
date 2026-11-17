"""Writes vectors/cases/complex_cross_spectra.json, stdlib only.

Coherence, H1 and H2 of complex input (conventions: Complex coherence and transfer functions;
ADR 0197): all M bins of the segment FFTs, in fftshift order. With nperseg 2, the shifted order is
[bin 1, bin 0] at [-fs/2, 0]. Expected values are hand DFTs worked in each source, each checked
here against a direct DFT of the segments.

Run from the repo root: python vectors/generators/complex_cross_spectra.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
NAN = complex(math.nan, math.nan)
cases = []


def sums(x, y, n):
    """Shifted (sum conj X Y, sum |X|^2, sum |Y|^2), rectangular window, no overlap."""
    sxy, sxx, syy = [0j] * n, [0.0] * n, [0.0] * n
    for s in range(len(x) // n):
        def spec(v):
            seg = v[s * n : s * n + n]
            return [sum(complex(seg[i]) * cmath.exp(-2j * math.pi * k * i / n) for i in range(n))
                    for k in range(n)]
        fx, fy = spec(x), spec(y)
        for k in range(n):
            sxy[k] += fx[k].conjugate() * fy[k]
            sxx[k] += abs(fx[k]) ** 2
            syy[k] += abs(fy[k]) ** 2
    order = [(i + (n + 1) // 2) % n for i in range(n)]
    return [sxy[k] for k in order], [sxx[k] for k in order], [syy[k] for k in order]


def direct(op, x, y, n):
    sxy, sxx, syy = sums(x, y, n)
    if op == "coherence":
        return [min(1.0, abs(a) ** 2 / (b * c)) if b * c > 1e-12 else math.nan
                for a, b, c in zip(sxy, sxx, syy)]
    if op == "transfer_function":
        return [a / b if b > 1e-12 else NAN for a, b in zip(sxy, sxx)]
    return [c / a.conjugate() if abs(a) > 1e-12 else NAN for a, c in zip(sxy, syy)]


def enc(v):
    if all(isinstance(c, float) for c in v):
        return v
    v = [complex(c) for c in v]
    return {"re": [c.real for c in v], "im": [c.imag for c in v]}


def nan_or(v):
    return "nan" if math.isnan(v) else v


def add(cid, op, x, y, fs, n, values, why):
    got = direct(op, x, y, n)
    for g, h in zip(got, values):
        ok = cmath.isnan(g) and cmath.isnan(h) if isinstance(h, complex) else (
            math.isnan(g) and math.isnan(h))
        assert ok or abs(g - h) < 1e-12, (cid, got)
    if op == "coherence":
        expected = {"values": [nan_or(v) for v in values]}
    else:
        expected = {"response": {"re": [nan_or(v.real) for v in values],
                                 "im": [nan_or(v.imag) for v in values]}}
    cases.append({"id": f"complex_cross_spectra.{cid}", "op": op,
                  "args": {"x": enc(x), "y": enc(y), "sample_rate": fs, "nperseg": n,
                           "noverlap": 0, "window": "rectangular"},
                  "expected": {"frequencies": [(i - n // 2) * fs / n for i in range(n)],
                               **expected, "num_segments": len(x) // n},
                  "tol": TOL, "source": why})


X = [1.0, 1j, 2.0, 0.0]
Y = [(1 + 1j) * v for v in X]
SCALED = ("y = (1 + j) x, segments X = [1 + j, 1 - j] and [2, 2], all non-zero: Sxy = (1 + j) Sxx "
          "and Syy = 2 Sxx")
add("scaled_h1", "transfer_function", X, Y, 2.0, 2, [1 + 1j, 1 + 1j], SCALED + ", so H1 = 1 + j")
add("scaled_h2", "transfer_function_h2", X, Y, 2.0, 2, [1 + 1j, 1 + 1j],
    SCALED + ", so H2 = 2 Sxx / ((1 - j) Sxx) = 1 + j")
add("scaled_coherence", "coherence", X, Y, 2.0, 2, [1.0, 1.0],
    SCALED + ", so |Sxy|^2 / (Sxx Syy) = 2 / 2 = 1")
ONE = ("x = [1, j], y = [1, 0]: X = [1 + j, 1 - j], Y = [1, 1]; one segment, so H = Y / X = "
       "[(1 - j)/2, (1 + j)/2]; shifted [bin 1, bin 0]: [(1 + j)/2, (1 - j)/2]")
add("single_h1", "transfer_function", [1.0, 1j], [1.0, 0.0], 2.0, 2, [0.5 + 0.5j, 0.5 - 0.5j], ONE)
add("single_h2", "transfer_function_h2", [1.0, 1j], [1.0, 0.0], 2.0, 2, [0.5 + 0.5j, 0.5 - 0.5j],
    ONE + " (H2 = |Y|^2 / (conj Y X) = Y / X too)")
TWO = ("x = [1, j] twice, y = [1, 0], [0, 1]: X = [1 + j, 1 - j] twice, Y = [1, 1], [1, -1]. "
       "Sxx = [4, 4], Syy = [2, 2], Sxy = [(1 - j) 2, (1 + j) 0] = [2 - 2j, 0]")
XT, YT = [1.0, 1j, 1.0, 1j], [1.0, 0.0, 0.0, 1.0]
add("disagree_h1", "transfer_function", XT, YT, 2.0, 2, [0j, 0.5 - 0.5j],
    TWO + ". H1 = [0.5 - 0.5j, 0]; shifted [0, 0.5 - 0.5j]")
add("disagree_h2", "transfer_function_h2", XT, YT, 2.0, 2, [NAN, 0.5 - 0.5j],
    TWO + ". H2 = Syy / conj Sxy = [2 / (2 + 2j), NaN] = [0.5 - 0.5j, NaN]; shifted [NaN, "
    "0.5 - 0.5j]")
add("disagree_coherence", "coherence", XT, YT, 2.0, 2, [0.0, 1.0],
    TWO + ". Coherence = [8 / 8, 0]; shifted [0, 1]")
MIX = ("real x = delta, complex y = [j, 1]: X = [1, 1], Y = [1 + j, -1 + j]; H = Y; shifted "
       "[-1 + j, 1 + j]")
add("mixed_h1", "transfer_function", [1.0, 0.0], [1j, 1.0], 4.0, 2, [-1 + 1j, 1 + 1j], MIX)
add("mixed_coherence", "coherence", [1.0, 0.0], [1j, 1.0], 4.0, 2, [1.0, 1.0],
    MIX + "; one segment, so coherence 1")


def err(cid, op, x, y, why):
    cases.append({"id": f"complex_cross_spectra.{cid}", "op": op,
                  "args": {"x": x, "y": y, "sample_rate": 1.0}, "error": "invalid_argument",
                  "source": why})


err("lengths", "coherence", {"re": [1.0, 2.0], "im": [0.0, 1.0]}, [1.0], "x and y differ in length")
err("nan", "transfer_function", {"re": [1.0, 2.0], "im": ["nan", 1.0]}, [1.0, 2.0], "not finite")

doc = {
    "schema": 1,
    "suite": "complex_cross_spectra",
    "description": "Coherence, H1 and H2 of complex input (conventions: Complex coherence and "
    "transfer functions; ADR 0197).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "complex_cross_spectra.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/complex_cross_spectra.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
