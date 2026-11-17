"""Writes vectors/cases/ar_psd.json, stdlib only.

AR model PSD (conventions: AR model PSD; ADR 0223). |A_k|^2 is summed directly as
sum_j sum_l a_j conj(a_l) e^(-2 pi i (j - l) k / M), no FFT; the density sigma^2 / (fs |A_k|^2)
is folded as Welch (one-sided interior doubled, else fftshift). The order-1 case is checked
against 1 + a^2 + 2 a cos(2 pi k / M), and ADR 0203's x = [1, 2] model against its yule_walker_psd
vector.

Run from the repo root: python vectors/generators/ar_psd.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def mag2(a, k, m):
    s = 0j
    for j, aj in enumerate(a):
        for l, al in enumerate(a):
            s += aj * complex(al).conjugate() * cmath.exp(-2j * math.pi * (j - l) * k / m)
    return s.real


def density(a, e, fs, m, one_sided):
    two = [e / (fs * mag2(a, k, m)) for k in range(m)]
    if one_sided:
        h = m // 2 + 1
        last = h - 1 if m % 2 == 0 else h
        psd = [two[k] * (2.0 if 1 <= k < last else 1.0) for k in range(h)]
        freqs = [k * (fs / m) for k in range(h)]
    else:
        psd = [two[(i + (m + 1) // 2) % m] for i in range(m)]
        freqs = [(i - m // 2) * (fs / m) for i in range(m)]
    return freqs, psd


def enc(vs):
    if any(isinstance(v, complex) for v in vs):
        return {"re": [complex(v).real for v in vs], "im": [complex(v).imag for v in vs]}
    return [float(v) for v in vs]


def add(cid, a, e, fs, m, one_sided, why, flag=None):
    freqs, psd = density(a, e, fs, m, one_sided)
    args = {"coefficients": enc(a), "error": e, "sample_rate": fs, "nfft": m}
    if flag is not None:
        args["one_sided"] = flag
    cases.append({"id": f"ar_psd.{cid}", "op": "ar_psd", "args": args,
                  "expected": {"frequencies": freqs, "psd": psd, "sample_rate": fs, "nperseg": m,
                               "num_segments": 1, "one_sided": one_sided, "bin_width": fs / m,
                               "enbw_hz": fs / m, "nfft": m},
                  "tol": TOL, "source": why})
    return freqs, psd


_, two = add("order_one_two_sided", [1.0, 0.5], 1.5, 8.0, 8, False,
             "1.5 / (8 (1 + a^2 + 2 a cos(2 pi k / 8))), a = 1/2, shifted", flag=False)
closed = [1.5 / (8.0 * (1.25 + math.cos(2 * math.pi * (i - 4) / 8))) for i in range(8)]
assert all(abs(x - y) < 1e-14 for x, y in zip(two, closed))
_, one = add("yule_walker_two_samples", [1.0, -0.4], 2.1, 1.0, 2, True,
             "ADR 0203's x = [1, 2] model: a1 = -2/5, sigma^2 = 21/10")
assert abs(one[0] - 5.833333333333334) < 1e-14 and abs(one[1] - 1.0714285714285716) < 1e-14
add("order_two_odd_nfft", [1.0, -0.9, 0.5], 0.3, 1000.0, 9, True, "odd nfft: no Nyquist bin")
add("order_two_even_nfft", [1.0, -0.9, 0.5], 0.3, 1000.0, 16, True, "even nfft: half-bin Nyquist")
add("order_three_minimal_nfft", [1.0, 0.2, -0.3, 0.1], 2.0, 4.0, 4, True, "nfft = order + 1")
add("complex", [1.0, -0.5 + 0.5j, 0.25j], 1.0, 10.0, 7, False, "complex: two-sided, shifted")
add("not_minimum_phase", [1.0, 2.0], 1.0, 1.0, 5, True, "|A|^2 = 5 + 4 cos w > 0: allowed")


def err(cid, why, **args):
    cases.append({"id": f"ar_psd.{cid}", "op": "ar_psd", "args": args,
                  "error": "invalid_argument", "source": why})


err("vanishes", "a = [1, 1] has A = 0 at fs/2, a bin of nfft = 4", coefficients=[1.0, 1.0],
    error=1.0, sample_rate=1.0, nfft=4)
err("nfft_too_small", "nfft must be at least order + 1", coefficients=[1.0, 0.2, 0.1],
    error=1.0, sample_rate=1.0, nfft=2)
err("a0", "coefficients[0] must be 1", coefficients=[2.0, 0.5], error=1.0, sample_rate=1.0,
    nfft=8)
err("zero_error", "error must be positive", coefficients=[1.0, 0.5], error=0.0,
    sample_rate=1.0, nfft=8)
err("zero_rate", "sample_rate must be positive", coefficients=[1.0, 0.5], error=1.0,
    sample_rate=0.0, nfft=8)
err("empty", "coefficients must not be empty", coefficients=[], error=1.0, sample_rate=1.0,
    nfft=8)
err("nan", "coefficients must be finite", coefficients=[1.0, "nan"], error=1.0, sample_rate=1.0,
    nfft=8)

doc = {
    "schema": 1,
    "suite": "ar_psd",
    "description": "AR model PSD (conventions: AR model PSD; ADR 0223).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "ar_psd.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/ar_psd.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
