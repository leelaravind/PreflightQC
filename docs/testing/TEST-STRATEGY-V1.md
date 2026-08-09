# PREFLIGHTQC — V1 TEST STRATEGY

| Field | Value |
| --- | --- |
| Status | Proposed. Subordinate to `docs/specification/PREFLIGHTQC-V1-SPEC.md` §24 and §25. |
| Date | 2026-08-09 |
| Executed by | `docs/planning/IMPLEMENTATION-PLAN-V1.md` phases 2, 3, 5, 9, 10 |

---

## 1. WHAT THIS TEST STRATEGY IS DEFENDING

PreflightQC's commercial value is that it is **right about severity**. A tool that
confidently tells a user their file will be rejected, when the platform only *recommended*
something, is worse than no tool — it causes needless re-exports and destroys trust.

So the test strategy is organised around four claims, in priority order:

| # | Claim | Primary defence |
| --- | --- | --- |
| **C1** | A recommendation **never** produces `FAIL`. | Severity guard tests + global preset assertion + corpus WARN fixtures |
| **C2** | Missing or undeterminable metadata **never** produces `FAIL`. | Engine semantics tests + corpus UNKNOWN fixtures |
| **C3** | Rule values match their sources **exactly**. | Source-traceability test + boundary corpus |
| **C4** | One broken file **never** terminates a batch, and source files are **never** modified. | Failure matrix + safety tests |

Everything else in this document supports one of those four.

---

## 2. TEST PYRAMID

```
                  ┌──────────────────────────────┐
                  │  Manual clean-machine        │  Phase 13
                  │  run-book (Win10 + Win11)    │  ~14 checks
                  ├──────────────────────────────┤
                  │  Integration / failure       │  Phase 10
                  │  matrix / soak               │  ~60 tests
                  ├──────────────────────────────┤
                  │  Golden corpus               │  Phase 9
                  │  fixtures × presets          │  ~400 parametrised cases
                  ├──────────────────────────────┤
                  │  Preset data assertions      │  Phase 4
                  │                              │  ~40 tests
                  ├──────────────────────────────┤
                  │  Unit: engine, model,        │  Phases 2, 3, 5, 7, 8
                  │  normaliser, reporting       │  ~500 tests
                  └──────────────────────────────┘
```

Counts are indicative targets, not quotas. **A test that does not defend C1–C4 or a
stated acceptance criterion should not be written.**

---

## 3. GOLDEN TEST CORPUS

### 3.1 Principle: generate, do not commit

Media files are **never committed**. `test-assets/corpus-manifest.json` is committed;
`tools/generate_corpus.py` produces the media; `tools/verify_corpus.py` checks the
result against recorded checksums.

This keeps the repository small, makes every fixture's construction explicit and
reviewable, and means a fixture's *intent* is documented next to its recipe.

### 3.2 Determinism requirements

| Requirement | Mechanism |
| --- | --- |
| Byte-identical regeneration | Fixed seeds; `-fflags +bitexact` (or equivalent); no encoder version string or creation timestamp written into the container |
| Cross-machine identity | Checksums recorded in the manifest and verified after generation |
| Encoder pinning | The generating encoder's exact version is recorded; a fixture that cannot be made bitexact is pinned to that version and the dependency is documented |

> **Development-only encoder exemption.** The corpus is generated with a development-only
> FFmpeg encoder on the developer's machine. It is never bundled, never referenced by
> application code, and never committed. This is dev tooling and does **not** contradict
> spec §20's prohibition on the *product* encoding — and is explicitly **not** permission
> to ship an encoder.

### 3.3 Categories (spec §24.1)

