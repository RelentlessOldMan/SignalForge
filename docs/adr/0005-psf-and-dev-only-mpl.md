# 0005: PSF-2.0 approved; MPL-2.0 allowed for development tools only; mypy added

Date: 2026-11-12. Status: accepted (approved by the user, 2026-11-12).

## Context

The license list (MIT, BSD-2, BSD-3, Apache-2.0, ISC) covers build and test tools as well as
runtime code. That kept mypy out: it needs typing_extensions (PSF-2.0) and pathspec (MPL-2.0).
The purpose of the list is that SignalForge can always ship commercially under MIT with nothing
able to force copyleft terms on it (see [0004](0004-numpy-gcc-runtime-exception.md)).

- **PSF-2.0** is the Python Software Foundation License, the license of Python itself. It is
  permissive: commercial and closed-source use allowed, with a copyright notice kept on
  redistribution and a summary of changes for modified copies. It meets the rule. It will come up
  again (matplotlib's license is PSF-based).
- **MPL-2.0** is weak, file-level copyleft: distributing MPL files obliges you to share those files'
  source and your changes to them, and nothing else. A tool that runs only on developer machines and
  in CI is never distributed by us, so the obligation never arises.

## Decision

- PSF-2.0 is approved generally, on the same footing as the allowed list.
- MPL-2.0 is allowed **only for development tools** (type checkers, linters, formatters, test
  helpers) that are never shipped, never bundled into a release, and never needed to install or run
  SignalForge. It is never allowed for runtime dependencies, build backends (they shape what is
  shipped), or code copied into the repo.
- mypy is added to the Python `dev` extra and to CI, in strict mode over `src` and `tests`.
