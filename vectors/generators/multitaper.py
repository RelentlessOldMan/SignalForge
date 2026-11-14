"""Writes vectors/cases/multitaper.json from the definitions, using only the Python standard library.

It does not import NumPy or SignalForge. The tapers are the eigenvectors of the commuting
tridiagonal matrix of conventions: Spectra (DPSS tapers), found here by cyclic Jacobi rotations on
the whole matrix (not the library's bisection and inverse iteration). Every taper is then checked
against the definition itself: A v = lambda v for the sinc matrix A[n][m] = sin(2 pi W (n - m)) /
(pi (n - m)), to 1e-10, and the tapers are checked orthonormal. Each concentration is v'Av summed
directly. Multitaper PSDs are the DFT of each tapered input summed term by term, averaged, scaled
by 1/(K fs) and folded as Welch, or combined by iterating Thomson's adaptive weights bin by bin
(conventions: Spectra, Multitaper PSD; ADR 0079). The harmonic F-test regresses the same tapered
DFTs on the tapers' sums, bin by bin (conventions: Spectra, Harmonic F-test; ADR 0080).

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


def adaptive(eigen, lam, noise):
    """Thomson's adaptive combination of one bin's eigenspectra (ADR 0079)."""
    s = eigen[0] if len(lam) == 1 else (eigen[0] + eigen[1]) / 2
    if len(lam) == 1 or noise == 0:
        return s
    for _ in range(1000):
        if s <= 0:
            break
        w = [lj / (lj * s + (1 - lj) * noise) ** 2 for lj in lam]
        new = math.fsum(wj * ej for wj, ej in zip(w, eigen)) / math.fsum(w)
        done = abs(new - s) <= 1e-10 * new
        s = new
        if done:
            break
    return s


def multitaper(x, fs, nw, k=None, one_sided=None, nfft=None, adapt=False):
    is_complex = any(isinstance(v, complex) for v in x)
    if one_sided is None:
        one_sided = not is_complex
    n = len(x)
    m = n if nfft is None else nfft
    tapers, lam = dpss(n, nw, k)
    kk = len(tapers)
    eigen = []
    for v in tapers:
        seg = [v[i] * x[i] for i in range(n)]
        eigen.append([abs(sum(seg[i] * cmath.exp(-2j * math.pi * b * i / m) for i in range(n))) ** 2
                      / fs for b in range(m)])
    if adapt:
        noise = math.fsum(abs(v) ** 2 for v in x) / n / fs
        p = [adaptive([e[b] for e in eigen], lam, noise) for b in range(m)]
    else:
        p = [math.fsum(e[b] for e in eigen) / kk for b in range(m)]
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


def f_test(x, fs, nw, k=None, nfft=None):
    """Thomson's harmonic F-test per bin by direct sums (ADR 0080)."""
    is_complex = any(isinstance(v, complex) for v in x)
    n = len(x)
    m = n if nfft is None else nfft
    tapers, _ = dpss(n, nw, k)
    kk = len(tapers)
    u = [math.fsum(v) for v in tapers]
    uu = math.fsum(a * a for a in u)
    bins = range(m // 2 + 1) if not is_complex else [(i - m // 2) % m for i in range(m)]
    mus, fs_, ps = [], [], []
    for b in bins:
        xs = [sum(v[i] * x[i] * cmath.exp(-2j * math.pi * b * i / m) for i in range(n))
              for v in tapers]
        mu = sum(a * y for a, y in zip(u, xs)) / uu
        resid = math.fsum(abs(y - mu * a) ** 2 for a, y in zip(u, xs))
        num = (kk - 1) * abs(mu) ** 2 * uu
        f = num / resid if resid > 0 else (math.inf if num > 0 else 0.0)
        mus.append(complex(mu))
        fs_.append(f)
        ps.append(0.0 if f == math.inf else (1 + f / (kk - 1)) ** -(kk - 1))
    if is_complex:
        freqs = [(i - m // 2) * fs / m for i in range(m)]
    else:
        freqs = [b * fs / m for b in bins]
    return {"frequencies": freqs, "amplitudes": cplx(mus), "f_statistic": fs_, "p_values": ps,
            "num_tapers": kk}


def same(a, b, tol=1e-14):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k], tol) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, int | float) and isinstance(b, int | float) and not isinstance(a, bool):
        return a == b or abs(a - b) <= tol * max(1.0, abs(b))
    return a == b


def cplx(z):
    return {"re": [v.real for v in z], "im": [v.imag for v in z]}


SRC = ("vectors/generators/multitaper.py (stdlib only): eigenvectors of the commuting tridiagonal "
       "matrix by cyclic Jacobi, each checked against the sinc eigen-equation to 1e-10")
PSRC = SRC + "; each tapered DFT summed term by term, averaged and folded per conventions: Spectra"
FSRC = SRC + ("; each tapered DFT summed term by term, regressed on the tapers' sums per "
               "conventions: Harmonic F-test")
ASRC = PSRC.replace("averaged", "combined by iterating Thomson's adaptive weights per bin (ADR 0079)")


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
    expected = multitaper(x, fs, nw, kw.get("num_tapers"), kw.get("one_sided"), kw.get("nfft"),
                          kw.get("adaptive", False))
    if psd is not None:  # a hand derivation replaces the sums
        assert max(abs(a - b) for a, b in zip(psd, expected["psd"])) < 1e-12
        expected["psd"] = psd
    return {"id": case_id, "op": "multitaper_psd", "args": args, "expected": expected, "tol": TOL,
            "source": src}