| Category | Content | Asserts |
| --- | --- | --- |
| **PASS** | One clean, conformant file per shipped preset (12) | Overall `PASS`; zero `FAIL`; zero `WARN` |
| **WARN** | One file per WARN-class rule per preset | Finding is `WARN`; overall is `WARN`, **never** `FAIL` — **C1** |
| **FAIL** | One file per `FAIL` rule, violating exactly that rule | Exactly that finding is `FAIL`; overall is `FAIL` |
| **UNKNOWN** | Files where a property is absent or undeterminable, one per gap G-1…G-6 | Finding is `UNKNOWN`; overall is **not** `FAIL` — **C2** |
| **Corrupt** | Truncated mid-`mdat`; corrupted `moov`; zero-byte; valid header + garbage body | `NOT_INSPECTED` (or partial + `UNKNOWN`); **never** `FAIL`; batch continues — **C4** |
| **Unsupported** | Non-media file with a video extension; a valid container outside every preset list | `NOT_APPLICABLE` or an explicit container `FAIL`; never an unhandled error |
| **Batch mixed** | One batch: PASS + WARN + FAIL + corrupt + unsupported + no-audio | Exact per-file statuses and exact summary counts, with `NOT_INSPECTED` counted separately from `FAIL` |
| **Boundary** | For every hard deterministic rule: just-inside and just-outside | The threshold is exactly where the source says it is — **C3** |

### 3.4 Boundary pairs — the core of C3

For **every** `FAIL` rule with a numeric threshold, two fixtures: one at the permitted
extreme, one one-unit beyond. The just-inside case must be `PASS` on that rule; the
just-outside case must be `FAIL` on that rule and only that rule.

The full boundary table is in `docs/planning/IMPLEMENTATION-PLAN-V1.md` §10 deliverable 4.
Representative rows:

| Rule | Just inside → expected | Just outside → expected |
| --- | --- | --- |
| IG Reels duration min 3 s | 3.00 s → PASS | 2.99 s → FAIL |
| IG Reels frame rate 23–60 | 23.00 and 60.00 fps → PASS | 22.98 and 60.10 fps → FAIL |
| IG Reels max width 1920 | 1920 px → PASS | 1921 px → FAIL |
| IG Stories size max 100 MB | 100 000 000 B → PASS | 100 000 001 B → FAIL |
| TikTok API dimensions 360–4096 | 360, 4096 → PASS | 359, 4097 → FAIL |
| TikTok In-Feed bitrate ≥ 516 kbps | 516 kbps → PASS | 515 kbps → FAIL |
| LinkedIn ads size 75 KB–500 MB | 76 800 and 500 000 000 B → PASS | 76 799 and 500 000 001 B → FAIL |
| LinkedIn ads AR 0.563–1.778 ±5% | at the tolerance edge inside → PASS | just beyond the tolerance → FAIL |
| LinkedIn ads audio sample rate < 64 kHz | 48 000 Hz → PASS | 64 000 Hz → FAIL |
| LinkedIn CTV bitrate ≥ 12 Mbps | 12.0 Mbps → PASS | 11.9 Mbps → FAIL |
| LinkedIn CTV frame rate set + CFR | 29.97 CFR → PASS | 27 fps → FAIL; VFR file → FAIL |

**Coverage is machine-verified.** `tests/golden/test_rule_coverage.py` enumerates every
`FAIL` rule across all shipped presets and asserts a boundary pair exists for each. An
uncovered rule **fails the build**. This is what prevents a rule being added in Phase 4
without a corresponding fixture.

### 3.5 Documented corpus exceptions

Some boundaries are impractical as real media. Each such case must be:

1. Covered by a unit test against a **synthetic `NormalisedMedia`** instead, and
2. **Recorded explicitly** in the manifest as an exception with its reason.

Known candidate: the YouTube 256 GB file-size boundary. It is never silently skipped.

---

## 4. THE SEVERITY INVARIANT TESTS (C1)

These are the most important tests in the product. Three independent layers, so a defect
must defeat all three:

### Layer 1 — engine guard (Phase 3)

`tests/rules/test_severity_guard.py`, table-driven over every
(classification × severity) pair:

| classification | FAIL | WARN | INFO | UNKNOWN |
| --- | --- | --- | --- | --- |
| `HARD_REQUIREMENT` | accept | accept | accept | accept |
| `DOCUMENTED_LIMIT` | accept | accept | accept | accept |
| `RECOMMENDATION` | **reject preset** | accept | accept | accept |
| `BEST_PRACTICE` | **reject preset** | accept | accept | accept |
| `ELIGIBILITY` | **reject preset** | accept | accept | accept |
| `UNKNOWN` | **reject preset** | **reject preset** | accept | accept |

Rejection is whole-preset, never partial.

### Layer 2 — shipped-data assertion (Phase 4)

