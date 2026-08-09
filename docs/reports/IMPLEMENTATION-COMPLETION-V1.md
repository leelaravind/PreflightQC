# PREFLIGHTQC — V1 IMPLEMENTATION COMPLETION REPORT

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Version built | `0.1.0-dev` |
| Plan executed | `docs/planning/IMPLEMENTATION-PLAN-V1.md` |
| Stack | ADR-001 as specified: Python 3.12.10 x64, PySide6 6.8.1.1, pytest, PyInstaller one-dir, Inno Setup |
| Overall status | **Phases 0, 2–10 complete. Phase 1 BLOCKED at GATE-1. Phases 11–13 blocked downstream of it.** |
| Releasable | **NO** — and deliberately so. See §9. |

---

## 1. HEADLINE

The engine, the preset data, the orchestration, the UI, the reporting and the test suite
are built and green. **957 tests pass, 3 skip, 0 fail.** Type checking, linting and the
documentation invariants are clean.

What is **not** done is everything that requires the two third-party inspector binaries,
because they are not present on this machine and the plan explicitly forbids downloading
them. That blocks GATE-1, and GATE-1 gates the packaging and licensing phases.

This is the correct outcome, not a shortfall: shipping a package built on an unverified
ffprobe build is precisely what the licensing gate exists to prevent.

---

## 2. PHASES COMPLETED

| Phase | Name | Status | Note |
| --- | --- | --- | --- |
| 0 | Repository, spec and source normalisation | **COMPLETE** | Toolchain pinned, doc invariants enforced in CI |
| 1 | Inspector technical spike | **BLOCKED — GATE-1** | Harness written and verified to fail closed; binaries absent |
| 2 | Normalised metadata model | **COMPLETE** | Three-valued fields, exact rationals, derived geometry |
| 3 | Rule and preset engine | **COMPLETE — GATE-2 PASSED** | Severity ceiling enforced at load time |
| 4 | Platform preset data | **COMPLETE** | 12 presets, 170 rules, 95 FAIL rules |
| 5 | Adapters and batch orchestration | **COMPLETE** | Real process runner; adapters tested against injected failures |
| 6 | Desktop UI | **COMPLETE** | Qt confined to the UI layer, enforced by test |
| 7 | Custom client profiles | **COMPLETE** | Full §16.1 property set, atomic storage |
| 8 | Reporting | **COMPLETE** | CSV + self-contained HTML from one shared model |
| 9 | Golden test corpus | **COMPLETE WITH A DOCUMENTED SUBSTITUTION** | Synthetic-model boundary corpus; no real media (§6) |
| 10 | Integration and robustness | **COMPLETE — GATE-4 PASSED for automatable criteria** | Failure matrix, soak, hostile inputs |
| 11 | Windows packaging | **TOOLING WRITTEN, BUILD NOT RUN** | Blocked on GATE-1 |
| 12 | Dependency and licensing audit | **TOOLING WRITTEN, GATES FAIL CLOSED** | Blocked on GATE-1 |
| 13 | Clean-machine release validation | **NOT STARTED** | Requires a package and clean Win10/Win11 machines |

---

## 3. FILES CREATED

### Application (`src/preflightqc/`, 33 modules)

| Layer | Modules |
| --- | --- |
| L0 platform | `process.py`, `paths.py`, `binaries.py` |
| L1 adapters | `base.py`, `ffprobe.py`, `ffprobe_raw.py`, `mediainfo.py`, `mediainfo_raw.py` |
| L2 core | `values.py`, `model.py`, `vocabulary.py`, `geometry.py` |
| L2 normalise | `normaliser.py`, `precedence.py` |
| L3 rules | `severity.py`, `finding.py`, `operators.py`, `document.py`, `loader.py`, `engine.py`, `schema/preset.schema.json` |
| L3 results | `aggregate.py` |
| L4 reporting | `model.py`, `csv_writer.py`, `html_renderer.py`, `export.py`, `claims.py`, `templates/report.html.j2` |
| L4 profiles | `model.py`, `compiler.py`, `store.py` |
| L5 scan | `enumerate.py` |
| L5 orchestration | `runner.py` |
| L6 ui | `app.py`, `main_window.py`, `viewmodels.py`, `severity_style.py`, `about.py` |
| L6 cli | `headless.py` (development-only) |

### Preset data (`presets/`, 12 documents)

