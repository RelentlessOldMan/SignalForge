"""Writes vectors/cases/lempel_ziv_complexity.json, stdlib only.

Lempel-Ziv complexity (conventions: Lempel-Ziv complexity; ADR 0336): the LZ76 parse by its
definition, with string searches: each phrase s[p..q] has the smallest q such that s[p..q] is
not a substring of s[0..q-1]; a piece still copyable at the end counts as one more phrase.

Run from the repo root: python vectors/generators/lempel_ziv_complexity.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys

cases = []


def lz76(s):
    n, p, phrases = len(s), 0, 0
    while p < n:
        q = p
        while q < n and s[p:q + 1] in s[:q]:
            q += 1
        phrases += 1
        p = q + 1
    return phrases


def add(cid, text, why):
    c = lz76(text)
    cases.append({"id": f"lempel_ziv_complexity.{cid}", "op": "lempel_ziv_complexity",
                  "args": {"bits": [int(ch) for ch in text]}, "expected": c, "source": why})
    return c


c = add("lempel_ziv", "0001101001000101", "Lempel and Ziv's example: 0 . 001 . 10 . 100 . "
        "1000 . 101")
assert c == 6, c
assert add("one", "1", "a single bit is one phrase") == 1
assert add("zeros", "0" * 20, "all zeros: 0 . then a copy of the rest") == 2
assert add("alternating", "01" * 10, "0 . 1 . then a copy") == 3
add("ones_then_zeros", "1" * 7 + "0" * 9, "a run of ones, then of zeros")
rng = random.Random(336)
add("pseudo_random", "".join(rng.choice("01") for _ in range(200)), "200 bits from Python's "
    "random.Random(336)")
reg = [1] * 7
for _ in range(120):
    reg.append(reg[-7] ^ reg[-6])
add("recurrence", "".join(str(v) for v in reg[7:]), "120 bits of b[n] = b[n-7] xor b[n-6] "
    "from all ones")


def err(cid, why, bits):
    cases.append({"id": f"lempel_ziv_complexity.{cid}", "op": "lempel_ziv_complexity",
                  "args": {"bits": bits}, "error": "invalid_argument", "source": why})


err("empty", "at least one bit", [])
err("two", "bits must be 0 or 1", [0, 1, 2])

doc = {
    "schema": 1,
    "suite": "lempel_ziv_complexity",
    "description": "Lempel-Ziv complexity (conventions: Lempel-Ziv complexity; ADR 0336).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "lempel_ziv_complexity.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/lempel_ziv_complexity.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