`tests/presets/test_severity_invariant_global.py` loads **every shipped preset** and
asserts no rule classified `RECOMMENDATION`, `BEST_PRACTICE`, or `ELIGIBILITY` carries
severity `FAIL`. This is the direct enforcement of spec AC-07.

### Layer 3 — behavioural proof (Phase 9)

`tests/golden/test_recommendations_never_fail.py`: for every WARN-class rule, a real
fixture that violates it, asserting the finding is `WARN` and the **overall file status is
not `FAIL`**.

### Named regression cases

Specific historical traps that must each have a named test:

| Case | Assertion |
| --- | --- |
| Instagram Reels-tab eligibility (5–90 s, 9:16) | `ELIGIBILITY` → `WARN`. **Never `FAIL`.** |
| YouTube's entire recommended-encoding block | All → `WARN`/`INFO`. Only container-list and 256 GB are `FAIL`. |
| YouTube Shorts | No `FAIL` inherited from `youtube_standard`'s encoding recommendations. |
| TikTok Global App Bundle "≥516 kbps recommended" | `RECOMMENDATION` → `WARN`. |
| LinkedIn ads non-H.264 codec | `RECOMMENDATION` → `WARN` (LinkedIn publishes no hard video-codec whitelist for ads). |
| LinkedIn organic bitrate 192 kbps–30 Mbps | Stated as a guideline → `WARN`. |
| Instagram Feed min-width 250 px | MEDIUM-confidence `DOCUMENTED_LIMIT` → capped at `WARN`. |
| Meta / TikTok audio bitrate 128 kbps | `RECOMMENDATION` → `WARN`. |

---

## 5. MISSING-METADATA TESTS (C2)

Spec §24.4 requires proof that missing metadata does not produce `FAIL`. Coverage is
**per property class**, not a single smoke test:

| Property class | Absent-state fixture | Expected |
| --- | --- | --- |
| Video bitrate absent from container | MP4 with no `stream.bit_rate` | `UNKNOWN`, not `FAIL`; bitrate rendered as `NOT_PRESENT`, **never `0`** |
| Field order `unknown` | ffprobe reports `unknown` | `UNKNOWN` on scan-type rules (gap G-3) |
| Frame-rate mode not signalled | Container without CFR/VFR signalling | `UNKNOWN` on LinkedIn CTV "must be constant" (gap G-5) |
| No colour description | Stream with no primaries/transfer/matrix | `UNKNOWN`/`INFO`, never `FAIL` |
| No audio stream | Video-only file | Audio rules `UNKNOWN`; overall not `FAIL` (spec §23) |
| Edit-list state undeterminable | Container where `elst` cannot be read | `UNKNOWN` (gap G-1) |
| GOP not measured | Any file | `UNKNOWN` with "not verified by PreflightQC V1" (gap G-2) |
| Loudness not measured | Any file, LinkedIn CTV preset | `UNKNOWN` with "not measured by PreflightQC V1" (gap G-4) |
| HDR side data absent | SDR file | `UNKNOWN`/`INFO`, HDR rules skipped by guard |
| Unmapped `pix_fmt` | Synthetic raw output | `Undetermined` with raw value retained, no coercion |

Plus, at the model layer (Phase 2): `NotPresent` and `Undetermined` are **distinct**, and
neither is readable as a bare value without explicitly handling absence.

---

## 6. SOURCE TRACEABILITY TESTS (C3)

| Test | Asserts |
| --- | --- |
| `tests/presets/test_source_traceability.py` | Every rule's `source_ref` resolves to a section in `SOURCE-REGISTER.md`; every rule has `source_url`, `confidence`, `last_verified_date`. |
| `tests/presets/test_forbidden_values.py` | No preset contains a known-bad third-party number: LinkedIn ads 200 MB; Instagram Reels 100 MB; YouTube 512 GB; TikTok mobile 72 MB / 287.6 MB; any imported LUFS target (−14, −15, −16, −23 as a *measured* rule). |
| `tests/presets/test_conflict_encoding.py` | Each documented conflict (C-1…C-6, T-C1, T-C2, L-C1…L-C5) is represented per the plan's prescription — permissive at `FAIL`, stricter at `WARN`, or `UNKNOWN`; never silently resolved. |
| `tests/docs/test_documentation_invariants.py` | The register itself contains no `RECOMMENDATION`/`BEST_PRACTICE`/`ELIGIBILITY` row whose behaviour is `FAIL`. |
| `tests/presets/test_verbatim_values.py` | Spot-check assertions that specific high-risk values match the register exactly: IG Reels 300 MB / 15 min / 1920 px; IG Stories 100 MB / 60 s / AR ≥ 0.1:1; IG Reels AR ≥ 0.01:1 (**the two AR bounds must differ**); TikTok 360–4096 px, 23–60 fps, 4 GB; LinkedIn organic 256×144–4096×2304, AR 0.417–2.4, 10–60 fps; LinkedIn ads 500 MB / 360–1920 px / <64 kHz; LinkedIn CTV 6–60 s / ≥12 Mbps / 48 kHz stereo; YouTube 256 GB. |