`meta/`: `ig_reels`, `ig_stories`, `ig_feed` · `tiktok/`: `tiktok_content_posting_api`,
`tiktok_studio_web`, `tiktok_infeed_auction_nonspark`, `tiktok_topview_reservation` ·
`youtube/`: `youtube_standard`, `youtube_shorts` · `linkedin/`: `linkedin_organic`,
`linkedin_video_ads`, `linkedin_ctv`

### Tests (`tests/`, 19 modules across 13 packages)

`docs/`, `core/`, `normalise/`, `rules/`, `results/`, `presets/`, `platform/`,
`adapters/`, `orchestration/`, `profiles/`, `reporting/`, `golden/`, `integration/`,
`architecture/`, plus `factories.py` and `golden/synthetic.py`.

### Tooling

`tools/check_docs.py` · `spikes/probe_matrix.py` · `packaging/preflightqc.spec`,
`binaries.lock.json`, `scan_prohibited.py`, `generate_manifest.py`, `layout_check.py`

### Configuration

`pyproject.toml`, `requirements.lock`

## FILES MODIFIED

`docs/FUTURE.md` (two limitations discovered during implementation, §8) ·
`.gitignore` (one Windows shell artefact, §10)

**No authoritative document was modified.** The specification, source register,
architecture, plan, test strategy and licensing gate are unchanged.

---

## 4. TEST RESULTS

```
957 passed, 3 skipped, 0 failed          11.2s
```

| Check | Result |
| --- | --- |
| `pytest` | **957 passed, 3 skipped** |
| `mypy` (strict below the UI) | **Success: no issues found in 52 source files** |
| `ruff check` | **All checks passed** |
| `tools/check_docs.py` | **All 6 documentation invariants hold** |

The 3 skips are boundary-derivation cases for rule shapes with no derivable violating
value (`present`-operator rules); each is skipped with an explicit reason, not silently.

### Coverage

| Scope | Coverage | Plan target |
| --- | --- | --- |
| Core packages (`core`, `normalise`, `rules`, `results`, `reporting`) | **96%** | ≥ 90% |
| Whole application (UI and CLI excluded per policy) | **92%** | — |
| `rules/severity.py` — the severity ceiling | **100%** | — |

### The four claims the strategy defends

| Claim | Evidence |
| --- | --- |
| **C1 — a recommendation never produces FAIL** | 56 ceiling tests over every (classification × severity) pair; a global assertion over all 170 shipped rules; a behavioural test per never-FAIL rule proving a violation yields WARN and the file is not failed |
| **C2 — missing metadata never produces FAIL** | Per-property-class engine tests; plus, for **every one of the 12 presets**, a fully-undetermined file asserted to produce zero FAIL findings |
| **C3 — rule values match their sources** | Source-ref and source-URL traceability into the register; forbidden-value scan for the four rejected third-party figures; 21 verbatim spot-checks; boundary pairs derived from the shipped values themselves |
| **C4 — one broken file never kills a batch; sources are never modified** | Failure-matrix tests per failure kind; SHA-256 before/after over every batch; a write-mode guard on source paths; 250-file soak |

---

## 5. ACCEPTANCE CRITERIA

| # | Criterion | Status |
| --- | --- | --- |
| AC-01 | Drag-and-drop, file picker, folder picker | **MET** (code + enumeration tests; drag-drop wired to `dropEvent`) |
| AC-02 | Select any shipped preset or custom profile | **MET** |
| AC-03 | 100+ mixed files, no file failure terminates the batch | **MET** (250-file soak) |
| AC-04 | Five per-file statuses computed per §7.2/§7.4 | **MET** (exhaustive truth table) |
| AC-05 | Batch summary counts NOT_INSPECTED separately from FAIL | **MET** |
| AC-06 | Findings show detected, expected, explanation, severity, rule id, source | **MET** |
| AC-07 | No shipped RECOMMENDATION/BEST_PRACTICE/ELIGIBILITY carries FAIL | **MET** — automated assertion over all shipped presets |
| AC-08 | Missing metadata yields UNKNOWN, never FAIL | **MET** — per preset and per property class |
| AC-09 | Create/edit/save/delete/export/import a custom profile | **MET** |
| AC-10 | CSV and human-readable report with all §17.2 elements | **MET** |
| AC-11 | Reports carry the approved claim and none of the forbidden ones | **MET** — automated content assertion |
| AC-12 | Full cycle with outbound network blocked | **MET** — socket layer patched to raise |
| AC-13 | No source file modified (bytes, size, mtime) | **MET** — hash comparison + write-mode guard |
| AC-14 | Cancellable; completed results preserved; report marked partial | **MET** |
| AC-15 | Every §23 failure row has a passing test | **MET** for every row reachable without real binaries |
| AC-16 | Golden corpus passes offline | **MET WITH SUBSTITUTION** — synthetic model, not real media (§6) |
| AC-17 | Installs and runs on a clean machine; never uses a PATH binary | **PARTIAL** — PATH avoidance proven by test; clean-machine install **NOT VERIFIED** |
| AC-18 | Release package has DEPENDENCY-MANIFEST and THIRD-PARTY-NOTICES | **NOT MET** — generators written, no package exists |
| AC-19 | No GPL/nonfree component in the release package | **NOT MET** — scanner written and fails closed, no package to scan |
| AC-20 | Application and installer Authenticode-signed | **NOT MET** — no certificate, no package |

