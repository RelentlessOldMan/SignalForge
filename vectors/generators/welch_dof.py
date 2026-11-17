"""Writes vectors/cases/welch_dof.json, stdlib only.

Welch equivalent degrees of freedom (conventions: Welch degrees of freedom; ADR 0200):
nu = 2K / (1 + 2 sum_{l=1}^{K-1} (1 - l/K) rho(l)^2), rho(l) = sum w[n] w[n + l S] / sum w^2.
Expected values are exact fractions worked in each source, each checked here against a direct
evaluation with the periodic window written out by hand.

Run from the repo root: python vectors/generators/welch_dof.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-13, "rel": 1e-13}
cases = []
WINDOWS = {
    "rectangular": lambda n: [1.0] * n,
    "hann": lambda n: [0.5 - 0.5 * math.cos(2 * math.pi * i / n) for i in range(n)],
}


def direct(w, step, k):
    n, e = len(w), sum(v * v for v in w)
    total = 0.0
    for lag in range(1, k):
        s = lag * step
        if s >= n:
            break
        rho = sum(w[i] * w[i + s] for i in range(n - s)) / e
        total += (1 - lag / k) * rho * rho
    return 2 * k / (1 + 2 * total)


def add(cid, nperseg, noverlap, k, window, value, why):
    assert abs(direct(WINDOWS[window](nperseg), nperseg - noverlap, k) - value) < 1e-14, cid
    args = {"nperseg": nperseg, "noverlap": noverlap, "num_segments": k}
    if window != "hann":
        args["window"] = window
    cases.append({"id": f"welch_dof.{cid}", "op": "welch_dof", "args": args, "expected": value,
                  "tol": TOL, "source": why})


add("no_overlap", 8, 0, 5, "rectangular", 10.0, "no overlap: rho = 0, nu = 2K = 10")
add("rect_half", 4, 2, 3, "rectangular", 4.5,
    "rectangular, step 2 of 4: rho(1) = 2/4, rho(2) = 0; nu = 6 / (1 + 2 (2/3) (1/4)) = 6 / (4/3)")
add("rect_three_quarters", 4, 3, 4, "rectangular", 64 / 17,
    "rectangular, step 1 of 4: rho = 3/4, 2/4, 1/4; sum (1 - l/4) rho^2 = 27/64 + 8/64 + 1/64 = "
    "9/16; nu = 8 / (1 + 9/8) = 64/17")
add("hann_half", 4, 2, 3, "hann", 81 / 14,
    "periodic Hann N = 4: w = [0, 1/2, 1, 1/2], sum w^2 = 3/2; step 2: rho(1) = (0 + 1/4) / (3/2) "
    "= 1/6; nu = 6 / (1 + 2 (2/3) / 36) = 6 / (28/27) = 81/14")
add("one_segment", 16, 8, 1, "hann", 2.0, "K = 1: the sum is empty, nu = 2")
add("hann_no_overlap", 4, 0, 6, "hann", 12.0, "no overlap: rho = 0, nu = 2K = 12")


def err(cid, why, **args):
    cases.append({"id": f"welch_dof.{cid}", "op": "welch_dof", "args": args,
                  "error": "invalid_argument", "source": why})


err("zero_length", "nperseg must be at least 1", nperseg=0, noverlap=0, num_segments=2)
err("overlap_too_big", "noverlap must be below nperseg", nperseg=4, noverlap=4, num_segments=2)
err("negative_overlap", "noverlap must be at least 0", nperseg=4, noverlap=-1, num_segments=2)
err("zero_segments", "num_segments must be at least 1", nperseg=4, noverlap=2, num_segments=0)

doc = {
    "schema": 1,
    "suite": "welch_dof",
    "description": "Welch equivalent degrees of freedom (conventions: Welch degrees of freedom; "
    "ADR 0200).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "welch_dof.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/welch_dof.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