def f_case(case_id, x, fs, nw, src=FSRC, expected=None, **kw):
    args = {"samples": cplx(x) if any(isinstance(v, complex) for v in x) else x, "sample_rate": fs,
            "half_bandwidth": nw} | kw
    computed = f_test(x, fs, nw, kw.get("num_tapers"), kw.get("nfft"))
    if expected is not None:  # a hand derivation replaces the sums
        assert same(expected, computed, 1e-12), (expected, computed)
        computed = expected
    return {"id": case_id, "op": "harmonic_f_test", "args": args, "expected": computed, "tol": TOL,
            "source": src}


def err(case_id, op, args, why):
    return {"id": case_id, "op": op, "args": args, "error": "invalid_argument", "source": why}


R2 = 1 / math.sqrt(2)
ramp = [float(i % 5) - 2 + 0.25 * math.sin(0.7 * i) for i in range(40)]
tone = [math.sin(2 * math.pi * 0.1013 * i) + 1e-4 * math.cos(2 * math.pi * 0.37 * i)
        for i in range(48)]
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
    psd_case("multitaper.adaptive_real_tone", tone, 1.0, 3.0, adaptive=True,
             src=ASRC),
    psd_case("multitaper.adaptive_real_two_sided_padded", ramp, 1000.0, 2.5, adaptive=True,
             one_sided=False, nfft=48, src=ASRC),
    psd_case("multitaper.adaptive_complex", chirp, 1e6, 3.0, num_tapers=5, adaptive=True,
             src=ASRC),
    psd_case("multitaper.adaptive_one_taper", ramp[:21], 2.0, 2.0, num_tapers=1, adaptive=True,
             psd=multitaper(ramp[:21], 2.0, 2.0, 1)["psd"],
             src="by hand: with one taper the adaptive estimate is the plain one (here the plain "
             "estimate from this generator's sums)"),
    psd_case("multitaper.adaptive_equal_eigenspectra", [3.0, 0.0], 2.0, 0.4, num_tapers=2,
             adaptive=True, psd=[2.25, 2.25],
             src="by hand: both N = 2 tapers times (3, 0) are (3/sqrt 2, 0), so both eigenspectra "
             "are 4.5/fs = 2.25 in each bin and any weighted mean of them is 2.25"),
    psd_case("multitaper.adaptive_zeros", [0.0] * 8, 2.0, 2.0, adaptive=True,
             psd=[0.0] * 5, src="by hand: all-zero input gives zeros"),
    f_case("multitaper.f_test_real_tone", tone, 1.0, 3.0),
    f_case("multitaper.f_test_real_padded", ramp, 1000.0, 2.5, num_tapers=3, nfft=45),
    f_case("multitaper.f_test_complex", chirp, 1e6, 3.0, num_tapers=5),
    f_case("multitaper.f_test_complex_padded_odd", chirp, 1e6, 2.0, nfft=31),
    f_case("multitaper.f_test_length_two", [3.0, 1.0], 1.0, 0.4, num_tapers=2,
           expected={"frequencies": [0.0, 0.5], "amplitudes": {"re": [2.0, 1.0], "im": [0.0, 0.0]},
                     "f_statistic": [4.0, 0.25], "p_values": [0.2, 0.8], "num_tapers": 2},
           src="by hand: with tapers (1, 1)/sqrt 2 and (1, -1)/sqrt 2, U = (sqrt 2, 0); bin 0 has "
           "X = (4, 2)/sqrt 2, so mu = 2, F = 1*4*2/2 = 4; bin 1 has X = (2, 4)/sqrt 2, so mu = 1, "
           "F = 2/8 = 0.25; p = 1/(1 + F)"),
    f_case("multitaper.f_test_zeros", [0.0] * 8, 1.0, 2.0,
           expected={"frequencies": [0.0, 0.125, 0.25, 0.375, 0.5],
                     "amplitudes": {"re": [0.0] * 5, "im": [0.0] * 5},
                     "f_statistic": [0.0] * 5, "p_values": [1.0] * 5, "num_tapers": 3},
           src="by hand: all-zero input has mu = 0 and residual 0, so F = 0 and p = 1"),
    err("multitaper.f_test_one_taper", "harmonic_f_test",
        {"samples": ramp, "sample_rate": 1.0, "half_bandwidth": 2.0, "num_tapers": 1},
        "the F-test needs at least 2 tapers"),
    err("multitaper.f_test_default_one_taper", "harmonic_f_test",
        {"samples": ramp, "sample_rate": 1.0, "half_bandwidth": 1.0},
        "NW 1 gives one taper by default, too few for the F-test"),
    err("multitaper.f_test_empty", "harmonic_f_test",
        {"samples": [], "sample_rate": 1.0, "half_bandwidth": 1.0}, "at least one sample required"),
    err("multitaper.f_test_nfft_short", "harmonic_f_test",
        {"samples": ramp, "sample_rate": 1.0, "half_bandwidth": 2.0, "nfft": 39},
        "nfft >= number of samples required"),
    err("multitaper.f_test_rate_zero", "harmonic_f_test",
        {"samples": ramp, "sample_rate": 0.0, "half_bandwidth": 2.0},
        "sample_rate must be positive"),
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
    "description": "DPSS tapers, Thomson's multitaper PSD (plain and adaptive) and harmonic "
    "F-test (conventions: Spectra, DPSS tapers, Multitaper PSD, Harmonic F-test).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "multitaper.json"




if "--check" in sys.argv[1:]:
    if not same(json.loads(out.read_text(encoding="utf-8")), json.loads(json.dumps(doc))):
        sys.exit(f"{out} is out of date: run python vectors/generators/multitaper.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