The `test_verbatim_values.py` list exists because **transcription error is the
highest-probability defect in the project** and a machine check is cheaper than a reread.

---

## 7. FAILURE-HANDLING TESTS (C4)

Spec §23 has 20 rows. Each gets one integration test through the orchestrator (not the
adapter in isolation), driven by the Phase 10 fault-injection harness.

| Injected condition | Stub behaviour | Expected |
| --- | --- | --- |
| Corrupt video | real corrupt fixture | `NOT_INSPECTED`, or partial + `UNKNOWN`; never `FAIL` |
| Unsupported video | real fixture | `NOT_APPLICABLE` or explicit container `FAIL` |
| Unreadable file | ACL denial | `NOT_INSPECTED`, reason "unreadable" |
| Permission denied | ACL denial | `NOT_INSPECTED`, reason "permission denied", with hint |
| Deleted mid-scan | delete between enqueue and inspect | `NOT_INSPECTED`, "no longer available"; batch continues |
| ffprobe crash | stub exits with a fault code | MediaInfo result used alone if usable; app does not crash |
| MediaInfo crash | stub exits with a fault code | ffprobe result used alone; MediaInfo-sourced fields → `Undetermined` |
| Inspector timeout | stub sleeps past the timeout | Process **tree** terminated; `NOT_INSPECTED` or partial |
| Malformed JSON | stub emits truncated JSON | Caught; treated as inspector failure; raw output retained truncated in the diagnostic log |
| Missing metadata | valid-but-sparse JSON | `UNKNOWN`, never `FAIL` |
| Multiple video streams | real fixture | First is primary; all enumerated; `INFO` finding names which was validated |
| Multiple audio streams | real fixture | As above |
| No audio stream | real fixture | `audio.present = false`; audio rules `UNKNOWN`; overall not `FAIL` |
| Malformed preset | invalid preset document | Whole preset rejected with the offending rule named; other presets still usable |
| Interrupted batch | kill mid-batch | Clean restart, no corrupt state |
| Cancellation | cancel mid-batch | Bounded return; results preserved; batch marked partial; **zero orphan processes** |
| Report-generation failure | read-only destination / disk full | Actionable error; **results not lost** |
| Inspector binary missing | remove from `bin/` | Actionable startup message; **no `PATH` fallback** |

### 7.1 Hostile-input tests

| Input | Asserts |
| --- | --- |
| Filenames with `"`, `'`, spaces, `%`, `&`, `;`, `\|`, newline, Unicode, RTL marks | Handled correctly and **never interpreted** — proves argv-list invocation, no shell |
| Reserved Windows device names (`CON`, `NUL`, `LPT1`) | No hang, no crash |
| Path at and beyond `MAX_PATH` | Handled |
| UNC path, unreachable | Bounded timeout → `NOT_INSPECTED`, not a hang |
| File replaced with a different file mid-batch | Detected via the `(path, size, mtime)` cache key, or reported cleanly |
| File locked by another process | `NOT_INSPECTED`, not a crash |
| Enormous inspector output | Capped; no memory exhaustion |

---

## 8. SAFETY AND PRIVACY TESTS