**16 of 20 met. 1 partial. 3 not met, all downstream of GATE-1.**

---

## 6. KNOWN LIMITATIONS

### 6.1 GATE-1 blocked — the inspector binaries are absent

`third-party/bin/` is empty. `ffprobe`, MediaInfo and the development-only FFmpeg encoder
are not present, and nothing is on `PATH`. The Phase 1 spike harness exists, runs, and
correctly refuses to proceed:

```
$ python spikes/probe_matrix.py
GATE-1 BLOCKED: inspector binaries not present in third-party/bin/: ffprobe, mediainfo
exit 2
```

**Consequences, stated plainly:**

- The per-field precedence table (`normalise/precedence.py`) is **documented, not
  measured**. It comes from source-register §5. If a real inspector behaves differently,
  entries need revision — a one-line table edit, which is why it is a table.
- Register gaps G-1…G-6 are implemented as documented. Whether each is genuinely
  undeterminable in practice is **unconfirmed**. The failure direction is conservative:
  an unconfirmed gap yields `UNKNOWN`, never a wrong verdict.
- ADR-001 **Q-3** (MediaInfo CLI vs library) and **Q-6** (whether MediaInfo's
  `HDR_Format` alone suffices) remain **unresolved**. Interim decisions: CLI subprocess,
  and the HDR first-frame read implemented but **disabled by default** — so in the
  shipped configuration the decoder is never engaged, which is the preferred outcome
  under the licensing review.

### 6.2 The golden corpus is synthetic, not generated media

No encoder is available, so no real fixture could be produced. The test strategy §3.5
authorises exactly this substitution, and it was taken deliberately rather than skipping
the rule.

**What was built instead:** boundary cases **derived from each shipped rule's own
expected value** and evaluated against a synthetic `NormalisedMedia`. Every one of the
95 FAIL rules gets a just-inside and a just-outside case, and a coverage test fails the
build if any FAIL rule yields no cases — so a rule cannot ship untested.

**What this proves:** each rule fires at exactly the threshold its source states.
**What it does not prove:** that ffprobe reports the value we think it does for a real
file. That is Phase 1's job and it is outstanding.

### 6.3 Not verifiable without a package

Clean-machine install, SmartScreen behaviour, PyInstaller plugin completeness, and the
real ffprobe build audit are all unverified. The packaging and licensing tooling is
written and **fails closed** — each of the three gate scripts was run and each correctly
refused a non-existent package (exit 1, 1, 2).

### 6.4 Engine limitation discovered

The engine compares a property against a constant; it has no cross-property operator.
LinkedIn CTV's "audio duration must match video duration" therefore ships as a
`RECOMMENDATION` that reports the value rather than comparing it. Recorded in
`docs/FUTURE.md` §3A.1 rather than implemented, because adding a second operand class is
an engine change and Phase 4 was preset data only.

---

## 7. DEPENDENCY MANIFEST

**No manifest exists, because no package exists.** `packaging/generate_manifest.py`
generates it from a built package and refuses to invent one.

What the manifest **will** cover, pinned in `packaging/binaries.lock.json`:

