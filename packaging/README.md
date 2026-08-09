# packaging/ — RESERVED, EMPTY BY DESIGN

**No build scripts, specs, or installers exist yet. This is correct.**

Populated by implementation plan Phases 11 and 12. Nothing here downloads, builds, signs,
or publishes anything until the plan is approved for execution.

## Planned contents

```
packaging/
├── build.py                  orchestrates the whole build            (Phase 11)
├── preflightqc.spec          PyInstaller ONE-DIR spec                (Phase 11)
├── installer.iss             Inno Setup script, per-user default     (Phase 11)
├── fetch_binaries.py         pinned-URL + SHA-256 fetch of inspectors(Phase 11)
├── binaries.lock.json        pinned versions, URLs, checksums        (Phase 11)
├── sign.py                   Authenticode signing                    (Phase 11)
├── layout_check.py           asserts the shipped tree is correct     (Phase 11)
├── generate_manifest.py      built package -> DEPENDENCY-MANIFEST    (Phase 12)
├── generate_notices.py       manifest -> THIRD-PARTY-NOTICES         (Phase 12)
└── scan_prohibited.py        prohibited-component scan               (Phase 12)
```

## Non-negotiables

| Rule | Reason |
| --- | --- |
| **One-dir PyInstaller build, never one-file** | Required for the LGPL shared-library-replacement posture |
| **`fetch_binaries.py` fails hard on checksum mismatch** | Never warns, never continues |
| **Shared-library filenames are never obfuscated** | FFmpeg LGPL checklist item |
| **Third-party binaries are bundled unmodified** | Modifying them would make us a "modifier" with source-correspondence duties. Re-signing is permitted; modification is not. |
| **No `ffmpeg.exe` in the package** | Spec §10.2 — V1 ships no encoder |
| **The manifest is generated from the built package** | Hand-maintained manifests drift; generated ones cannot |
| **Binaries are resolved by absolute path under `bin/`** | `PATH` is never consulted |

## Shipped layout

See `docs/architecture/ADR-001-TECH-STACK.md` §5 for the exact tree. `layout_check.py`
asserts it.

## Gates

Phase 11 exits into Phase 12, which runs release gates **G-1 … G-11 and G-13**
automatically. **G-12 — owner licensing & compliance risk acceptance (amended
2026-08-09 from attorney review; ADR-G12) — is human and blocking: the owner's
written residual-risk acceptance cannot come from tooling.**

Full detail: `docs/licensing/LICENSING-GATE-V1.md`.

## Nothing here is committed to git

Build output (`build/`, `dist/`, `packaging/output/`, `packaging/staging/`) and fetched
third-party binaries are git-ignored.
