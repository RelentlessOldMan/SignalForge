# ADR 0623: In-order sums without a Python loop

Status: accepted, 2026-11-26.

## Context

The C# library adds its sums one value at a time, first to last. The Python functions of ADRs
0607–0620 copied that with a Python `for` loop per value, so the two languages round the same
way. The loop cost about 0.08–0.23 s per 5e5 values. `np.sum` would be fast but adds pairwise,
which rounds differently: on 5000 values of mixed size, a probe gave a different last bit.

## Decision

- A private helper `measurements._ordered_sum(t)` returns `np.cumsum(t, out=t)[-1]`, or 0
  for an empty array. NumPy's cumulative sum adds strictly in order, so the result is the
  loop's sum bit for bit. A probe over 160 arrays of up to 2e5 values, spread across about 26
  decades and including strided and Fortran-ordered views, found no difference. The helper
  overwrites `t` with its running sums, so callers pass an array they own: a fresh product
  or quotient, or a `.copy()`.
- Each term is formed by the same NumPy element-wise operations as the loop's scalar ones
  (`a / top`, `q * q`, `(a - 1.0) / top`), so each term rounds the same way too.
- It replaces the loops in `strauss_selection`, the shared count sums of Lloyd's, Green's,
  Morisita's, David and Moore's, Cassie's and Fisher's indices (`_count_pairs`,
  `_count_spread`), the Clark–Evans mean, Hopkins' statistic, Pielou's index and Eberhardt's
  index. Johnson's rank preference index had no such loop.

## Consequences

- Before and after gave identical results, compared bit for bit: 780 results and error
  messages over 60 random inputs of up to 3000 values. On 5e5 values, `green_index` went
  from 0.156 s to 0.012 s, `eberhardt_index` from 0.076 s to 0.008 s, and
  `strauss_selection` from 0.231 s to 0.017 s.
- Each sum holds one extra array of the input's size while it runs.
- `python/tests/test_ordered_sums.py` traces the Python lines each of the 14 functions runs
  in `measurements` and requires the count to be the same for 8 values as for 800. 13 of
  the 14 failed before the change. It also checks `_ordered_sum` against a hand loop, and
  Eberhardt's index against the loop form, on data where pairwise summation rounds
  differently. Mutations were checked: `np.sum` in place of `np.cumsum` failed 2 tests, and
  a loop put back into Hopkins' statistic failed 1.
- About 76 more loops of the same kind remain in older `measurements` functions (and one in
  `dsp`); `docs/status.md` lists them as a lead.