| Component | Licence | Linkage | Status |
| --- | --- | --- | --- |
| ffprobe + `libav*` | LGPL-2.1-or-later | subprocess | **UNSET** — must be a BtbN `win64-lgpl-shared` build |
| MediaInfo (CLI) | BSD-2-Clause | subprocess | **UNSET** — ≥ 0.7.63, no GUI, no libcurl |
| ZenLib | zlib | transitive | pending |
| CPython 3.12 | PSF-2.0 | frozen | present |
| PySide6 / Qt 6 | **LGPL-3.0** | dynamic | present — **see §9** |
| Jinja2, MarkupSafe | BSD-3-Clause | frozen | present |
| jsonschema | MIT | frozen | present |

Every checksum in the lock file is deliberately `UNSET`. They must be filled from the
publishers' own published checksums — never from a hash computed after downloading,
which would verify nothing.

**Runtime network capability:** the PyInstaller spec excludes `PySide6.QtNetwork`,
`urllib.request`, `http`, `ftplib`, `smtplib` and related modules. The preset schema
contains no remote `$ref`, verified by test. The application is designed to be
*incapable* of a network request rather than merely not making one.

---

## 8. LICENSING STATUS

**NO LEGAL CLEARANCE IS CLAIMED, AND NO GATE HAS BEEN MARKED COMPLETE THAT IS NOT.**

| Gate | Status |
| --- | --- |
| G-1 manifest complete + checksums | **NOT MET** — no package |
| G-2 notices cover every component | **NOT MET** — generator written |
| G-3 prohibited-component scan clean | **NOT MET** — scanner written, fails closed, nothing to scan |
| G-4 ffprobe confirmed LGPL shared | **NOT MET** — this is GATE-1 |
| G-5 version-matched FFmpeg source archived | **NOT MET** |
| G-6 configure line recorded | **NOT MET** |
| G-7 DLL names unobfuscated | **NOT MET** — checker written; UPX disabled in the spec |
| G-8 EULA carve-outs | **NOT STARTED** |
| G-9 MediaInfo + ZenLib notices | **PARTIAL** — required sentences are in the About dialog; full file pending |
| G-10 official sources + published checksums | **NOT MET** |
| G-11 Authenticode signing | **NOT MET** |
| **G-12 attorney review** | **NOT COMPLETE — HUMAN GATE. Cannot be satisfied by any tool in this repository, and has not been.** |
| G-13 GUI framework licence posture | **OPEN** — see §9 |

Compliance measures **already implemented in code**:

- The startup self-check scans the bundled ffprobe's reported configuration for all 19
  prohibited build tokens and reports a licence violation rather than proceeding quietly.
- Inspector binaries are resolved by **absolute path only**; `PATH` is never consulted,
  proven by a test that plants a sentinel executable on `PATH` and asserts it is never
  invoked.
- The PyInstaller spec is **one-dir** and disables UPX, so Qt and `libav*` remain
  separate, unobfuscated, replaceable files — the LGPL shared-library-mechanism posture.
- The About dialog carries the required FFmpeg, MediaInfo and ZenLib notices and renders
  entirely offline.
- Reports and UI carry no platform-endorsement claim; a forbidden-phrase detector is
  asserted against every generated report.

---

## 9. OPEN MANUAL GATES

| # | Gate | Owner | Blocks |
| --- | --- | --- | --- |
| 1 | **GATE-1** — supply checksum-verified BtbN `win64-lgpl-shared` ffprobe and MediaInfo ≥ 0.7.63 into `third-party/bin/`, plus sample media | Operator | Phases 1, 11, 12, 13 |
| 2 | **GATE-3 / Q-1** — is bundling **LGPLv3 PySide6/Qt** in a closed-source commercial product acceptable? | Attorney | Release. **The UI is already built on Qt** because the stack instruction directed it; the ADR-001 fallback (.NET + Avalonia) remains affordable because no module below the UI imports Qt, enforced by test. |
| 3 | **Q-2** — does the PyInstaller bootloader exception cover the shipped bootloader? | Attorney | Release |
| 4 | **G-12** — final commercial licence, EULA and notice review | Attorney | Release |
| 5 | **G-8** — EULA drafting with the LGPL carve-outs (no reverse-engineering prohibition, FFmpeg ownership disclaimer, all translations) | Legal + operator | Release |
| 6 | **G-11** — Authenticode certificate | Operator | Release |
| 7 | **Phase 13** — clean Windows 10 and Windows 11 x64 machines | Operator | Release |
| 8 | Development-only FFmpeg encoder, for real-media corpus generation | Operator | Full Phase 9 |

---

## 10. SPEC DEVIATIONS

