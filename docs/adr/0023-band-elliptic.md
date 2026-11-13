# 0023: Band-pass and band-stop elliptic

Date: 2026-11-13. Status: accepted.

## Context

ADR 0022 gave the elliptic low-pass prototype: a real pole for an odd order, pole pairs with
finite zeros `±jΩ_i`, and the type I gain `10^(−R/20)` for an even order. ADR 0021 already
transforms a prototype with exactly these parts to a band: the real pole and the even-order gain
as for type I, finite zeros as for type II.

## Decision

- **`elliptic_bandpass` and `elliptic_bandstop`** take `order, ripple_db, attenuation_db, low,
  high, sample_rate`, with `low` and `high` the pass-band edges, as the type I band designs do.
- **The ADR 0021 band builder, unchanged**: the elliptic poles and zeros are passed in; the real
  pole section gets `−p_r` (band-pass), each pair section `|p_i|/Ω_i` (band-pass), band-stop
  sections 1, and an even order's `10^(−R/20)` goes on the first section. The zero images are
  assigned to sections as for type II.
- Validation is the elliptic low-pass's plus the band's (`0 < low < high < fs/2`).
- Implemented from the definitions; no third-party code.

## Consequences

- `|H|²` has the closed form `1/(1 + ε_p²R_N(|x|)²)` in `tan(πf/fs)`; the generator checks its
  rows against it with R_N computed from theta series, independent of the library's Landen
  ladder, and checks the denominator product by polynomial substitution.
- No new numerical machinery: the elliptic prototype and the band transform are each already
  tested and cross-checked.
