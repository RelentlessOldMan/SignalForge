"""Writes vectors/cases/gcc_phat.json, stdlib only.

GCC-PHAT delay (conventions: GCC-PHAT delay; ADR 0191): pad to L = N + M - 1, W = G/|G| for
G = X conj Y (0 where G = 0), r = Re ifft(W), lag i for i < N else i - L. For impulses
x = a delta[n-p], y = b delta[n-q] (a, b > 0), W = e^{-j w (p-q)} exactly, so r is 1 at lag
p - q and 0 elsewhere: delay (p - q)/fs, lag p - q, peak 1. For y = x, W = 1 wherever X != 0.

Run from the repo root: python vectors/generators/gcc_phat.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def impulse(length, at, scale=1.0):
    return [scale if i == at else 0.0 for i in range(length)]


def add(cid, x, y, fs, delay, lag, peak, why, max_delay=None):
    args = {"x": x, "y": y, "sample_rate": fs}
    if max_delay is not None:
        args["max_delay"] = max_delay
    cases.append({"id": f"gcc_phat.{cid}", "op": "gcc_phat", "args": args,
                  "expected": {"delay": delay, "lag": lag, "peak": peak}, "tol": TOL,
                  "source": why})


add("positive", impulse(8, 3, 2.0), impulse(3, 0), 1000.0, 0.003, 3, 1.0,
    "x = 2 delta[n-3], y = delta[n]: W = e^{-3jw}, r = delta at lag 3; neighbours 0 so the "
    "parabola gives 0")
add("negative", impulse(4, 0), impulse(5, 2, 0.5), 100.0, -0.02, -2, 1.0,
    "x = delta[n], y = 0.5 delta[n-2]: x is earlier, lag -2 (index L - 2 of L = 8)")
add("zero", impulse(6, 4), impulse(6, 4, 3.0), 48000.0, 0.0, 0, 1.0,
    "both at n = 4: W = 1, r = delta at lag 0")
add("edge", impulse(5, 4), impulse(1, 0), 10.0, 0.4, 4, 1.0,
    "x = delta[n-4], y = delta[n]: lag 4 is the last searched, so no parabola")
add("windowed", impulse(10, 6), impulse(10, 1), 1.0, 5.0, 5, 1.0,
    "lag 5, max_delay 5 s at 1 Hz: lags -5..5 still hold the peak, now at the edge", max_delay=5.0)
add("same_signal", [1.0, 2.0], [1.0, 2.0], 1.0, 0.0, 0, 1.0,
    "y = x = [1, 2], L = 3: X_k = 1 + 2 e^{-2 pi j k/3} != 0, so W = 1 and r = delta at lag 0")
add("zero_bin_tie", [1.0, 1.0], [1.0], 1.0, 0.0, 0, 0.5,
    "x = [1, 1], y = [1], L = 2: G = [2, 0], W = [1, 0], r = [1/2, 1/2] at lags 0 and 1: the "
    "tie goes to lag 0; lag -1 is not searched (M - 1 = 0), so no parabola")


def err(cid, x, y, fs, why, max_delay=None):
    args = {"x": x, "y": y, "sample_rate": fs}
    if max_delay is not None:
        args["max_delay"] = max_delay
    cases.append({"id": f"gcc_phat.{cid}", "op": "gcc_phat", "args": args,
                  "error": "invalid_argument", "source": why})


err("silent_x", [0.0, 0.0], [1.0], 1.0, "x all zero")
err("silent_y", [1.0], [0.0, 0.0], 1.0, "y all zero")
err("empty", [], [1.0], 1.0, "x empty")
err("zero_rate", [1.0], [1.0], 0.0, "sample_rate must be positive")
err("negative_window", [1.0, 0.0], [1.0], 1.0, "max_delay must be at least 0", max_delay=-1.0)
err("nan", [1.0, "nan"], [1.0], 1.0, "not finite")

doc = {
    "schema": 1,
    "suite": "gcc_phat",
    "description": "GCC-PHAT delay (conventions: GCC-PHAT delay; ADR 0191).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "gcc_phat.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/gcc_phat.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
