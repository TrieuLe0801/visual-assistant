# ADR 0011 — Require Python 3.11 for patched Pillow

Date: 2026-11-10
Status: Accepted
Amends: ADR 0001 and ADR 0010

## Context

The previous project range allowed Python 3.10 and selected Pillow 12.3.0 for
that interpreter. The security audit found 39 published advisories for this
version; the reported fix is Pillow 13.0.0. Pillow 13 dropped Python 3.10
support after Python 3.10 reached end of life. Keeping the old interpreter
would keep a vulnerable dependency in a supported configuration.

## Decision

- Require Python 3.11 or newer in project metadata and development instructions.
  Set `.python-version` to 3.11.
- Require Pillow 13.0.0 or newer without a Python-version branch. Regenerate
  `uv.lock`; remove Pillow 12.3.0 from the active dependency graph.
- Set Black and Ruff targets to Python 3.11. Keep the Docker runtime on Python
  3.11 and Pillow 13.
- Treat the old Python 3.10 baseline and security-audit scan as historical
  evidence, not a supported development or deployment target.

## Consequences

- `uv sync` requires a Python 3.11+ interpreter. Attempting to run the project
  with Python 3.10 fails before installing or importing Pillow.
- Hosts still using Python 3.10 must install a supported Python version before
  running this project. Existing SQLite and image files do not need migration.
- Revisit the lower bound only if a supported, patched Pillow release for
  Python 3.10 becomes available and the project explicitly restores support.

## Evidence

- [Pillow 13 release notes](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html)
  state that Python 3.10 support was dropped.
- [Pillow Python support matrix](https://pillow.readthedocs.io/en/stable/installation/python-support.html)
  lists Pillow 13 for Python 3.11+.
- The current lockfile and audit results are recorded in the current learning
  log and security audit report.
