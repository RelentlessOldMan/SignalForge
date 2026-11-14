# ADR 0061: SigMF annotations

Status: accepted, 2026-11-13

## Context

A SigMF recording's `annotations` array marks spans of samples (a burst, a packet, a label from a
detector): each is an object with `core:sample_start`, usually `core:sample_count`, and any other
fields, such as `core:label`, `core:comment` or `core:freq_lower_edge`. SignalForge wrote an empty
array and ignored the one it read, so a labelled recording lost its labels in a round trip.
Annotations are data about the samples, not about how to decode them, so they fit the Signal's
metadata; the choice is where they live there and how strictly they are checked.

## Decision

- Annotations are the metadata key `core:annotations`: a list of JSON objects, in the order of the
  file. Writing puts the list in the top-level `annotations` array, not in `global`; reading puts
  a non-empty array under that key. An empty or missing array gives no key, so a Signal without
  annotations reads back with the metadata it was written with.
- Each annotation must have `core:sample_start`, an integer ≥ 0 (a bool or `2.0` is not one), and
  may have `core:sample_count`, an integer ≥ 0. Every other field is kept as it is, with the
  JSON limits of the rest of the metadata. The list must be sorted by `core:sample_start` (ties in
  any order), as SigMF asks; an unsorted list is rejected, not sorted, both ways.
- Not checked: whether an annotation runs past the end of the samples (a recording may be cut
  short and keep its labels), and what `core:label` or the frequency edges hold.
- `annotations: null` is rejected, as `captures: null` is. A global field named
  `core:annotations` is rejected on reading, since it would collide with the key.

## Consequences

- A labelled recording keeps its labels through SignalForge in both languages, and the two
  languages exchange them.
- Operations that change the samples (slicing, resampling) do not move annotations; they keep the
  metadata as it is. Re-indexing annotations is for a later slice if it is needed.
