# ADR 0066: LMS equalizer

Status: accepted, 2026-11-13

## Context

The single-carrier chains have no equalizer, so the link rejects `multipath_delays` for them
(ADR 0064). A linear adaptive equalizer between the matched filter and the decisions is the usual
fix. The choices are the adaptation rule (LMS, normalized LMS, RLS), the tap spacing (one tap per
symbol, or fractionally spaced at two or more taps per symbol, which also absorbs a timing
offset), how it is trained (known symbols, then its own decisions), and the indexing, which two
implementations could easily define differently.

## Decision

- A standalone block in `sync`: `lms_equalizer(samples, training, num_taps, step, *,
  samples_per_symbol=1, center=None, decision=None)` (C# `Sync.LmsEqualizer`), returning
  `Equalization(symbols, errors, taps)`. The link uses it in a later slice.
- **Normalized LMS**: each update is scaled by the regressor's power, so `step` is in `[0, 2]`
  whatever the signal level (stable inside `(0, 2)`) and a scalar channel is learned in one step
  at `step = 1`. Plain LMS would need a step sized to the power; RLS costs `O(L²)` per symbol and
  is not needed yet.
- **Fractional spacing** by `samples_per_symbol`: one output per `sps` input samples, every input
  sample in the regressor. `sps = 1` is a symbol-spaced equalizer.
- Taps start as a unit impulse at `center` (default `⌊(L − 1)/2⌋`), so an equalizer with
  `step = 0` reads the input at `n·sps` and passes it through unchanged.
- **Training then decisions**: the first `len(training)` outputs adapt to the given symbols; after
  that, with `decision` one of `"qpsk"`, `"psk8"`, `"qam16"`, `"qam64"`, to the point the hard
  demapper and the mapper give for the output (the existing decisions, so both languages decide
  ties the same way); with `decision = None` the taps are held.
- The error reported per symbol is `d − y` before the update, 0 where there is no reference.

## Consequences

- No step-size schedule, leakage or constant-modulus mode. Those can come later as options.
- Output `n` starts as the input sample at `n·sps`. Aligning the training symbols with the
  channel's and filters' delay is the caller's.
- Vectors come from a stdlib generator running the same recurrence, plus cases checked against
  closed forms (pass-through, one-step scalar inversion).
