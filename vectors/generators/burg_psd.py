"""Writes vectors/cases/burg_psd.json, stdlib only.

Burg AR PSD (conventions: Burg AR PSD; ADR 0204). Each case runs the forward/backward error
recursion written out here with plain lists, then evaluates sigma^2 / (fs |sum_j a_j
e^(-2 pi i j k/M)|^2) at each bin with cmath. The 3-sample case is pinned to exact fractions and
order 1 to its closed form.

Run from the repo root: python vectors/generators/burg_psd.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def fit(x, p):
    f = [complex(v) for v in x]
    b = list(f)
    a = [1 + 0j]
    err = sum(abs(v) ** 2 for v in f) / len(f)
    ks = []
    for _ in range(p):
        fw, bw = f[1:], b[:-1]
        k = -2 * sum(u * v.conjugate() for u, v in zip(fw, bw)) / sum(
            abs(u) ** 2 + abs(v) ** 2 for u, v in zip(fw, bw))
        f = [u + k * v for u, v in zip(fw, bw)]
        b = [v + k.conjugate() * u for u, v in zip(fw, bw)]
        a = a + [0j]
        a = [a[j] + k * a[len(a) - 1 - j].conjugate() for j in range(len(a))]
        err *= 1 - abs(k) ** 2
        ks.append(k)
    return a, err, ks


a3, e3, k3 = fit([1.0, 2.0, 3.0], 2)
assert abs(k3[0] + 8 / 9) < 1e-15 and abs(k3[1] - 77 / 85) < 1e-15
assert abs(a3[1] + 144 / 85) < 1e-14 and abs(a3[2] - 77 / 85) < 1e-15
assert abs(e3 - 14 / 3 * 17 / 81 * 1296 / 7225) < 1e-15
xo = [0.5, -1.0, 2.0, 1.5]
k_closed = -2 * sum(xo[i] * xo[i - 1] for i in range(1, 4)) / sum(
    xo[i] ** 2 + xo[i - 1] ** 2 for i in range(1, 4))
assert abs(fit(xo, 1)[2][0] - k_closed) < 1e-15


def add(cid, x, fs, p, why, nfft=None, one_sided=None):
    is_complex = any(isinstance(v, complex) for v in x)
    side = (not is_complex) if one_sided is None else one_sided
    n = len(x)
    m = n if nfft is None else nfft
    a, s2, _ = fit(x, p)
    two = []
    for k in range(m):
        big_a = sum(a[j] * cmath.exp(-2j * math.pi * j * k / m) for j in range(p + 1))
        two.append(s2 / (fs * abs(big_a) ** 2))
    if side:
        top = m // 2
        psd = [two[k] * (1 if k == 0 or (m % 2 == 0 and k == top) else 2) for k in range(top + 1)]
        freqs = [k * fs / m for k in range(top + 1)]
    else:
        order = [(i + m - m // 2) % m for i in range(m)]
        psd = [two[k] for k in order]
        freqs = [(k if k <= (m - 1) // 2 else k - m) * fs / m for k in order]
    args = {"samples": ({"re": [complex(v).real for v in x], "im": [complex(v).imag for v in x]}
                        if is_complex else x),
            "sample_rate": fs, "order": p}
    if nfft is not None:
        args["nfft"] = nfft
    if one_sided is not None:
        args["one_sided"] = one_sided
    cases.append({"id": f"burg_psd.{cid}", "op": "burg_psd", "args": args,
                  "expected": {"frequencies": freqs, "psd": psd, "sample_rate": fs, "nperseg": n,
                               "num_segments": 1, "one_sided": side, "bin_width": fs / m,
                               "enbw_hz": fs / n, "nfft": m},
                  "tol": TOL, "source": why})


add("three_samples", [1.0, 2.0, 3.0], 1.0, 2,
    "x = [1, 2, 3]: k1 = -8/9, k2 = 77/85, a = [1, -144/85, 77/85], sigma^2 = (14/3)(17/81)"
    "(1296/7225); M = 8", nfft=8)
add("order_one", [0.5, -1.0, 2.0, 1.5], 2.0, 1,
    "order 1: k = -2 sum x[n] x[n-1] / sum (x[n]^2 + x[n-1]^2), sigma^2 = mean x^2 (1 - k^2)")
add("order_three", [3.0, 1.0, -2.0, 0.0, 1.0, 2.5, -1.5], 1.0, 3,
    "order 3 by the error recursion; M = 9 (odd), interior doubled", nfft=9)
add("two_sided_real", [1.0, 2.0, 3.0], 3.0, 1, "real input, one_sided = false: shifted bins",
    nfft=6, one_sided=False)
add("complex_ar1", [1 + 0j, 1j, -0.5 + 0.5j], 4.0, 1, "complex order 1; M = 4, shifted", nfft=4)
add("complex_ar2", [1 + 1j, -0.5 + 2j, 1.5 - 1j, 0.25j, -1 + 0j], 1.0, 2,
    "complex order 2 by the error recursion with conj(k) in the backward update; M = 5, shifted")


def err(cid, why, **args):
    cases.append({"id": f"burg_psd.{cid}", "op": "burg_psd", "args": args,
                  "error": "invalid_argument", "source": why})


err("order_zero", "order must be at least 1", samples=[1.0, 2.0], sample_rate=1.0, order=0)
err("order_too_big", "order must be below the input length", samples=[1.0, 2.0],
    sample_rate=1.0, order=2)
err("nfft_too_small", "nfft must be at least order + 1", samples=[1.0, 2.0, 3.0, 4.0],
    sample_rate=1.0, order=2, nfft=2)
err("zero_rate", "sample_rate must be positive", samples=[1.0, 2.0], sample_rate=0.0, order=1)
err("all_zero", "the error energy is 0", samples=[0.0, 0.0, 0.0], sample_rate=1.0, order=1)
err("predictable", "x = [1, -1]: k = -2(-1)/2 = 1, sigma^2 = 0", samples=[1.0, -1.0],
    sample_rate=1.0, order=1)
err("nan_sample", "samples must be finite", samples=[1.0, "nan", 2.0], sample_rate=1.0, order=1)

doc = {
    "schema": 1,
    "suite": "burg_psd",
    "description": "Burg AR PSD (conventions: Burg AR PSD; ADR 0204).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "burg_psd.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/burg_psd.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
