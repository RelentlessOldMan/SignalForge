# ADR 0282: Shelving and peaking EQ sections

Status: accepted, 2026-11-17.

## Context

A parametric equaliser is built from three kinds of second-order section:
- a low shelf, which sets the gain below a corner;
- a high shelf, which sets the gain above one;
- a peaking section, which boosts or cuts a band around a centre and leaves both ends at unity.

Each one is the bilinear transform of a short analogue prototype, prewarped to its frequency.
The closed forms are the ones Robert Bristow-Johnson published. They are derived here from the
prototypes, not copied. They return the second-order sections of the IIR conventions, so
`IirFilter`, `sos_response` and the rest take them as they are.

## Decision

- **The API.**
  - Python: `low_shelf`, `high_shelf` and `peaking_eq`, each
    `(frequency, gain_db, q, sample_rate)`, in `dsp`.
  - C#: `Dsp.LowShelf`, `Dsp.HighShelf` and `Dsp.PeakingEq` with the same parameters.
  - Each returns one section, shape `(1, 6)` (C#: `double[1][6]`), with `a0 = 1`.
- **The quantities.**
  - `A = 10^(gain_db/40)`, so the shelf or peak gain is `A² = 10^(gain_db/20)`.
  - `w0 = (2π·frequency)/fs`, `c = cos w0`, `α = sin(w0)/(2q)`, `√A`.
- **The prototypes**, with `s = j` at `w0`:
  - peaking: `(s² + (A/q)·s + 1)/(s² + s/(A·q) + 1)`;
  - low shelf: `A·(s² + (√A/q)·s + A)/(A·s² + (√A/q)·s + 1)`;
  - high shelf: `A·(A·s² + (√A/q)·s + 1)/(s² + (√A/q)·s + A)`.
- **The coefficients.** Each is computed as below, then divided by `a0`.
  - Peaking:
    - `b = [1 + α·A, −2c, 1 − α·A]`;
    - `a = [1 + α/A, −2c, 1 − α/A]`.
  - Low shelf:
    - `b0 = A·((A + 1) − (A − 1)·c + 2√A·α)`;
    - `b1 = 2A·((A − 1) − (A + 1)·c)`;
    - `b2 = A·((A + 1) − (A − 1)·c − 2√A·α)`;
    - `a0 = (A + 1) + (A − 1)·c + 2√A·α`;
    - `a1 = −2·((A − 1) + (A + 1)·c)`;
    - `a2 = (A + 1) + (A − 1)·c − 2√A·α`.
  - High shelf:
    - `b0 = A·((A + 1) + (A − 1)·c + 2√A·α)`;
    - `b1 = −2A·((A − 1) + (A + 1)·c)`;
    - `b2 = A·((A + 1) + (A − 1)·c − 2√A·α)`;
    - `a0 = (A + 1) − (A − 1)·c + 2√A·α`;
    - `a1 = 2·((A − 1) − (A + 1)·c)`;
    - `a2 = (A + 1) − (A − 1)·c − 2√A·α`.
- **The gains.**
  - Low shelf: `A²` at DC and 1 at fs/2.
  - High shelf: 1 at DC and `A²` at fs/2.
  - Peaking: 1 at both ends and `A²` at `w0`.
  - `gain_db = 0` is unity everywhere.
- **The rules.**
  - `0 < frequency < fs/2` and `q > 0`, finite.
  - `gain_db` and `fs` must be finite, with `fs > 0`.
  - A section that rounds to a pole on the unit circle is rejected, as the other IIR designs do.

## Consequences

- **Vectors.**
  - Expected values come from the bilinear transform of the prototypes. It is done in exact
    rationals at the float `tan(w0/2)`, `A` and `√A`, which is a different route from the
    sin/cos closed forms above.
  - The generator checks the DC and fs/2 gains exactly.
  - The tolerance is `abs 1e-13, rel 1e-12`.
