"""Writes vectors/cases/multitaper.json from the definitions, using only the Python standard library.

It does not import NumPy or SignalForge. The tapers are the eigenvectors of the commuting
tridiagonal matrix of conventions: Spectra (DPSS tapers), found here by cyclic Jacobi rotations on
the whole matrix (not the library's bisection and inverse iteration). Every taper is then checked
against the definition itself: A v = lambda v for the sinc matrix A[n][m] = sin(2 pi W (n - m)) /
(pi (n - m)), to 1e-10, and the tapers are checked orthonormal. Each concentration is v'Av summed
directly. Multitaper PSDs are the DFT of each tapered input summed term by term, averaged, scaled
by 1/(K fs) and folded as Welch (conventions: Spectra, Multitaper PSD).

Run from the repo root: python vectors/generators/multitaper.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-10, "rel": 1e-10}


def jacobi(a):
    """Eigenvalues and unit eigenvectors (columns) of the symmetric matrix a, by cyclic Jacobi."""
    n = len(a)
    a = [row[:] for row in a]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for _ in range(100):
        off = math.fsum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j)
        if off < 1e-30 * max(1.0, math.fsum(a[i][i] ** 2 for i in range(n))):
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if a[p][q] == 0.0:
                    continue
                theta = (a[q][q] - a[p][p]) / (2 * a[p][q])
                t = math.copysign(1.0, theta) / (abs(theta) + math.sqrt(theta * theta + 1))
                c = 1 / math.sqrt(t * t + 1)
                s = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p], a[k][q] = c * akp - s * akq, s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k], a[q][k] = c * apk - s * aqk, s * apk + c * aqk
                for k in range(n):
                    vkp, vkq = v[k][p], v[k][q]
                    v[k][p], v[k][q] = c * vkp - s * vkq, s * vkp + c * vkq
    return [a[i][i] for i in range(n)], [[v[k][i] for k in range(n)] for i in range(n)]


def sinc_matrix(n, w):
    return [[2 * w if i == j else math.sin(2 * math.pi * w * (i - j)) / (math.pi * (i - j))
             for j in range(n)] for i in range(n)]


def dpss(n, nw, k=None):
    w = nw / n
    k = max(1, math.floor(2 * nw) - 1) if k is None else k
    t = [[0.0] * n for _ in range(n)]
    for i in range(n):
        t[i][i] = ((n - 1) / 2 - i) ** 2 * math.cos(2 * math.pi * w)
        if i:
            t[i - 1][i] = t[i][i - 1] = i * (n - i) / 2
    vals, vecs = jacobi(t)
    order = sorted(range(n), key=lambda i: -vals[i])[:k]
    a = sinc_matrix(n, w)
    tapers, conc = [], []
    mid = (n - 1) / 2
    for j, i in enumerate(order):
        v = vecs[i]
        norm = math.sqrt(math.fsum(x * x for x in v))
        v = [x / norm for x in v]
        sign = math.fsum(v) if j % 2 == 0 else math.fsum((mid - m) * x for m, x in enumerate(v))
        if sign < 0:
            v = [-x for x in v]
        av = [math.fsum(a[r][m] * v[m] for m in range(n)) for r in range(n)]
        lam = math.fsum(x * y for x, y in zip(v, av))
        assert max(abs(x - lam * y) for x, y in zip(av, v)) < 1e-10, (n, nw, j)
        tapers.append(v)
        conc.append(lam)
    for p in range(k):
        for q in range(k):
            dot = math.fsum(x * y for x, y in zip(tapers[p], tapers[q]))
            assert abs(dot - (p == q)) < 1e-12, (n, nw, p, q)
    assert all(p >= q - 1e-14 for p, q in zip(conc, conc[1:]))
    return tapers, conc


def multitaper(x, fs, nw, k=None, one_sided=None, nfft=None):
    is_complex = any(isinstance(v, complex) for v in x)
    if one_sided is None:
        one_sided = not is_complex
    n = len(x)
    m = n if nfft is None else nfft
    tapers, _ = dpss(n, nw, k)
    kk = len(tapers)
    p = [0.0] * m
    for v in tapers:
        seg = [v[i] * x[i] for i in range(n)]
        for b in range(m):
            p[b] += abs(sum(seg[i] * cmath.exp(-2j * math.pi * b * i / m) for i in range(n))) ** 2
    p = [q / (kk * fs) for q in p]
    if one_sided:
        h = m // 2 + 1
        last = h - 1 if m % 2 == 0 else h
        psd = [p[b] * (2 if 1 <= b < last else 1) for b in range(h)]
        freqs = [b * fs / m for b in range(h)]
    else:
        psd = [p[(i - m // 2) % m] for i in range(m)]
        freqs = [(i - m // 2) * fs / m for i in range(m)]
    return {"frequencies": freqs, "psd": psd, "sample_rate": fs, "nperseg": n, "num_segments": kk,
            "one_sided": one_sided, "bin_width": fs / m, "enbw_hz": 2 * nw / n * fs, "nfft": m}


def cplx(z):
    return {"re": [v.real for v in z], "im": [v.imag for v in z]}


SRC = ("vectors/generators/multitaper.py (stdlib only): eigenvectors of the commuting tridiagonal "
       "matrix by cyclic Jacobi, each checked against the sinc eigen-equation to 1e-10")
PSRC = SRC + "; each tapered DFT summed term by term, averaged and folded per conventions: Spectra"


def taper_case(case_id, n, nw, k=None, src=SRC, expected=None):
    args = {"length": n, "half_bandwidth": nw} | ({} if k is None else {"num_tapers": k})
    if expected is None:
        tapers, conc = dpss(n, nw, k)
        expected = {"tapers": tapers, "concentrations": conc}
    return {"id": case_id, "op": "dpss_tapers", "args": args, "expected": expected, "tol": TOL,
            "source": src}


def psd_case(case_id, x, fs, nw, src=PSRC, psd=None, **kw):
    args = {"samples": cplx(x) if any(isinstance(v, complex) for v in x) else x, "sample_rate": fs,
            "half_bandwidth": nw} | kw
    expected = multitaper(x, fs, nw, kw.get("num_tapers"), kw.get("one_sided"), kw.get("nfft"))
    if psd is not None:  # a hand derivation replaces the sums
        assert max(abs(a - b) for a, b in zip(psd, expected["psd"])) < 1e-12
        expected["psd"] = psd
    return {"id": case_id, "op": "multitaper_psd", "args": args, "expected": expected, "tol": TOL,
            "source": src}


def err(case_id, op, args, why):
    return {"id": case_id, "op": op, "args": args, "error": "invalid_argument", "source": why}


R2 = 1 / math.sqrt(2)
ramp = [float(i % 5) - 2 + 0.25 * math.sin(0.7 * i) for i in range(40)]
chirp = [cmath.exp(1j * (0.3 * i + 0.02 * i * i)) * (1 + 0.05 * i) for i in range(24)]

cases = [
    taper_case("multitaper.dpss_length_one", 1, 0.3, src="by hand: N = 1 gives the taper [1] and "
               "concentration 2W = 0.6", expected={"tapers": [[1.0]], "concentrations": [0.6]}),
    taper_case("multitaper.dpss_length_two", 2, 0.4, 2,
               src="by hand: N = 2 gives (1, 1)/sqrt 2 and (1, -1)/sqrt 2 (sign rule), with "
               "concentrations 2W +- sin(2 pi W)/pi, W = 0.2",
               expected={"tapers": [[R2, R2], [R2, -R2]],
                         "concentrations": [0.4 + math.sin(0.4 * math.pi) / math.pi,
                                            0.4 - math.sin(0.4 * math.pi) / math.pi]}),
    taper_case("multitaper.dpss_16_nw_2_5_default", 16, 2.5),
    taper_case("multitaper.dpss_64_nw_4_seven", 64, 4.0, 7),
    taper_case("multitaper.dpss_33_odd_three", 33, 3.0, 3),
    taper_case("multitaper.dpss_20_nw_1_5_all", 20, 1.5, 20),
    psd_case("multitaper.real_one_sided", ramp, 1000.0, 3.0),
    psd_case("multitaper.real_two_sided", ramp, 1000.0, 2.5, one_sided=False),
    psd_case("multitaper.real_padded_odd", ramp[:21], 2.0, 2.0, num_tapers=2, nfft=32),
    psd_case("multitaper.complex_two_sided", chirp, 1e6, 3.0),
    psd_case("multitaper.complex_padded", chirp, 1e6, 2.0, num_tapers=4, nfft=31),
    psd_case("multitaper.constant_two", [3.0, 3.0], 2.0, 0.4, num_tapers=2, psd=[4.5, 4.5],
             src="by hand: the two N = 2 tapers put 2c^2 in bin 0 and 2c^2 in bin 1; over K fs "
             "= 4 that is c^2/fs = 4.5 in each, and neither bin is doubled at nfft 2"),
    err("multitaper.dpss_length_zero", "dpss_tapers", {"length": 0, "half_bandwidth": 0.5},
        "length >= 1 required"),
    err("multitaper.dpss_nw_zero", "dpss_tapers", {"length": 8, "half_bandwidth": 0.0},
        "half_bandwidth > 0 required"),
    err("multitaper.dpss_nw_half_length", "dpss_tapers", {"length": 8, "half_bandwidth": 4.0},
        "half_bandwidth < length/2 required"),
    err("multitaper.dpss_nw_nan", "dpss_tapers", {"length": 8, "half_bandwidth": "nan"},
        "half_bandwidth must be finite"),
    err("multitaper.dpss_k_zero", "dpss_tapers", {"length": 8, "half_bandwidth": 2.0,
                                                  "num_tapers": 0}, "num_tapers >= 1 required"),
    err("multitaper.dpss_k_above_length", "dpss_tapers",
        {"length": 8, "half_bandwidth": 2.0, "num_tapers": 9}, "num_tapers <= length required"),
    err("multitaper.psd_empty", "multitaper_psd", {"samples": [], "sample_rate": 1.0,
                                                   "half_bandwidth": 1.0},
        "at least one sample required"),
    err("multitaper.psd_nfft_short", "multitaper_psd",
        {"samples": ramp, "sample_rate": 1.0, "half_bandwidth": 2.0, "nfft": 39},
        "nfft >= number of samples required"),
    err("multitaper.psd_rate_zero", "multitaper_psd",
        {"samples": ramp, "sample_rate": 0.0, "half_bandwidth": 2.0}, "sample_rate must be positive"),
    err("multitaper.psd_nw_too_wide", "multitaper_psd",
        {"samples": ramp[:6], "sample_rate": 1.0, "half_bandwidth": 3.0},
        "half_bandwidth < length/2 required"),
]

doc = {
    "schema": 1,
    "suite": "multitaper",
    "description": "DPSS tapers and Thomson's multitaper PSD (conventions: Spectra, DPSS tapers, "
    "Multitaper PSD).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "multitaper.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/multitaper.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
