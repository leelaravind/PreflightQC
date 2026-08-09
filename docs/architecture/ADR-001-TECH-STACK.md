# ADR-001 — Windows-first desktop stack

| Field | Value |
| --- | --- |
| Status | **PROPOSED ARCHITECTURE DECISION** — not approved for implementation |
| Date | 2026-08-09 |
| Decides | Language, GUI framework, packaging and test toolchain for PreflightQC V1 |
| Supersedes | — |
| Authority | Subordinate to `docs/specification/PREFLIGHTQC-V1-SPEC.md` |

> This decision takes effect **only** when the implementation plan is explicitly approved
> for execution. Nothing in this document authorises writing code, installing
> dependencies, or downloading binaries.

---

## 1. DECISION

**Python 3.12 (64-bit) + PySide6 (Qt 6) + PyInstaller one-directory build + Inno Setup
installer.**

Supporting choices:

| Concern | Choice | Note |
| --- | --- | --- |
| Language | Python 3.12 x64 | Pinned minor version; no 3.13 until re-evaluated |
| GUI | PySide6 (official Qt for Python, LGPLv3) | Qt Widgets, **not** QML |
| Concurrency | `concurrent.futures.ThreadPoolExecutor` + `subprocess` | Inspection is I/O- and process-bound, not CPU-bound; the GIL is not a constraint |
| Data model | `dataclasses` + explicit sentinel types | No ORM, no pydantic in V1 |
| Preset/rule format | JSON, validated against a JSON Schema at load | Human-diffable, tool-agnostic |
| Templating | Jinja2 (BSD-3-Clause) | HTML report only |
| CSV | stdlib `csv` | UTF-8 with BOM |
| PDF | **Deferred.** HTML report is print-clean; browser "Print to PDF" is the V1 path | See §6.3 |
| Testing | pytest + pytest-qt + coverage | |
| Lint / format / types | ruff + mypy (strict on core, lenient on UI) | |
| Packaging | PyInstaller **one-dir** (`--onedir`), never one-file | Required for LGPL relink posture — see §5 |
| Installer | Inno Setup 6 (per-user default) | |
| Signing | Authenticode via `signtool` | Application, all first-party binaries, and installer |

---

## 2. HOW THE DECISION WAS MADE

The specification's selection criteria, evaluated against four candidate stacks. Scores
are 1 (poor) to 5 (excellent). The criteria are those listed in the brief, in the order
given; **3–7 day MVP feasibility** and **Claude Code implementation efficiency** carry
the heaviest weight because they are the difference between a shipped V1 and a stalled
one.

| Criterion | Python + PySide6 | .NET 8 + Avalonia | Tauri 2 (Rust + TS) | Electron |
| --- | --- | --- | --- | --- |
| 3–7 day MVP feasibility | **5** | 3 | 2 | 3 |
| Drag-and-drop (files + folders) | 5 | 5 | 3 | 4 |
| Subprocess management | **5** | 5 | 4 | 4 |
| Local filesystem access | 5 | 5 | 4 | 4 |
| JSON processing | 5 | 5 | 4 | **5** |
| Report generation | 5 | 4 | 3 | **5** |
| Installer packaging | 4 | 4 | **5** | 3 |
| Windows reliability | 4 | **5** | 4 | 4 |
| Commercial redistribution | **3** | **5** | **5** | **5** |
| Low bundle complexity | 3 | 4 | **5** | 1 |
| Easy automated testing | **5** | 5 | 3 | 3 |
| ffprobe + MediaInfo compatibility | 5 | 5 | 5 | 5 |
| Future macOS portability | 4 | 4 | 4 | **5** |
| Claude Code implementation efficiency | **5** | 4 | 2 | 3 |

### 2.1 Why Python + PySide6

1. **Fastest path to a correct V1.** Every core operation in PreflightQC — spawn a
   process, parse JSON, evaluate a rule table, write a CSV, render an HTML template —
   is a few lines of standard-library Python. The interesting work in this product is
   the rule engine's *correctness*, not the plumbing. The stack that spends the least
   effort on plumbing leaves the most for correctness.
2. **Single language, single test runner.** One toolchain for engine, UI, and tests.
   pytest gives fast, deterministic, table-driven tests, which is exactly the shape of
   the test strategy (`docs/testing/TEST-STRATEGY-V1.md`) — hundreds of
   rule × boundary × expected-severity cases.
3. **Qt Widgets is the right UI primitive.** Native drag-and-drop for files *and*
   folders, a mature virtualised table view for large batches, native file/folder
   dialogs, and a background-thread signal/slot model that keeps a 1000-file batch
   responsive. No web renderer, no IPC bridge, no HTML layout debugging.
4. **The inspection boundary is a subprocess.** The application's most performance- and
   reliability-critical path is `spawn → read stdout → parse JSON → kill on timeout`.
   Python's `subprocess` handles this well, including Windows process-tree termination.
   The GIL is irrelevant: the threads are blocked on I/O.
