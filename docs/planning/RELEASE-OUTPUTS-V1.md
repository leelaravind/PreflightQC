# PREFLIGHTQC 1.0.0 — RELEASE OUTPUT SPECIFICATION

| Field | Value |
| --- | --- |
| Date | 2026-08-10 (Final Binding) |
| Status | **Specification only — the final customer build has NOT been created.** Executing §4 requires the Product Owner's explicit `FINAL BUILD APPROVED`. |
| Identity | PreflightQC 1.0.0 · ITISYOU · Windows x64 · Policy U intentionally unsigned |

## 1. FINAL ARTEFACTS AND FILENAMES

| Artefact | Exact name | Notes |
| --- | --- | --- |
| Installer (the sold file) | `PreflightQC-1.0.0-setup.exe` | Inno Setup, per-user, no elevation; **unsigned by Policy U** |
| Package directory (inside installer) | `PreflightQC/` | One-dir layout below |
| Release hash manifest | `RELEASE-HASHES.txt` | Published on the product page; format in §3 |
| Corresponding-source bundle | the seven files of `packaging/source-release/` | Hosted at `/products/preflightqc/source`; hashes already pinned |

Package layout (unchanged from the validated architecture):

```
PreflightQC/
├── PreflightQC.exe          (icon: approved logo, multi-size .ico)
├── bin/                     ffprobe.exe + 7 libav*/libsw* DLLs, MediaInfo.exe — unmodified
├── presets/                 12 shipped presets
├── licenses/                EULA.txt, DEPENDENCY-MANIFEST.json, THIRD-PARTY-NOTICES.txt,
│                            all licence texts incl. MS-VC-Redistributable.txt
└── _internal/               CPython + Qt runtime; preflightqc/ui/assets/preflightqc.png
```

## 2. INSTALLER IDENTITY (already wired in `packaging/installer.iss`)

| Field | Value |
| --- | --- |
| AppId | `{9F1D5A2C-6B84-4E31-9C77-2A5D4E8B31F0}` (stable across versions) |
| AppName / AppVersion | PreflightQC / 1.0.0 (passed by `build.py` from `preflightqc.__version__`) |
| AppPublisher | ITISYOU |
| VersionInfoVersion | derives from AppVersion |
| SetupIconFile | `assets/logo/preflightqc.ico` (approved-logo derivative) |
| Privileges | `lowest` — per-user, no UAC |
| LicenseFile | the final `EULA.txt` |

## 3. `RELEASE-HASHES.txt` STRUCTURE

Plain text, `sha256sum`-compatible, one line per sold/served file, preceded by two
comment lines:

```
# PreflightQC 1.0.0 — release file hashes (SHA-256), published 20XX-XX-XX
# Verify: Get-FileHash <file> -Algorithm SHA256   (PowerShell)
<64-hex-sha256>  PreflightQC-1.0.0-setup.exe
```

Rules: the hash is computed from the exact uploaded artefact **after** the final
build's gates pass; the same value goes into both marketplace descriptions; any
rebuild invalidates and regenerates this file. The corresponding-source files keep
their own `SHA256SUMS` (already staged).

## 4. POST-AUTHORIZATION SEQUENCE (runs only after `FINAL BUILD APPROVED`)

1. **Remove the EULA draft banner** (`packaging/EULA.txt` header) — the first FINAL
   BUILD action, deliberately not done during binding because the binding plan does
   not authorize it. This is a **planned, justified test change**: the guard
   assertions on the banner strings ("NOT LEGAL ADVICE", "has not been reviewed")
   move to the EULA's §9 honesty block, which keeps stating that the open questions
   were never answered by an attorney. Recording that here is what makes the test
   edit at build time a documented decision rather than a weakening.
2. `python packaging/build.py` — freeze, stage `bin/ presets/ licenses/`, build
   `PreflightQC-1.0.0-setup.exe`. The build runs its own gates: manifest generation
   (G-1/G-2), prohibited-component scan (G-3/G-4), layout check, `verify_source.py`
   (G-5), self-check.
3. `python packaging/sign.py verify --expect unsigned` → **exit 0** (Policy U U-1),
   and `python packaging/sign.py verify` → **exit 1**, both outputs recorded (A8-U).
4. Full test suite against the new package (`TestTheBuiltPackage` now runs against
   the 1.0.0 artefact); mypy; ruff.
5. Generate `RELEASE-HASHES.txt` per §3 from the final installer.
6. Re-shoot the marketplace screenshot set against the release build (listing §5).
7. Clean-machine validation on Windows 10 + 11 per `RELEASE-VALIDATION-V1.md`,
   using A2-U/A8-U variants; G-12 acceptance already covers exactly this identity.
8. Publication (each its own step, in order): source page live + H-2 hash check +
   `hosting_status` flip; product/support/refunds/legal pages live with support
   contact connected; Lemon Squeezy and Gumroad products created per the two listing
   documents; Policy U conditions U-1…U-6 confirmed.

## 5. RELATIONSHIP TO THE SOURCE BUNDLE

`packaging/binaries.lock.json` pins the shipped-binary hashes and the
corresponding-source archive hashes; `verify_source.py` re-derives the match on every
build. The hosted source page (§SOURCE-PAGE.md) must serve the staged bundle
byte-for-byte — the chain is: binary in installer → lock file → archive hash →
`SHA256SUMS` → hosted file.
