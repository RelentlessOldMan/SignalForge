"""Writes vectors/cases/fsk.json from first principles, using only the Python standard library.

It does not import NumPy or SignalForge.

- fsk_modulate: the phase definition in the conventions (Bits and symbols, FSK), evaluated with
  cmath; one case is also written out by hand.
- fsk_demod_noncoherent: noiseless waveforms decide the bits they carry (the expected value is
  the input, not a detector's output), and hand-built blocks (two tones of different amplitude,
  zeros) decide the label worked out by hand.
- fsk_ser_theory and fsk_ber_theory: the closed form in the conventions, each value checked
  against a numerical integral of the square-law detector: with the noise of one correlator
  normalized to unit variance per dimension, the right correlator's amplitude is Rician with
  nu = sqrt(2 Es/N0), each wrong one Rayleigh, and
  Ps = integral over r of r exp(-(r^2 + nu^2)/2) I0(nu r) (1 - (1 - exp(-r^2/2))^(M-1)) dr.
  I0 comes from its power series (or its asymptotic series for large arguments), the integral
  from Simpson's rule, so nothing is shared with the alternating binomial sum.

Run from the repo root: python vectors/generators/fsk.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import cmath
import json
import math
import pathlib
import sys

cases = []
BITS = {2: 1, 4: 2, 8: 3, 16: 4}


def labels(bits, k):
    return [int("".join(map(str, bits[i : i + k])), 2) for i in range(0, len(bits), k)]


def modulate(bits, order, sps, h):
    out, start = [], 0
    for m in labels(bits, BITS[order]):
        a = 2 * m - (order - 1)
        out += [cmath.exp(1j * (math.pi * h * (start + (a * n) / sps))) for n in range(sps)]
        start += a
    return out


def cx(z):
    return {"re": [v.real for v in z], "im": [v.imag for v in z]}


def bits_of(seed, n):
    # a small LCG, only to spread the labels around
    out, x = [], seed
    for _ in range(n):
        x = (1103515245 * x + 12345) % 2**31
        out.append((x >> 16) & 1)
    return out


def add(cid, op, args, expected, source, tol=None):
    c = {"id": cid, "op": op, "args": args, "expected": expected}
    if tol is not None:
        c["tol"] = tol
    c["source"] = source
    cases.append(c)


def err(cid, op, args, source):
    cases.append({"id": cid, "op": op, "args": args, "error": "invalid_argument", "source": source})


# ---- fsk_modulate
r = math.sqrt(0.5)
hand = [1, complex(r, -r), -1j, complex(-r, -r), -1, complex(-r, -r), -1j, complex(r, -r)]
assert max(abs(a - b) for a, b in zip(hand, modulate([0, 1], 2, 4, 1.0))) < 1e-15
add("fsk_modulate.binary_by_hand", "fsk_modulate",
    {"bits": [0, 1], "order": 2, "samples_per_symbol": 4, "modulation_index": 1.0}, cx(hand),
    "by hand: bit 0 is level -1, so the phase falls by pi/4 a sample from 0 to -3pi/4; bit 1 "
    "starts at -pi (no jump) and rises by pi/4 a sample: e^{-j pi n/4}, then -e^{j pi n/4}",
    {"abs": 1e-15, "rel": 0})
MOD_SRC = "the phase definition in the conventions (Bits and symbols, FSK), evaluated with cmath"
for order, sps, h, n in ((4, 8, 1.0, 24), (8, 16, 1.0, 30), (16, 4, 0.5, 32), (2, 3, 0.5, 9)):
    b = bits_of(order * 7 + sps, n)
    add(f"fsk_modulate.m{order}_sps{sps}_h{h:g}", "fsk_modulate",
        {"bits": b, "order": order, "samples_per_symbol": sps, "modulation_index": h},
        cx(modulate(b, order, sps, h)), MOD_SRC, {"abs": 1e-12, "rel": 0})
add("fsk_modulate.empty", "fsk_modulate",
    {"bits": [], "order": 4, "samples_per_symbol": 8, "modulation_index": 1.0},
    {"re": [], "im": []}, "by hand: no bits, no samples")
err("fsk_modulate.order_3", "fsk_modulate",
    {"bits": [0, 1], "order": 3, "samples_per_symbol": 8, "modulation_index": 1.0}, "order must be 2, 4, 8 or 16")
err("fsk_modulate.odd_bits", "fsk_modulate",
    {"bits": [0, 1, 1], "order": 4, "samples_per_symbol": 8, "modulation_index": 1.0}, "4-FSK needs bit pairs")
err("fsk_modulate.sps_0", "fsk_modulate",
    {"bits": [0], "order": 2, "samples_per_symbol": 0, "modulation_index": 1.0}, "samples_per_symbol must be at least 1")
err("fsk_modulate.h_0", "fsk_modulate",
    {"bits": [0], "order": 2, "samples_per_symbol": 8, "modulation_index": 0.0}, "modulation_index must be positive")
err("fsk_modulate.h_nan", "fsk_modulate",
    {"bits": [0], "order": 2, "samples_per_symbol": 8, "modulation_index": "nan"}, "modulation_index must be finite")
err("fsk_modulate.bit_2", "fsk_modulate",
    {"bits": [0, 2], "order": 2, "samples_per_symbol": 8, "modulation_index": 1.0}, "bits must be 0 or 1")

# ---- fsk_demod_noncoherent
for order, sps, h, n in ((2, 4, 1.0, 16), (4, 8, 1.0, 24), (8, 16, 1.0, 30), (16, 32, 1.0, 32), (4, 16, 2.0, 24)):
    b = bits_of(order * 11 + sps, n)
    add(f"fsk_demod_noncoherent.noiseless_m{order}_h{h:g}", "fsk_demod_noncoherent",
        {"samples": cx(modulate(b, order, sps, h)), "order": order, "samples_per_symbol": sps,
         "modulation_index": h}, b,
        "the bits that were modulated: with orthogonal tones only the sent label's correlator "
        "sees energy (sps*sps against about 0)")


def tone(order, sps, h, m, amp, phase):
    a = 2 * m - (order - 1)
    return [amp * cmath.exp(1j * (math.pi * h * a * n / sps + phase)) for n in range(sps)]


two = [x + y for x, y in zip(tone(4, 8, 1.0, 2, 1.0, 0.3), tone(4, 8, 1.0, 0, 0.5, -1.0))]
add("fsk_demod_noncoherent.two_tones_by_hand", "fsk_demod_noncoherent",
    {"samples": cx(two + [0j] * 8), "order": 4, "samples_per_symbol": 8, "modulation_index": 1.0},
    [1, 0, 0, 0],
    "by hand: tones are orthogonal over 8 samples, so label 2 (amplitude 1) has energy 64 and "
    "label 0 (amplitude 0.5) 16: decides 10; the zero block ties at 0 and decides label 0, 00")
err("fsk_demod_noncoherent.length", "fsk_demod_noncoherent",
    {"samples": cx([1, 1, 1]), "order": 2, "samples_per_symbol": 2, "modulation_index": 1.0},
    "samples must be a multiple of samples_per_symbol")
err("fsk_demod_noncoherent.nan", "fsk_demod_noncoherent",
    {"samples": {"re": [1.0, "nan"], "im": [0.0, 0.0]}, "order": 2, "samples_per_symbol": 2,
     "modulation_index": 1.0}, "samples must be finite")
err("fsk_demod_noncoherent.order_32", "fsk_demod_noncoherent",
    {"samples": cx([1, 1]), "order": 32, "samples_per_symbol": 2, "modulation_index": 1.0},
    "order must be 2, 4, 8 or 16")


# ---- theory
def closed(es, order):
    total, c = 0.0, 1.0
    for k in range(1, order):
        c = c * (order - k) / k
        term = c / (k + 1) * math.exp(-k * es / (k + 1))
        total = total + term if k % 2 else total - term
    return total


def i0e(x):
    """I0(x) e^-x: power series below 40, the asymptotic series above."""
    if x < 40:
        term, total, q, k = 1.0, 1.0, x * x / 4, 0
        while term > 1e-18 * total:
            k += 1
            term *= q / (k * k)
            total += term
        return total * math.exp(-x)
    term, total, k = 1.0, 1.0, 0
    while True:
        k += 1
        nxt = term * (2 * k - 1) ** 2 / (k * 8 * x)
        if nxt < 1e-17 or nxt > term:
            break
        term = nxt
        total += term
    return total / math.sqrt(2 * math.pi * x)


def by_integral(es, order):
    nu = math.sqrt(2 * es)
    top = nu + 14.0
    n = 6000

    def f(r):
        if r == 0:
            return 0.0
        u = math.exp(-r * r / 2)
        wrong = -math.expm1((order - 1) * math.log1p(-u)) if u < 1 else 1.0
        return r * math.exp(-(r - nu) ** 2 / 2) * i0e(nu * r) * wrong

    hstep = top / n
    s = f(0.0) + f(top) + sum((4 if i % 2 else 2) * f(i * hstep) for i in range(1, n))
    return s * hstep / 3


SRC = ("closed form (conventions: EVM and BER, noncoherent orthogonal FSK; Proakis), checked "
       "against the square-law detector's error integral over the Rician and Rayleigh densities "
       "(Simpson, I0 by its series) to 1e-9")
for order in (2, 4, 8, 16):
    for db in (-5.0, 0.0, 4.0, 8.0, 12.0):
        if order >= 8 and db == 12.0:
            continue
        es = BITS[order] * 10 ** (db / 10)
        ps = closed(es, order)
        chk = by_integral(es, order)
        assert abs(chk / ps - 1) < 1e-9, (order, db, ps, chk)
        if order == 2:
            assert abs(ps / (0.5 * math.exp(-es / 2)) - 1) < 1e-15
        pb = ps * (order / 2) / (order - 1)
        tol = {"abs": 0, "rel": 1e-12}
        for op, v in (("fsk_ser_theory", ps), ("fsk_ber_theory", pb)):
            add(f"{op}.m{order}_{db:g}db", op, {"eb_n0_db": db, "order": order}, v,
                "by hand: 0.5*exp(-Eb/2N0); " + SRC if order == 2 else SRC, tol)
add("fsk_ber_theory.default_order", "fsk_ber_theory", {"eb_n0_db": 10.0}, 0.5 * math.exp(-5.0),
    "by hand: order 2 by default, 0.5*exp(-10/2)", {"abs": 0, "rel": 1e-14})
for order in (2, 4, 8, 16):
    add(f"fsk_ser_theory.m{order}_minus_inf", "fsk_ser_theory", {"eb_n0_db": "-inf", "order": order},
        1 - 1 / order, f"by hand: Eb/N0 = 0 makes the decision a fair guess, {order - 1} of {order} labels wrong",
        {"abs": 1e-13, "rel": 0})
    add(f"fsk_ber_theory.m{order}_minus_inf", "fsk_ber_theory", {"eb_n0_db": "-inf", "order": order},
        0.5, "by hand: a fair guess gets half the bits wrong", {"abs": 1e-13, "rel": 0})
    add(f"fsk_ber_theory.m{order}_inf", "fsk_ber_theory", {"eb_n0_db": "inf", "order": order}, 0.0,
        "by hand: no noise, no errors", {"abs": 0, "rel": 0})
for op in ("fsk_ser_theory", "fsk_ber_theory"):
    err(f"{op}.nan", op, {"eb_n0_db": "nan", "order": 4}, "Eb/N0 must not be NaN")
    err(f"{op}.order_32", op, {"eb_n0_db": 4.0, "order": 32}, "order must be 2, 4, 8 or 16")
    err(f"{op}.order_6", op, {"eb_n0_db": 4.0, "order": 6}, "order must be 2, 4, 8 or 16")

doc = {
    "schema": 1,
    "suite": "fsk",
    "description": "Continuous-phase M-FSK, its noncoherent detector, and noncoherent orthogonal "
    "FSK error rates (conventions: Bits and symbols, FSK; EVM and BER).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "fsk.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/fsk.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
