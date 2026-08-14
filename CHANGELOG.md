# PreflightQC — Changelog

The product version has a single authoritative source: `preflightqc.__version__`
(`src/preflightqc/__init__.py`). Everything customer-facing derives from it.

## 1.0.0 — identity frozen 2026-08-09, validated 2026-08-14, NOT YET RELEASED

Release identity frozen by Product Owner decision: **PreflightQC 1.0.0**, publisher
**ITISYOU**, **Windows x64**, **Policy U — intentionally unsigned**
(`docs/licensing/UNSIGNED-RELEASE-POLICY-V1.md`).

First commercial release of PreflightQC: offline technical QC for video deliverables.
Inspect → validate → explain → report against 12 shipped platform presets (170
traceable rules) using bundled ffprobe and MediaInfo. No account, no telemetry, no
network capability.

**Validated release candidate** (Phase 13 PASS, 2026-08-14):
`PreflightQC-1.0.0-setup.exe`, 72,810,462 bytes, SHA-256
`5d71cec80d5972eb42734e77ad89b079b9f64426ec87574c73c8ab2d13517504`. Clean-machine
validated end to end on Windows 11 x64 (Product Owner observed: install, launch,
real-media inspection, HTML/CSV export, uninstall with user data preserved) and on
Windows 10 x64 (PRODUCT OWNER ATTESTED). This exact artefact must ship byte-for-byte;
a rebuild voids the validation.

**Two earlier 1.0.0 candidates were withdrawn after failing clean-machine first
launch** — never publish these hashes
(full records in `docs/reports/CLEAN-MACHINE-VALIDATION-V1.md`):

- `d9e6f907…aadf05f` (withdrawn 2026-08-12): the freeze excluded `urllib.request`,
  which `jsonschema` imports at module scope. Fix: `packaging/frozen_excludes.py` —
  one exclusion list shared by the spec and tests; the packaged self-check imports the
  GUI launch closure; `tests/packaging/test_frozen_import_closure.py` guards it. No
  TLS stack ships.
- `0563117b…d43386` (withdrawn 2026-08-14): the spec's `datas` omitted
  `preflightqc/rules/schema/preset.schema.json` (and, latently, the HTML report
  template), so the frozen app crashed reading the schema at startup. Fix:
  `packaging/frozen_datas.py` — one package-data manifest shared by the spec and
  tests; the packaged self-check performs the launch's data reads (preset catalogue
  through the real loader, report template through the real renderer);
  `tests/packaging/test_frozen_data_resources.py` guards manifest completeness, the
  runtime resource paths, and the startup chain in a frozen-shaped layout.

Gate status at validation: all 12 build gates PASS; full regression 1,365 tests
(1,362 passed, 3 skipped); mypy and ruff clean; Policy U verified
(`sign.py verify --expect unsigned` exit 0; plain `verify` exit 1 — G-11 remains
OPEN, the disclosed unsigned state); G-12 owner risk acceptance complete, scoped to
exactly 1.0.0 (`docs/reports/G12-OWNER-ACCEPTANCE-V1.md`, executed 2026-08-09; voided
by any material change). No attorney has reviewed this product; no legal clearance is
claimed.

**Still required before sale** (`docs/reports/FINAL-BUILD-AUDIT-V1.md` §8): publish
the corresponding-source bundle (H-2/H-3); publish the customer pages with the
validated hash `5d71cec8…13517504`; create the marketplace product(s) and verify the
uploaded file's hash; confirm Policy U conditions U-1…U-6 at publication.

## 0.1.0-dev — development identity, 2026-08-09 and earlier

The engineering identity under which V1 was specified, built, audited and refined.
Never released, never distributed. Dated reports and captured artefacts referring to
`0.1.0-dev` describe this period and are preserved unchanged.