5. **Deterministic output is easy.** Sorted keys, explicit `Decimal`/`Fraction` for exact
   frame-rate rationals, and `zoneinfo` for timezone-stamped reports.

### 2.2 Why not the others

**.NET 8 + Avalonia** is the strongest runner-up and is the designated fallback (§7). Its
licensing posture is genuinely better — MIT throughout, so the only copyleft-adjacent
obligation in the whole product would be FFmpeg's LGPL. It loses on MVP speed: XAML plus
MVVM plumbing plus a stricter type system costs real days on a 3–7 day target, and the
rule engine's dynamic, data-driven property lookup is more ceremony in C# than in Python.

**Tauri 2** produces the smallest, cleanest bundle and has a flawless licence
(MIT/Apache-2.0). It loses decisively on implementation efficiency: two languages
(Rust + TypeScript), an IPC boundary between them, and a WebView2 runtime dependency on
the target machine. For a tool whose value is rule correctness, splitting the work across
a Rust core and a web frontend adds cost with no product benefit.

**Electron** is rejected on bundle complexity (~150 MB before the inspectors) and on
"low bundle complexity" being an explicit criterion. Its strengths — web UI velocity,
excellent HTML report rendering — do not outweigh shipping a full Chromium to run a
metadata checker.

**PyQt6** (Riverbank) is rejected in favour of PySide6: PyQt6 is GPL-or-commercial, so a
closed-source product requires a paid Riverbank licence. PySide6 is the official Qt for
Python binding under LGPLv3, which is compliable without a purchase.

---

## 3. WHAT THIS DECISION EXPLICITLY REJECTS

- **PyInstaller `--onefile`.** A one-file build extracts to a temp directory at runtime,
  which frustrates the LGPL shared-library-replacement posture, slows startup, and
  interferes with Authenticode trust. **One-dir only.**
- **Bundling QML / Qt WebEngine.** Not needed; Qt WebEngine would add a Chromium and a
  large notice surface.
- **An in-process FFmpeg binding** (`PyAV`, `ffmpeg-python` with linked libav). Prohibited
  by spec §10.2 — ffprobe is a child process, always.
- **Any dependency requiring network access at runtime.**
- **`pydantic` / `attrs` / heavy validation frameworks in V1.** JSON Schema for preset
  validation plus dataclasses for the metadata model is sufficient and keeps the
  dependency and notice surface small.

---

## 4. DEPENDENCY LICENCE POSTURE OF THIS STACK

| Component | Licence | Copyleft on PreflightQC source? | Obligation |
| --- | --- | --- | --- |
| CPython 3.12 | PSF License (permissive) | No | Notice |
| PySide6 / Qt 6 | **LGPLv3** (Qt for Python, LGPL option) | **No, if the shared-library mechanism is satisfied** | Notice + LGPLv3 text + replaceable Qt libraries + no reverse-engineering prohibition in EULA |
| Jinja2 | BSD-3-Clause | No | Notice |
| MarkupSafe (Jinja2 dep) | BSD-3-Clause | No | Notice |
| PyInstaller | GPL **with a bootloader exception** permitting closed-source distribution of frozen apps | No | Build tool; verify the exception applies to the shipped bootloader |
| Inno Setup | Modified BSD-style | No | Build tool; notice if the stub is embedded |
| pytest, ruff, mypy, coverage | MIT / BSD | No | Dev-only; not shipped |
| ffprobe + `libav*` | **LGPL 3.0+** (verified build carries `--enable-version3`) | No (subprocess + shared) | Full FFmpeg checklist — see licensing gate §2.0 |
| MediaInfo | BSD-2-Clause | No | Attribution sentence |
| ZenLib | zlib | No | Attribution |

### 4.1 The one genuine risk in this decision

**PySide6 is LGPLv3.** That is a real obligation, and it is the reason .NET + Avalonia
scores higher on "commercial redistribution".

Three things make it acceptable:

1. **The compliance machinery is already required.** PreflightQC must already ship LGPL
   text, a notice file, a source-availability link, unobfuscated shared libraries, and
   an EULA free of a reverse-engineering prohibition — all for FFmpeg. Adding LGPLv3 Qt
   extends an existing process rather than creating a new one. **This argument became
   stronger after the 2026-08-09 amendment**: the verified FFmpeg build is itself LGPL
   **v3**, so Qt and FFmpeg now sit under the same licence version and constitute a
   single compliance surface and a single legal conversation.
2. **PyInstaller one-dir satisfies the shared-library mechanism.** Qt's `.dll` files and
   PySide6's `.pyd` extension modules sit as separate, unobfuscated files in
   `_internal/`. A user can replace them with an interface-compatible build. This is
   LGPLv3 §4(d)(1), the same route used for FFmpeg.
