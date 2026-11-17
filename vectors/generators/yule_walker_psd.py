"""Writes vectors/cases/yule_walker_psd.json, stdlib only.

Yule-Walker AR PSD (conventions: Yule-Walker AR PSD; ADR 0203). Each case solves the normal
equations sum_j a_j r[i - j] = 0 (i = 1 .. p, a_0 = 1, r[-k] = conj r[k]) by Cramer's rule,
takes sigma^2 = sum_j a_j r[-j], and evaluates sigma^2 / (fs |sum_j a_j e^(-2 pi i j k/M)|^2) at
each bin with cmath. No Levinson recursion and no FFT.

Run from the repo root: python vectors/generators/yule_walker_psd.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def r_biased(x, k):
    n = len(x)
    return sum(x[i + k] * complex(x[i]).conjugate() for i in range(n - k)) / n


def fit(x, p):
    r = [complex(r_biased(x, k)) for k in range(p + 1)]
    rm = lambda k: r[k] if k >= 0 else r[-k].conjugate()  # noqa: E731
    if p == 1:
        a = [1, -r[1] / r[0]]
    else:
        # a1 r0 + a2 r[-1] = -r1 ; a1 r1 + a2 r0 = -r2
        det = r[0] * r[0] - rm(-1) * r[1]
        a1 = (-r[1] * r[0] - rm(-1) * -r[2]) / det
        a2 = (r[0] * -r[2] - r[1] * -r[1]) / det
        a = [1, a1, a2]
    sigma2 = sum(a[j] * rm(-j) for j in range(p + 1))
    assert abs(sigma2.imag) < 1e-12
    return a, sigma2.real


def add(cid, x, fs, p, why, nfft=None, one_sided=None):
    is_complex = any(isinstance(v, complex) for v in x)
    side = (not is_complex) if one_sided is None else one_sided
    n = len(x)
    m = n if nfft is None else nfft
    a, s2 = fit(x, p)
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
    cases.append({"id": f"yule_walker_psd.{cid}", "op": "yule_walker_psd", "args": args,
                  "expected": {"frequencies": freqs, "psd": psd, "sample_rate": fs, "nperseg": n,
                               "num_segments": 1, "one_sided": side, "bin_width": fs / m,
                               "enbw_hz": fs / n, "nfft": m},
                  "tol": TOL, "source": why})


a_check, s_check = fit([1.0, 2.0], 1)
assert abs(a_check[1] + 0.4) < 1e-15 and abs(s_check - 2.1) < 1e-15
add("ar1_two_samples", [1.0, 2.0], 1.0, 1,
    "x = [1, 2]: r0 = 5/2, r1 = 1, a1 = -2/5, sigma^2 = 21/10; |A|^2 = 9/25 at DC, 49/25 at fs/2")
add("ar1_padded", [1.0, 2.0], 10.0, 1,
    "x = [1, 2], M = 8: sigma^2 / (fs (1 + a^2 + 2 a cos(2 pi k/8))), interior doubled", nfft=8)
add("ar1_two_sided", [1.0, 2.0], 4.0, 1, "real input, one_sided = false: all 4 bins, shifted",
    nfft=4, one_sided=False)
add("ar2", [3.0, 1.0, -2.0, 0.0, 1.0], 2.0, 2,
    "order 2 by Cramer's rule on the biased r0, r1, r2; M = 6, interior doubled", nfft=6)
add("ar2_odd_bins", [0.5, -1.0, 2.0, 1.5, -0.5, 0.25], 1.0, 2,
    "order 2, M = 7 (odd): bins 0 .. 3, all but DC doubled", nfft=7)
add("complex_ar1", [1 + 0j, 1j], 4.0, 1,
    "x = [1, i]: r0 = 1, r1 = i/2, a1 = -i/2, sigma^2 = 3/4; two-sided, shifted, M = 4", nfft=4)
add("complex_ar2", [1 + 1j, -0.5 + 2j, 1.5 - 1j, 0.25j, -1 + 0j], 1.0, 2,
    "complex order 2 by Cramer's rule with r[-1] = conj r1; M = 5, shifted", )


def err(cid, why, **args):
    cases.append({"id": f"yule_walker_psd.{cid}", "op": "yule_walker_psd", "args": args,
                  "error": "invalid_argument", "source": why})


err("order_zero", "order must be at least 1", samples=[1.0, 2.0], sample_rate=1.0, order=0)
err("order_too_big", "order must be below the input length", samples=[1.0, 2.0],
    sample_rate=1.0, order=2)
err("nfft_too_small", "nfft must be at least order + 1", samples=[1.0, 2.0, 3.0, 4.0],
    sample_rate=1.0, order=2, nfft=2)
err("zero_rate", "sample_rate must be positive", samples=[1.0, 2.0], sample_rate=0.0, order=1)
err("all_zero", "r[0] = 0: Levinson needs r[0] > 0", samples=[0.0, 0.0, 0.0], sample_rate=1.0,
    order=1)
err("nan_sample", "samples must be finite", samples=[1.0, "nan", 2.0], sample_rate=1.0, order=1)

doc = {
    "schema": 1,
    "suite": "yule_walker_psd",
    "description": "Yule-Walker AR PSD (conventions: Yule-Walker AR PSD; ADR 0203).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "yule_walker_psd.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/yule_walker_psd.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