| Test | Asserts | Acceptance criterion |
| --- | --- | --- |
| `tests/safety/test_no_network.py` | Zero outbound connections during a full inspect → validate → report cycle. The socket layer is patched to raise on any use. | AC-12 |
| `tests/safety/test_source_files_unmodified.py` | For every file in a batch: bytes, size, and mtime unchanged. Hash before and after. | AC-13 |
| `tests/safety/test_no_write_handles.py` | No source path is ever opened in a write mode. | Spec §12.1 |
| `tests/safety/test_no_path_binary.py` | With a sentinel `ffprobe` planted on `PATH`, the sentinel is never invoked. | AC-17 |
| `tests/safety/test_no_orphan_processes.py` | After cancellation and after shutdown, no inspector process survives. | Spec §15.7 |
| `tests/reporting/test_forbidden_claims.py` | No report contains "guaranteed accepted", "approved by", "certified by", or "guaranteed to upload"; the approved claim language is present. | AC-11 |
| `tests/reporting/test_html_self_contained.py` | No external URL scheme in the rendered HTML. | Spec §17.3 |

---

## 9. DETERMINISM TESTS

| Test | Method |
| --- | --- |
| Repeat determinism | Same input twice → byte-identical findings |
| Cross-process | Two processes with different `PYTHONHASHSEED` → identical output |
| Cross-locale | `LC_ALL=C` vs `LC_ALL=tr_TR.UTF-8` (the classic dotted-I trap) → identical output |
| Cross-worker-count | 1, 2, 4, 8 workers → identical results and identical presentation order |
| Engine purity | `evaluate()` with `open`, `time`, and `random` patched to raise → still succeeds |
| Report snapshots | Injected clock, version and paths → stable golden CSV and HTML |

---

## 10. ARCHITECTURE TESTS

Structural invariants are cheaper to enforce mechanically than in review:

| Test | Asserts |
| --- | --- |
| `tests/architecture/test_import_boundaries.py` | **No module below `ui/` imports Qt.** No lower layer imports a higher one. |
| `tests/rules/test_engine_is_platform_agnostic.py` | The engine source contains no platform name and no platform threshold literal. |
| `tests/ui/test_no_platform_data_in_ui.py` | No module under `ui/` contains a platform name or threshold literal. |
| `tests/ui/test_single_severity_style_source.py` | Severity styling comes from exactly one mapping table. |

The import-boundary test is what makes the ADR-001 fallback (replace the GUI framework)
affordable. It is not decoration.

---

## 11. COVERAGE POLICY

| Package | Line | Branch |
| --- | --- | --- |
| `core/`, `normalise/`, `rules/`, `results/`, `reporting/` | ≥ 90% | ≥ 85% |
| `adapters/`, `orchestration/`, `platform/`, `profiles/` | ≥ 80% | ≥ 70% |
| `ui/` | **excluded from thresholds** | — |

UI coverage is excluded deliberately. Chasing widget coverage produces brittle tests and
diverts effort from where correctness actually lives. UI gets a small number of
capability tests, not a coverage target.

**Coverage is a floor, not a goal.** A phase whose coverage passes but whose acceptance
criteria fail is not complete.

---

## 12. WHAT IS NOT TESTED, AND WHY

Stated so gaps are known rather than assumed covered:

| Not tested | Why |
| --- | --- |
| Perceptual video quality | Out of scope (spec §20) |
| Whether a platform actually accepts a file | Cannot be tested offline; the product explicitly does not claim it (spec §4.1) |
| ffprobe / MediaInfo internal correctness | Third-party; we test our handling of their output, including their failure modes |
| Safe zones, watermarks, composition | Not file-metadata properties (spec §20.1) |
| Windows ARM64 | Not a V1 target (spec §22.2) |
| macOS | Not a V1 target (spec §20) |
| Performance beyond responsiveness and soak | No V1 performance requirement exists; adding one would be scope creep |

---

## 13. TEST EXECUTION MODES

| Mode | Contents | When |
| --- | --- | --- |
| **Fast** | Unit + preset assertions + architecture tests. No media, no subprocesses. | Every change |
| **Full** | Fast + golden corpus + integration + failure matrix | Before every phase gate |
| **Offline** | Full, with the network blocked at the OS level | Before GATE-4 and GATE-6 |
| **Soak** | 1000-file mixed batch, orphan-process and memory checks | Before GATE-4 |
| **Clean machine** | The Phase 13 manual run-book, Windows 10 and Windows 11 | GATE-6 |

The corpus is generated once and cached; the fast suite never depends on it, so ordinary
development stays quick.
