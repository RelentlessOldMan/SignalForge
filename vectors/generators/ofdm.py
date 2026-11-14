"""Writes vectors/cases/ofdm.json from first principles, using only the Python standard library.

It does not import NumPy or SignalForge, and it uses no FFT.

- ofdm_modulate: blocks written out by hand (one subcarrier, DC, Nyquist), and the definition in
  the conventions (Bits and symbols, OFDM) evaluated as a direct sum with cmath.
- ofdm_demodulate: the direct DFT sum of the samples after the cyclic prefix, and round trips,
  whose expected value is the input symbols.

Run from the repo root: python vectors/generators/ofdm.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import cmath
import json
import math
import pathlib
import sys

cases = []
TOL = {"abs": 1e-12, "rel": 1e-12}


def cx(z):
    return {"re": [complex(v).real for v in z], "im": [complex(v).imag for v in z]}


def add(cid, op, args, expected, source):
    cases.append({"id": f"{op}.{cid}", "op": op, "args": args, "expected": cx(expected),
                  "tol": TOL, "source": source})


def err(cid, op, args, source):
    cases.append({"id": f"{op}.{cid}", "op": op, "args": args, "error": "invalid_argument",
                  "source": source})


def default(n):
    return list(range(-(n // 2), n - n // 2))


def modulate(symbols, n, cp, sub):
    u, out = len(sub), []
    for b in range(len(symbols) // u):
        spec = [0j] * n
        for i, k in enumerate(sub):
            spec[k % n] = symbols[b * u + i]
        x = [sum(spec[k] * cmath.exp(2j * math.pi * k * t / n) for k in range(n)) / math.sqrt(n)
             for t in range(n)]
        out += x[n - cp:] + x
    return out


def demodulate(samples, n, cp, sub):
    out = []
    for b in range(len(samples) // (n + cp)):
        y = samples[b * (n + cp) + cp:(b + 1) * (n + cp)]
        spec = [sum(y[t] * cmath.exp(-2j * math.pi * k * t / n) for t in range(n)) / math.sqrt(n)
                for k in range(n)]
        out += [spec[k % n] for k in sub]
    return out


def symbols_of(seed, count):
    # QPSK-like points from a small LCG, with a varying amplitude so a scaling error shows
    out, x = [], seed
    for _ in range(count):
        x = (1103515245 * x + 12345) % 2**31
        q = (x >> 16) & 3
        amp = 0.5 + ((x >> 8) & 255) / 255
        out.append(amp * cmath.exp(1j * math.pi * (2 * q + 1) / 4))
    return out


# ---- ofdm_modulate, by hand
add("one_subcarrier", "ofdm_modulate",
    {"symbols": cx([1]), "nfft": 4, "cp_len": 1, "subcarriers": [1]},
    [-0.5j, 0.5, 0.5j, -0.5, -0.5j],
    "by hand: e^{j2pi n/4}/2 = [1/2, j/2, -1/2, -j/2], the last sample copied in front")
add("dc", "ofdm_modulate", {"symbols": cx([2]), "nfft": 4, "cp_len": 2, "subcarriers": [0]},
    [1] * 6, "by hand: DC symbol 2 over sqrt(4) is 1 in every sample, prefix included")
add("nyquist", "ofdm_modulate", {"symbols": cx([1j]), "nfft": 4, "cp_len": 0,
                                 "subcarriers": [-2]},
    [0.5j, -0.5j, 0.5j, -0.5j], "by hand: subcarrier -2 of 4 is bin 2, (-1)^n j/2")
add("order_of_subcarriers", "ofdm_modulate",
    {"symbols": cx([2, 0]), "nfft": 4, "cp_len": 0, "subcarriers": [0, 1]},
    [1, 1, 1, 1], "by hand: the first symbol goes on the first listed subcarrier (DC here)")
add("order_reversed", "ofdm_modulate",
    {"symbols": cx([0, 2]), "nfft": 4, "cp_len": 0, "subcarriers": [1, 0]},
    [1, 1, 1, 1], "by hand: listing the subcarriers the other way swaps which symbol is DC")
add("empty", "ofdm_modulate", {"symbols": cx([]), "nfft": 8, "cp_len": 2}, [],
    "no symbols, no blocks")

# ---- ofdm_modulate, direct sums
plans = [
    ("guarded_8", 8, 2, [-3, -2, -1, 1, 2, 3], 3, 11),
    ("full_6", 6, 0, None, 2, 12),
    ("odd_5", 5, 5, None, 2, 13),
    ("scattered_16", 16, 4, [5, -7, 1, -1, 7, 2], 2, 14),
    ("single_1", 1, 1, None, 3, 15),
]
for name, n, cp, sub, blocks, seed in plans:
    used = sub if sub is not None else default(n)
    s = symbols_of(seed, blocks * len(used))
    args = {"symbols": cx(s), "nfft": n, "cp_len": cp}
    if sub is not None:
        args["subcarriers"] = sub
    x = modulate(s, n, cp, used)
    add(name, "ofdm_modulate", args, x,
        "the definition as a direct sum: x[n] = sum X[k] e^{j2pi kn/N} / sqrt(N), prefix in front")
    dargs = {"samples": cx(x), "nfft": n, "cp_len": cp}
    if sub is not None:
        dargs["subcarriers"] = sub
    add(f"round_trip_{name}", "ofdm_demodulate", dargs, s,
        "round trip: demodulating the modulated blocks returns the symbols")

# ---- ofdm_demodulate, direct sums on samples that are not OFDM
raw = symbols_of(21, 2 * (8 + 3))
add("prefix_dropped", "ofdm_demodulate",
    {"samples": cx(raw), "nfft": 8, "cp_len": 3, "subcarriers": [-4, 3, 0, -1]},
    demodulate(raw, 8, 3, [-4, 3, 0, -1]),
    "direct DFT sum of each block's last 8 samples over sqrt(8); the 3 prefix samples are "
    "ignored even though they are not a copy")
add("all_subcarriers", "ofdm_demodulate", {"samples": cx(raw[:12]), "nfft": 6, "cp_len": 0},
    demodulate(raw[:12], 6, 0, default(6)), "direct DFT sum, subcarriers -3 ... 2 in order")

# ---- bad arguments
two = cx([1, 1])
err("cp_too_long", "ofdm_modulate", {"symbols": two, "nfft": 2, "cp_len": 3},
    "cp_len at most nfft")
err("cp_negative", "ofdm_modulate", {"symbols": two, "nfft": 2, "cp_len": -1},
    "cp_len at least 0")
err("nfft_zero", "ofdm_modulate", {"symbols": cx([]), "nfft": 0, "cp_len": 0},
    "nfft at least 1")
err("subcarrier_high", "ofdm_modulate",
    {"symbols": two, "nfft": 4, "cp_len": 0, "subcarriers": [0, 2]},
    "for N = 4 the subcarriers are -2 ... 1")
err("subcarrier_low", "ofdm_modulate",
    {"symbols": two, "nfft": 5, "cp_len": 0, "subcarriers": [0, -3]},
    "for N = 5 the subcarriers are -2 ... 2")
err("duplicate", "ofdm_modulate", {"symbols": two, "nfft": 4, "cp_len": 0, "subcarriers": [1, 1]},
    "subcarriers must be distinct")
err("no_subcarriers", "ofdm_modulate", {"symbols": cx([]), "nfft": 4, "cp_len": 0,
                                        "subcarriers": []}, "at least one subcarrier")
err("partial_block", "ofdm_modulate", {"symbols": cx([1, 1, 1]), "nfft": 4, "cp_len": 0,
                                       "subcarriers": [0, 1]}, "3 symbols do not fill blocks of 2")
err("nan_symbol", "ofdm_modulate",
    {"symbols": {"re": [1, "nan"], "im": [0, 0]}, "nfft": 2, "cp_len": 0},
    "symbols must be finite")
err("partial_samples", "ofdm_demodulate", {"samples": cx([1] * 9), "nfft": 4, "cp_len": 1},
    "9 samples are not a whole number of blocks of 5")
err("inf_sample", "ofdm_demodulate",
    {"samples": {"re": [1, 0, 0, 0], "im": [0, "inf", 0, 0]}, "nfft": 4, "cp_len": 0},
    "samples must be finite")
err("demod_bad_subcarrier", "ofdm_demodulate",
    {"samples": cx([1] * 4), "nfft": 4, "cp_len": 0, "subcarriers": [4]},
    "for N = 4 the subcarriers are -2 ... 1")

doc = {
    "schema": 1,
    "suite": "ofdm",
    "description": "OFDM modulate and demodulate: unitary DFT, signed subcarriers, cyclic prefix "
    "(conventions: Bits and symbols, OFDM).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "ofdm.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/ofdm.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
