"""Writes vectors/cases/error_rates.json from first principles, using only the Python standard library.

It does not import NumPy or SignalForge.

- 16-QAM and 64-QAM: the closed forms in the conventions, each checked here against a numerical
  integral of the Gaussian over the decision intervals of one 4-PAM or 8-PAM axis (piecewise
  Simpson between the thresholds, so the integrands are smooth).
- 8-PSK: the tail of the received phase's density,
  P(psi) = integral from psi to pi of p(phi), p(phi) = e^-g/(2 pi) + sqrt(g) cos(phi)
  e^(-g sin^2 phi) erfc(-sqrt(g) cos(phi)) / (2 sqrt(pi)), by Simpson with one Richardson step.
  The libraries integrate Pawula's form instead, so the two are independent.
- QPSK in Rayleigh fading: the closed form, checked against the AWGN curve averaged over the
  exponential density of |g|^2 (with x = u^2 so the integrand is smooth, Simpson with one
  Richardson step on [0, 12]).

Run from the repo root: python vectors/generators/error_rates.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import json
import math
import pathlib
import sys

LEVELS = [-math.inf, -5.0, 0.0, 4.0, 8.0, 12.0, 16.0]


def simpson(f, a, b, n):
    h = (b - a) / n
    s = f(a) + f(b)
    for i in range(1, n):
        s += (4 if i % 2 else 2) * f(a + i * h)
    return s * h / 3


def richardson(f, a, b, n):
    coarse, fine = simpson(f, a, b, n), simpson(f, a, b, 2 * n)
    return fine + (fine - coarse) / 15


def q(x):
    return 0.5 * math.erfc(x / math.sqrt(2))


def lin(db):
    return 0.0 if db == -math.inf else 10 ** (db / 10)


def qam16(eb_n0):
    a = math.sqrt(4 * eb_n0 / 5)
    p = 1.5 * q(a)
    return (3 * q(a) + 2 * q(3 * a) - q(5 * a)) / 4, 2 * p - p * p


def qam16_by_integral(eb_n0):
    """One 4-PAM axis, levels -3, -1, 1, 3 (Gray 10, 11, 01, 00), noise sigma^2 = 5/(Es/N0)."""
    if eb_n0 == 0:
        return 0.5, 15 / 16
    sigma = math.sqrt(5 / (4 * eb_n0))
    edges = [-2.0, 0.0, 2.0]
    bits = {3: (0, 0), 1: (0, 1), -1: (1, 1), -3: (1, 0)}
    region_bits = [(1, 0), (1, 1), (0, 1), (0, 0)]  # v < -2, -2..0, 0..2, v > 2
    bit_err = sym_err = 0.0
    for level, own in bits.items():
        lo, hi = level - 40 * sigma, level + 40 * sigma
        cuts = [lo] + [e for e in edges if lo < e < hi] + [hi]
        for x0, x1 in zip(cuts, cuts[1:]):
            mid = (x0 + x1) / 2
            region = sum(mid > e for e in edges)
            wrong = sum(b != o for b, o in zip(region_bits[region], own))
            if wrong:
                mass = richardson(lambda v, lv=level: math.exp(-((v - lv) ** 2) / (2 * sigma**2))
                               / (sigma * math.sqrt(2 * math.pi)), x0, x1, 2000)
                bit_err += wrong * mass / 2
                sym_err += mass
    bit_err /= 4  # mean over the four levels, of the two bits of this axis
    p = sym_err / 4
    return bit_err, 2 * p - p * p


def qam64(eb_n0):
    a = math.sqrt(2 * eb_n0 / 7)
    p = 1.75 * q(a)
    return (7 * q(a) + 6 * q(3 * a) - q(5 * a) + q(9 * a) - q(13 * a)) / 12, 2 * p - p * p


def qam64_by_integral(eb_n0):
    """One 8-PAM axis, levels -7..7 step 2 with the Gray labels of the conventions,
    noise sigma^2 = 7/(2 Eb/N0) in level units."""
    if eb_n0 == 0:
        return 0.5, 63 / 64
    sigma = math.sqrt(7 / (2 * eb_n0))
    labels = {7: (0, 0, 0), 5: (0, 0, 1), 3: (0, 1, 1), 1: (0, 1, 0),
              -1: (1, 1, 0), -3: (1, 1, 1), -5: (1, 0, 1), -7: (1, 0, 0)}
    edges = [-6.0, -4.0, -2.0, 0.0, 2.0, 4.0, 6.0]
    region_bits = [labels[-7 + 2 * j] for j in range(8)]
    bit_err = sym_err = 0.0
    for level, own in labels.items():
        lo, hi = level - 40 * sigma, level + 40 * sigma
        cuts = [lo] + [e for e in edges if lo < e < hi] + [hi]
        for x0, x1 in zip(cuts, cuts[1:]):
            region = sum((x0 + x1) / 2 > e for e in edges)
            wrong = sum(b != o for b, o in zip(region_bits[region], own))
            if wrong:
                mass = richardson(lambda v, lv=level: math.exp(-((v - lv) ** 2) / (2 * sigma**2))
                               / (sigma * math.sqrt(2 * math.pi)), x0, x1, 2000)
                bit_err += wrong * mass / 3
                sym_err += mass
    p = sym_err / 8
    return bit_err / 8, 2 * p - p * p


def phase_tail(psi, es_n0):
    if es_n0 == 0:
        return (math.pi - psi) / (2 * math.pi)
    g = es_n0
    root = math.sqrt(g)

    def density(phi):
        c, s = math.cos(phi), math.sin(phi)
        return (math.exp(-g) / (2 * math.pi)
                + root * c * math.exp(-g * s * s) * math.erfc(-root * c) / (2 * math.sqrt(math.pi)))

    top = min(math.pi, psi + 60 / root)
    return richardson(density, psi, top, 20000)


def psk8(eb_n0):
    es_n0 = 3 * eb_n0
    p1, p3 = phase_tail(math.pi / 8, es_n0), phase_tail(3 * math.pi / 8, es_n0)
    return (2 / 3) * (p1 + p3), 2 * p1


cases = []


def rayleigh(eb_n0):
    if eb_n0 == 0:
        return 0.5
    return 0.5 * (1 - math.sqrt(eb_n0 / (1 + eb_n0)))


def rayleigh_by_integral(eb_n0):
    root = math.sqrt(eb_n0)
    return richardson(lambda u: math.erfc(root * u) * math.exp(-u * u) * u, 0.0, 12.0, 40000)


def add(op, db, value, source, tol):
    cases.append({"id": f"{op}.{'minus_inf' if db == -math.inf else f'{db:g}db'}", "op": op,
                  "args": {"eb_n0_db": "-inf" if db == -math.inf else db},
                  "expected": value, "tol": tol, "source": source})


QAM_SRC = ("closed form (conventions: EVM and BER), erfc from Python's math module; checked "
           "against Simpson integration of the Gaussian over the 4-PAM decision intervals")
QAM64_SRC = ("closed form (conventions: EVM and BER; Cho and Yoon's square-QAM sum written out "
             "for 8-PAM), erfc from Python's math module; checked against Simpson integration "
             "of the Gaussian over the 8-PAM decision intervals")
PSK_SRC = ("the received phase's density integrated from psi to pi (Simpson, Richardson step), "
           "independent of the libraries' Pawula form; rel 1e-11 covers both integrations")
RAY_SRC = ("closed form 0.5*(1 - sqrt(g/(1+g))) by hand (conventions: EVM and BER); checked "
           "against the AWGN curve averaged over the exponential density of |g|^2 by Simpson")
for db in LEVELS:
    g = lin(db)
    ber, ser = qam16(g)
    ib, iser = qam16_by_integral(g)
    assert abs(ib / ber - 1) < 1e-10 and abs(iser / ser - 1) < 1e-10, (db, ber, ib, ser, iser)
    b64, s64 = qam64(g)
    ib64, is64 = qam64_by_integral(g)
    assert abs(ib64 / b64 - 1) < 1e-10 and abs(is64 / s64 - 1) < 1e-10, (db, b64, ib64, s64, is64)
    pb, ps = psk8(g)
    ray = rayleigh(g)
    if g:
        assert abs(rayleigh_by_integral(g) / ray - 1) < 1e-10, (db, ray, rayleigh_by_integral(g))
    if db == -math.inf:
        assert (ber, ser, pb, ps, b64, s64) == (0.5, 15 / 16, 0.5, 7 / 8, 0.5, 63 / 64)
        src = "by hand: Eb/N0 = 0 makes every decision a fair guess"
        for op, v in (("qpsk_ber_rayleigh_theory", 0.5), ("qam16_ber_theory", 0.5), ("qam16_ser_theory", 15 / 16),
                      ("psk8_ber_theory", 0.5), ("psk8_ser_theory", 7 / 8),
                      ("qam64_ber_theory", 0.5), ("qam64_ser_theory", 63 / 64)):
            add(op, db, v, src + (": 15 of 16 points wrong" if op == "qam16_ser_theory" else
                                  ": 63 of 64 points wrong" if op == "qam64_ser_theory" else
                                  ": 7 of 8 points wrong" if op == "psk8_ser_theory" else
                                  ": half the bits"), {"abs": 1e-15, "rel": 0})
        continue
    add("qpsk_ber_rayleigh_theory", db, ray, RAY_SRC, {"abs": 0, "rel": 1e-12})
    add("qam16_ber_theory", db, ber, QAM_SRC, {"abs": 0, "rel": 1e-12})
    add("qam16_ser_theory", db, ser, QAM_SRC, {"abs": 0, "rel": 1e-12})
    add("psk8_ber_theory", db, pb, PSK_SRC, {"abs": 0, "rel": 1e-11})
    add("psk8_ser_theory", db, ps, PSK_SRC, {"abs": 0, "rel": 1e-11})
    add("qam64_ber_theory", db, b64, QAM64_SRC, {"abs": 0, "rel": 1e-12})
    add("qam64_ser_theory", db, s64, QAM64_SRC, {"abs": 0, "rel": 1e-12})
for op in ("qpsk_ber_rayleigh_theory", "qam16_ber_theory", "qam16_ser_theory", "psk8_ber_theory",
           "psk8_ser_theory", "qam64_ber_theory", "qam64_ser_theory"):
    cases.append({"id": f"{op}.inf", "op": op, "args": {"eb_n0_db": "inf"}, "expected": 0.0,
                  "tol": {"abs": 0, "rel": 0}, "source": "by hand: no noise, no errors"})
    cases.append({"id": f"{op}.nan", "op": op, "args": {"eb_n0_db": "nan"},
                  "error": "invalid_argument", "source": "Eb/N0 must not be NaN"})

doc = {
    "schema": 1,
    "suite": "error_rates",
    "description": "Bit and symbol error rates of Gray 16-QAM, 64-QAM and 8-PSK in AWGN, and of QPSK in "
    "Rayleigh fading (conventions: EVM and BER).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "error_rates.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/error_rates.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