3. **It is reversible.** The architecture (`ARCHITECTURE-V1.md`) isolates all Qt usage
   behind the UI layer. The engine, adapters, rule evaluation, and reporting have **zero**
   Qt imports. Swapping the UI framework touches one layer.

**This risk is formally assigned to release gate G-13** (see
`docs/licensing/LICENSING-GATE-V1.md`) and to attorney review G-12. It is an **OPEN
QUESTION**, not a resolved one.

---

## 5. PACKAGING LAYOUT (proposed)

```
PreflightQC/
  PreflightQC.exe                  signed, PyInstaller one-dir launcher
  _internal/                       Python runtime, PySide6, Qt DLLs, app code
  bin/
    ffprobe.exe                    unmodified BtbN win64-lgpl-shared
    avcodec-*.dll                  unobfuscated names, LGPL shared
    avformat-*.dll
    avutil-*.dll
    swresample-*.dll
    swscale-*.dll
    MediaInfo.dll                  or mediainfo.exe (see ARCHITECTURE-V1.md §5)
  presets/                         shipped preset JSON + schema
  licenses/
    LGPL-2.1.txt
    LGPL-3.0.txt
    THIRD-PARTY-NOTICES.txt
    DEPENDENCY-MANIFEST.json
    ffmpeg-build-configuration.txt
```

Layout constraints (all derived from spec §22 and §26):

- Inspector binaries live under `bin/` and are resolved by **absolute path** from the
  application directory. `PATH` is never consulted.
- Shared-library filenames are **never** renamed or obfuscated.
- The whole tree is Authenticode-signed. Third-party DLLs may be re-signed but **must not
  be modified**.

---

## 6. CONSEQUENCES

### 6.1 Accepted costs

- Bundle size ≈ 90–130 MB before inspectors, ≈ 150–200 MB after. Acceptable for a desktop
  QC tool; well below Electron.
- Cold start ≈ 1–2 s. Acceptable.
- Python source is recoverable from a frozen bundle. **PreflightQC's IP is the rule data
  and the severity discipline, both of which are visible in the shipped presets anyway.**
  Obfuscation is not attempted and is not a V1 goal.

### 6.2 Required guardrails

| Guardrail | Enforcement |
| --- | --- |
| No Qt import outside the UI layer | Automated import-boundary test (Phase 6) |
| No network-capable library in the shipped dependency set | Dependency audit, Phase 12 |
| Pinned, hash-locked dependency versions | `requirements.lock` with hashes; CI verifies |
| Deterministic evaluation (no locale/clock dependence) | Determinism test, Phase 3 |

### 6.3 PDF export

PDF is a "prefer if feasible" requirement (spec §17.1). Every viable Python PDF path adds
either a heavy dependency (WeasyPrint → Pango/Cairo/GObject, a large notice and bundle
surface) or a licence complication. **V1 ships a print-clean, fully self-contained HTML
report** and defers native PDF to a Phase 8 stretch goal, re-evaluated against the
dependency gate (spec §21.6). If the gate rejects every candidate, HTML remains the
human-readable format and this is recorded, not silently dropped.

---

## 7. FALLBACK

If attorney review (G-12) or the dependency gate (G-13) rejects bundling LGPLv3 Qt in a
closed-source commercial product, the fallback is:

**.NET 8 + Avalonia UI (MIT) + `dotnet publish` self-contained + WiX/Inno installer.**

The fallback is viable **only** because the architecture keeps the UI layer thin and
Qt-free below it. Triggering the fallback re-does Phase 6 (desktop UI) and Phase 11
(packaging) and leaves Phases 2–5 and 7–9 conceptually intact but requiring a port.

**The fallback decision must be taken before Phase 6 begins.** Discovering it after Phase
11 would be expensive. This is why the licensing gate has an early checkpoint at the end
of Phase 1 (see `docs/planning/IMPLEMENTATION-PLAN-V1.md`, gate GATE-1).

---

## 8. OPEN QUESTIONS

| # | Question | Owner | Blocks |
| --- | --- | --- | --- |
| Q-1 | Does bundling LGPLv3 PySide6/Qt via PyInstaller one-dir satisfy LGPLv3 §4 for a closed-source commercial product? | Attorney (G-12) + early check at GATE-1 | Phase 6 start |
| Q-2 | Does the PyInstaller bootloader exception cover the shipped bootloader as used here? | Attorney (G-12) | Release |
| Q-3 | MediaInfo CLI or library? | Engineering, Phase 1 spike | Phase 1 exit |
| Q-4 | Is a native PDF path available that survives the dependency gate? | Engineering, Phase 8 | Phase 8 scope only |
| Q-5 | Python 3.12 vs 3.13 — is PySide6 + PyInstaller support for 3.13 mature on the target date? | Engineering, Phase 0 | Phase 0 exit |
