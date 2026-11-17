"""Writes vectors/cases/coherence_threshold.json, stdlib only.

Coherence significance threshold (conventions: Coherence threshold; ADR 0199):
1 - alpha^(1/(K-1)) for K independent segments. Expected values are closed forms worked in each
source, each checked here against math.pow.

Run from the repo root: python vectors/generators/coherence_threshold.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def add(cid, k, alpha, value, why):
    assert abs(value - (1 - math.pow(alpha, 1 / (k - 1)))) < 1e-15, cid
    args = {"num_segments": k}
    if alpha != 0.05 or cid == "two_segments":
        args["alpha"] = alpha
    cases.append({"id": f"coherence_threshold.{cid}", "op": "coherence_threshold", "args": args,
                  "expected": value, "tol": TOL, "source": why})


add("two_segments", 2, 0.05, 0.95, "K = 2: 1 - 0.05^1 = 0.95")
add("default_alpha", 2, 0.05, 0.95, "alpha defaults to 0.05; K = 2: 0.95")
add("three_segments", 3, 0.01, 0.9, "K = 3, alpha = 0.01: 1 - sqrt(0.01) = 0.9")
add("fourth_root", 5, 0.5, 1 - 2 ** -0.25, "K = 5, alpha = 0.5: 1 - 0.5^(1/4) = 1 - 2^(-1/4)")
add("eleven", 11, 0.05, 1 - math.exp(math.log(0.05) / 10),
    "K = 11, alpha = 0.05: 1 - 0.05^(1/10) = 1 - e^(ln 0.05 / 10) = 0.25886...")


def err(cid, why, **args):
    cases.append({"id": f"coherence_threshold.{cid}", "op": "coherence_threshold", "args": args,
                  "error": "invalid_argument", "source": why})


err("one_segment", "num_segments must be at least 2", num_segments=1)
err("zero_segments", "num_segments must be at least 2", num_segments=0)
err("alpha_zero", "alpha must be strictly between 0 and 1", num_segments=4, alpha=0.0)
err("alpha_one", "alpha must be strictly between 0 and 1", num_segments=4, alpha=1.0)
err("alpha_nan", "alpha must be finite", num_segments=4, alpha="nan")

doc = {
    "schema": 1,
    "suite": "coherence_threshold",
    "description": "Coherence significance threshold (conventions: Coherence threshold; ADR 0199).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "coherence_threshold.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/coherence_threshold.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