**NONE that weaken the specification.** Three substitutions were made where the plan's
preferred route was unavailable; each is authorised by the governing document and each is
recorded, not silent.

| # | Item | Authorised by | Nature |
| --- | --- | --- | --- |
| D-1 | Phase 2 built against the **documented** precedence table rather than measured spike output | Necessity — GATE-1 blocked | **Dependency-order deviation.** Recorded in `SPIKE-01-INSPECTOR-FINDINGS.md` §1.2 with its unverified consequences. Fails conservative: an unconfirmed field yields UNKNOWN. |
| D-2 | Golden corpus is a **synthetic-model** boundary corpus, not generated media | Test strategy §3.5 explicitly authorises this substitution and requires it be recorded | **Substitution, not a skip.** Coverage over all 95 FAIL rules is machine-verified. |
| D-3 | Phase 6 (UI) proceeded with **GATE-3 unresolved** | The stack instruction directed PySide6 explicitly; GATE-3 is a *legal* gate that blocks **release**, not development | **Sequencing.** Mitigated by the "no Qt below the UI" invariant, which keeps the documented fallback affordable. G-13 and G-12 remain open and are reported as such. |

Two **strengthenings** beyond what the plan required, both prompted by tests catching
real weaknesses:

- Every FAIL rule must rest on a **HIGH-confidence** source. This caught
  `linkedin_organic.max_duration_hard` resting on a MEDIUM reading; the rule was
  re-justified (above 15 minutes *both* documented figures are exceeded, so the
  rejection does not depend on resolving the conflict) rather than quietly downgraded.
- Every file now contributes **at least one row** to the findings CSV. Previously a
  clean file produced no row at all and silently vanished from the export.

**One non-code note:** a literal `%SystemDrive%/` directory appeared in the working
directory during the session. It contains Windows shell caches, and nothing in this
codebase references that variable. It was **not deleted** — it is not ours to remove —
and is excluded in `.gitignore` so it cannot be committed.

---

## 11. FUTURE ITEMS RECORDED

Added to `docs/FUTURE.md` during implementation, per spec §29.3:

- **§3A.1 Cross-property rules** — the engine cannot express "audio duration must equal
  video duration"; LinkedIn CTV actually specifies this.
- **§3A.2 Surfacing inspector disagreement** — a conflicted property that passes on the
  permissive reading shows as a clean PASS with only an INFO note. Correct per §10.4, but
  arguably under-weighted in the UI. Any fix must be presentational: promoting it to WARN
  would violate §7.1.

Nothing from the locked non-goals list was implemented.

---

## 12. RELEASE READINESS

### **NOT RELEASABLE.**

| Dimension | Assessment |
| --- | --- |
| Functional completeness | **High.** Every V1 feature is implemented and tested. |
| Correctness discipline | **High.** The severity invariant is enforced structurally at three independent layers and proven over all 170 shipped rules. |
| Real-world verification | **None.** The product has never inspected a real video file. |
| Packaging | **Not produced.** |
| Licensing | **Not cleared.** Eleven of thirteen gates open, including the human one. |

**The single next action** is GATE-1: place checksum-verified binaries in
`third-party/bin/` and run `python spikes/probe_matrix.py`. Everything downstream —
Phase 1 completion, packaging, the licensing audit and clean-machine validation — unlocks
from there.

**The single longest-lead action** is the attorney engagement (G-12 and Q-1). The plan
schedules it at GATE-3, i.e. before the UI phase. It has not been started, and it cannot
be accelerated by engineering effort.

---

## 13. `git status --short`

```
 M .gitignore
 M docs/FUTURE.md
?? docs/planning/SPIKE-01-INSPECTOR-FINDINGS.md
?? docs/reports/
?? packaging/binaries.lock.json
?? packaging/generate_manifest.py
?? packaging/layout_check.py
?? packaging/preflightqc.spec
?? packaging/scan_prohibited.py
?? presets/
?? pyproject.toml
?? requirements.lock
?? spikes/
?? src/preflightqc/
?? tests/adapters/
?? tests/architecture/
?? tests/conftest.py
?? tests/core/
?? tests/docs/
?? tests/factories.py
?? tests/golden/
?? tests/integration/
?? tests/normalise/
?? tests/orchestration/
?? tests/platform/
?? tests/presets/
?? tests/profiles/
?? tests/reporting/
?? tests/results/
?? tests/rules/
?? tools/
```

**Not committed. Not pushed. Not published. No release action taken.**
