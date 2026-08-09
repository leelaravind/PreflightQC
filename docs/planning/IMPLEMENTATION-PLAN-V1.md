# PREFLIGHTQC — V1 IMPLEMENTATION PLAN

| Field | Value |
| --- | --- |
| Status | **AWAITING APPROVAL — NOT AUTHORISED FOR EXECUTION** |
| Version | 1.0.0 |
| Date | 2026-08-09 |
| Authority | Subordinate to `docs/specification/PREFLIGHTQC-V1-SPEC.md` |
| Stack | `docs/architecture/ADR-001-TECH-STACK.md` (PROPOSED) |
| Structure | `docs/architecture/ARCHITECTURE-V1.md` |

---

## 0. HOW TO EXECUTE THIS PLAN

This document is written to be executed by a later session under an instruction such as
*"Execute the approved implementation plan exactly as written."*

### 0.1 Execution rules

1. **Phases execute in order** unless the phase's `Parallelizable` field says otherwise.
2. **A phase is not complete until every acceptance criterion in its table passes.**
   Partial completion is reported as partial, never as done.
3. **Do not invent product requirements.** If this plan is ambiguous about *what the
   product should do*, stop and ask. Do not choose on the user's behalf and proceed.
   (Implementation detail *within* a stated requirement is yours to decide.)
4. **Do not expand scope.** Anything not in the specification or this plan is out of
   scope. Ideas go to `docs/FUTURE.md`.
5. **Do not weaken the severity model** to make a test pass. If a test fails because the
   severity model forbids something, the test or the rule data is wrong — not the model.
6. **Do not add a platform rule** without a backing row in
   `docs/sources/SOURCE-REGISTER.md`.
7. **Do not add a dependency** without running it through spec §21 and recording it in the
   dependency manifest.
8. **Record every deviation** from the specification in the completion report under
   `SPEC DEVIATIONS`. Silent deviation is a defect.
9. **Stop at every GATE.** Gates are listed in §16 and are blocking.

### 0.2 Conventions used below

| Field | Meaning |
| --- | --- |
| Objective | What this phase makes true that was not true before |
| Modules | Files/modules expected to exist at phase exit |
| Depends on | Phases that must be complete first |
| Deliverables | Concrete artefacts |
| Acceptance | Conditions that prove the phase is done. Every one is checkable. |
| Tests | Test artefacts created in this phase |
| Risks | What can go wrong |
| Rework trigger | The condition under which this phase must be redone or rolled back |
| Prerequisites | Non-code preconditions (decisions, approvals, tooling) |
| Parallelizable | Whether this phase can run concurrently with another |

Module paths are relative to `src/preflightqc/` unless stated.

---

## 1. PHASE 0 — REPOSITORY, SPEC AND SOURCE NORMALISATION

**Objective.** The repository is a working development environment with a pinned
toolchain, a validated documentation set, and automated checks that the specification's
structural invariants hold — before any product code exists.

**Depends on.** Nothing. This is the entry point.

**Prerequisites.**
- Approval of this plan.
- Confirmation of ADR-001 Q-5 (Python 3.12 vs 3.13 — verify PySide6 and PyInstaller
  support for the chosen minor version on the execution date; if 3.12 support is
  unhealthy, stop and report rather than silently switching).

**Modules.**

```
pyproject.toml                     project metadata, tool config (ruff, mypy, pytest)
requirements.in / requirements.lock  hash-pinned runtime deps
requirements-dev.lock              hash-pinned dev deps
src/preflightqc/__init__.py        __version__ single source of truth
src/preflightqc/py.typed
tests/conftest.py
tests/docs/test_documentation_invariants.py
tools/check_docs.py
.editorconfig
```

**Deliverables.**

1. A Python 3.12 x64 virtual environment reproducible from the lock files.
2. `ruff`, `mypy`, `pytest`, `coverage` configured and running clean on an empty tree.
3. `__version__` defined once; everything else imports it.
4. `tools/check_docs.py`, wired into the test suite, asserting:
   - Every document referenced by `README.md` exists.
   - `docs/sources/SOURCE-REGISTER.md` §0 lists all six research areas and each named
     PDF exists at its stated path.
   - The register contains no row whose Class is `RECOMMENDATION`, `BEST_PRACTICE`, or
     `ELIGIBILITY` and whose Behaviour column contains the token `FAIL`.
5. A `CHANGELOG.md` seeded at `0.1.0-dev`.

**Acceptance.**

| # | Criterion |
| --- | --- |
| P0-A1 | `pip install -r requirements.lock` succeeds from a clean venv with hash verification. |
| P0-A2 | `ruff check`, `ruff format --check`, and `mypy src` all pass. |
| P0-A3 | `pytest` runs and passes with the documentation-invariant tests present. |
| P0-A4 | All six research PDFs are present at the paths named in the source register. |
| P0-A5 | The severity-ceiling grep over the source register finds zero violations. |
| P0-A6 | No runtime dependency in `requirements.lock` has network capability. Verified by an explicit reviewed list, recorded in the phase report. |

**Tests.** `tests/docs/test_documentation_invariants.py`.

**Risks.**
- *PySide6 wheel unavailable for the pinned Python minor version.* → Detected here, not in
  Phase 6. Stop and report.
- *Hash-pinned installs fail behind a proxy.* → Environment issue; report, do not disable
  hash checking.

**Rework trigger.** A change to the specification's document set or to the source
register's structure.

**Parallelizable.** No. Everything depends on this.

---

## 2. PHASE 1 — INSPECTOR TECHNICAL SPIKE

**Objective.** Empirically determine what `ffprobe` and MediaInfo can and cannot tell us
about real files, on Windows, so that Phase 2's model is built on measurements rather than
assumptions — and resolve the open questions that would be expensive to answer later.

**Depends on.** Phase 0.

**Prerequisites.**
- ffprobe: an **unmodified BtbN `win64-lgpl-shared`** build, obtained manually by the
  operator from the official source and checksum-verified. **This phase does not
  auto-download anything.**
- MediaInfo 26.05 (or the then-current BSD-era release) from `mediaarea.net` or the
  official MediaArea GitHub release, checksum-verified.
- Both placed under `third-party/bin/` (git-ignored).
- A small set of real sample files supplied by the operator, covering at minimum: H.264
  MP4, HEVC MP4, VP9 WebM, MOV, an interlaced file, a VFR file, a file with no audio, an
  HDR (PQ or HLG) file, and a deliberately truncated file.

**Deliverables.** *Spike code lives in `spikes/` and is **not** shipped.*

1. `spikes/probe_matrix.py` — runs both inspectors over the sample set and emits a
   coverage matrix.
2. `docs/planning/SPIKE-01-INSPECTOR-FINDINGS.md` recording, per field in spec §9:
   - Does ffprobe report it? Reliably? Under what conditions is it absent?
   - Does MediaInfo report it? Reliably?
   - Which should win in the precedence table?
   - Measured cost (ms) of each invocation mode.
3. A **decision on ADR-001 Q-3** (MediaInfo CLI vs library), with measured spawn cost, a
   crash-isolation assessment, and a recommendation. Default is CLI unless the
   measurements contradict `ARCHITECTURE-V1.md` §4.3.
4. A decision on whether the bounded HDR first-frame read is necessary, i.e. whether
   MediaInfo's `HDR_Format` alone is sufficient for the V1 HDR `INFO` findings. **If it
   is sufficient, the decoder is never engaged and the patent-exposure question in the
   FFmpeg source pack becomes moot — prefer this outcome.**
5. Measured behaviour for each row of spec §23 that is reachable at this layer: corrupt
   file, unreadable file, permission denied, timeout, malformed JSON, zero-byte file,
   file with a 4 GB+ size, path >260 chars, UNC path.
6. Recorded exact version strings and checksums of both inspectors.

**Acceptance.**

| # | Criterion |
| --- | --- |
| P1-A1 | Every field in spec §9 has a row in the findings document with an explicit determinability verdict. |
| P1-A2 | The precedence table for §10.4 is fully populated and justified by observation, not assumption. |
| P1-A3 | Q-3 (CLI vs library) is decided and recorded with measurements. |
| P1-A4 | The HDR strategy is decided and recorded; if the first-frame read is retained, the reason is stated. |
| P1-A5 | Every §23 condition reachable at this layer has an observed inspector behaviour recorded. |
| P1-A6 | ffprobe's reported configuration is confirmed to contain **no** `--enable-gpl` and **no** `--enable-nonfree`, and none of the prohibited components. Output captured verbatim in the findings document. |
| P1-A7 | Gaps G-1 … G-6 from source register §5.1 are each confirmed or refuted by observation. |

**Tests.** No shipped tests. The spike's output is the deliverable. Sample-file
observations become fixtures for Phase 9.

**Risks.**
- *The obtained ffprobe build is GPL.* → **STOP.** This is GATE-1. Do not proceed with a
  non-conforming build.
- *MediaInfo cannot determine scan type on the sample set.* → Expected and documented;
  the model must represent it as `Undetermined`, and the affected rules become `UNKNOWN`.
- *Field availability differs from the source register's assumptions.* → Update the
  register's §5 mapping table; that is what this phase is for.

**Rework trigger.** Changing either inspector's version or build variant invalidates the
findings and requires re-running the spike.

**Parallelizable.** No — Phase 2's design depends on its output.

> **GATE-1 fires at the end of this phase.** See §16.

---

## 3. PHASE 2 — NORMALISED METADATA MODEL

**Objective.** A pure, dependency-free representation of a media file's metadata that can
express *known*, *not present*, *undetermined*, and *conflicted* — and a normaliser that
converts raw inspector output into it without ever fabricating a value.

**Depends on.** Phase 1.

**Modules.**

```
core/values.py          Known / NotPresent / Undetermined / Conflicted, Provenance
core/model.py           NormalisedMedia, FileInfo, ContainerInfo, VideoStream, AudioStream
core/vocabulary.py      pix_fmt, container, codec, colour canonicalisation tables
core/geometry.py        SAR/DAR/rotation -> displayed geometry; exact Fraction frame rates
adapters/base.py        InspectorOutcome, failure taxonomy
adapters/ffprobe_raw.py raw ffprobe JSON -> typed intermediate
adapters/mediainfo_raw.py raw MediaInfo JSON -> typed intermediate
normalise/precedence.py the per-field precedence table (DATA)
normalise/normaliser.py raw intermediates -> NormalisedMedia
```

**Deliverables.**

1. The three-valued field type, with **no** implicit conversion to a bare value. Reading
   a field's value must require explicitly handling the absent cases.
2. `NormalisedMedia` covering every field in spec §9.1–9.5.
3. Canonicalisation tables as **data**: `pix_fmt → (chroma, bit_depth)`,
   container name sets → canonical container, codec name/tag → canonical codec. An
   unmapped input yields `Undetermined` with the raw value retained — never a coercion.
4. Exact-rational frame rate (`Fraction`), never a float in the model.
5. Displayed-geometry computation applying SAR **and** rotation, with `derived` flagged.
6. Bitrate resolution recording its source (`stream` / `container` / `computed`).
7. Precedence table populated from the Phase 1 findings.
8. Conflict detection producing `Conflicted(a, b)` with both provenances.
9. Primary-stream selection (first video, first audio) with all streams enumerated.

**Acceptance.**

| # | Criterion |
| --- | --- |
| P2-A1 | Every spec §9 field exists in the model with a three-valued type. |
| P2-A2 | An absent bitrate normalises to `NotPresent`, **not** `0`. Asserted by test. |
| P2-A3 | An `unknown` field-order from ffprobe normalises to `Undetermined`, distinct from `NotPresent`. Asserted by test. |
| P2-A4 | 24000/1001 round-trips exactly and compares equal to 23.976 within the declared tolerance; `Fraction` is used throughout. |
| P2-A5 | A file with SAR ≠ 1 produces a displayed DAR that differs from `width/height`, flagged as derived. |
| P2-A6 | A file with 90° rotation metadata produces swapped displayed dimensions. |
| P2-A7 | Where the two inspectors disagree on a field, the result is `Conflicted` with both values and provenances retained. |
| P2-A8 | Every populated field carries provenance naming the inspector and the raw field path. |
| P2-A9 | An unmapped `pix_fmt` yields `Undetermined` with the raw string retained — no silent default. |
| P2-A10 | `mypy --strict` passes over `core/` and `normalise/`. |
| P2-A11 | No module in this phase imports Qt, or any L3–L5 module. Asserted by the import-boundary test. |

**Tests.**

- `tests/core/test_values.py` — the three-valued type, including that a bare value cannot
  be read without handling absence.
- `tests/core/test_vocabulary.py` — table-driven canonicalisation, including unmapped
  inputs.
- `tests/core/test_geometry.py` — SAR, rotation, DAR, exact rationals.
- `tests/normalise/test_normaliser.py` — table-driven, using **captured real ffprobe and
  MediaInfo JSON fixtures from Phase 1** (committed as JSON, not as media).
- `tests/normalise/test_conflicts.py` — conflict detection and preservation.
- `tests/architecture/test_import_boundaries.py` — created here, extended each phase.

**Risks.**
- *Over-modelling.* → The model covers spec §9 and stops. No speculative fields.
- *Float leakage.* → A test asserts no `float` appears in frame-rate storage.

**Rework trigger.** A Phase 1 finding revision, or a spec §9 change.

**Parallelizable.** No.

---

## 4. PHASE 3 — RULE AND PRESET ENGINE

**Objective.** A generic, deterministic, platform-agnostic evaluation engine, plus a
preset schema and loader that **mechanically enforces the severity invariant** — with no
platform data present at all.

**Depends on.** Phase 2.

**Modules.**

```
rules/schema/preset.schema.json     JSON Schema for preset documents
rules/document.py                   PresetDocument, RuleRecord, SourceRef
rules/operators.py                  the operator set, each with accepted value shapes
rules/loader.py                     load, schema-validate, severity-guard, path-resolve
rules/severity.py                   classification -> max severity ceiling (spec §7.3)
rules/engine.py                     evaluate(media, preset) -> Finding[]
rules/finding.py                    Finding
results/aggregate.py                Finding[] -> FileResult; BatchSummary derivation
```

**Deliverables.**

1. `preset.schema.json` requiring every field in spec §11.2, with `rule_id` uniqueness
   and `source_ref` / `confidence` / `last_verified_date` mandatory.
2. The operator set from `ARCHITECTURE-V1.md` §6.5, each declaring its accepted value
   shapes and its tolerance semantics.
3. **The severity guard**: a single table mapping classification → maximum severity,
   applied at load time, rejecting the whole preset on violation.
4. Property-path resolution validated at load, so an unknown path fails the preset rather
   than failing a file at runtime.
5. `evaluate()` implementing `ARCHITECTURE-V1.md` §6.3 exactly, including:
   - `applies_when` guards **skip**, never fail;
   - `NotPresent` / `Undetermined` → `UNKNOWN` finding, **never** `FAIL`;
   - `Conflicted` → `INFO` with both values, evaluated against the more permissive value,
     severity capped at `WARN`;
   - deterministic ordering.
6. `aggregate()` implementing spec §7.2 with `INFO` and `UNKNOWN` **structurally absent**
   from the computation's inputs, plus the separate `NOT_INSPECTED` / `NOT_APPLICABLE`
   states.

**Acceptance.**

| # | Criterion |
| --- | --- |
| P3-A1 | Loading a preset whose rule declares `severity: FAIL` with `classification: RECOMMENDATION` **fails the whole preset** with a message naming the rule. |
| P3-A2 | Same for `BEST_PRACTICE` and `ELIGIBILITY`. |
| P3-A3 | Loading a preset with an unknown property path, unknown operator, mismatched value shape, duplicate `rule_id`, or missing `source_ref` fails the whole preset. |
| P3-A4 | A malformed preset **never partially loads**; the loader is all-or-nothing. |
| P3-A5 | A rule over a `NotPresent` property emits exactly one `UNKNOWN` finding and zero `FAIL` findings. |
| P3-A6 | A rule over an `Undetermined` property emits `UNKNOWN`, with an explanation distinguishing it from `NotPresent`. |
| P3-A7 | A rule whose `applies_when` is false emits no `FAIL` and no `WARN`. |
| P3-A8 | A `Conflicted` property can never produce `FAIL`. |
| P3-A9 | Overall status matches spec §7.2 for all 2^3 combinations of {has FAIL, has WARN, has other}, plus INFO-only and UNKNOWN-only cases. Exhaustive truth-table test. |
| P3-A10 | `INFO` and `UNKNOWN` findings do not change overall status. Asserted directly. |
| P3-A11 | Evaluating the same fixture twice, and across two processes with different `PYTHONHASHSEED` and different `LC_ALL`, yields byte-identical finding sequences. |
| P3-A12 | The engine source contains **no** occurrence of "instagram", "tiktok", "youtube", "linkedin", "reels", "shorts" (case-insensitive), and no platform threshold literal. Asserted by a source-scanning test. |
| P3-A13 | `evaluate()` performs no I/O, reads no clock, and uses no randomness. Asserted by a test that patches `open`, `time`, and `random` to raise. |
| P3-A14 | No module in this phase imports Qt or any L4–L5 module. |

**Tests.**

- `tests/rules/test_severity_guard.py` — **the most important test file in the product.**
  Table-driven over every (classification, severity) pair.
- `tests/rules/test_loader_rejection.py` — every malformed-preset class.
- `tests/rules/test_operators.py` — table-driven per operator, including tolerance
  boundaries and value-shape rejection.
- `tests/rules/test_engine_semantics.py` — guards, missing, undetermined, conflicted.
- `tests/rules/test_determinism.py` — repeat, cross-process, cross-locale.
- `tests/rules/test_engine_is_platform_agnostic.py` — the source scan.
- `tests/results/test_aggregate.py` — exhaustive truth table.

**Risks.**
- *Severity logic leaking into evaluation.* → Guard at load, not at evaluation; asserted.
- *Float comparison defects.* → Tolerances are explicit and required for numeric
  operators; a bare `==` on floats is rejected in review and by a lint rule.

**Rework trigger.** Any change to spec §7 or §11.

**Parallelizable.** No — Phase 4 consumes the schema.

> **GATE-2 fires at the end of this phase.** See §16.

---

## 5. PHASE 4 — PLATFORM PRESET DATA

**Objective.** Every V1 preset exists as validated data, each rule traceable to a row in
the source register, with **zero engine changes**.

**Depends on.** Phase 3. Independent of Phases 5–8.

**Prerequisites.** Source register §1–§4 is the only input. **No new research. No new
sources. No values from memory.**

**Modules (data, not code).**

```
presets/meta/ig_reels.json
presets/meta/ig_stories.json
presets/meta/ig_feed.json
presets/tiktok/tiktok_content_posting_api.json
presets/tiktok/tiktok_studio_web.json
presets/tiktok/tiktok_infeed_auction_nonspark.json
presets/tiktok/tiktok_topview_reservation.json
presets/youtube/youtube_standard.json
presets/youtube/youtube_shorts.json
presets/linkedin/linkedin_organic.json
presets/linkedin/linkedin_video_ads.json
presets/linkedin/linkedin_ctv.json
presets/RULESET-VERSION                     e.g. 2026-08-09.1
```

**Deliverables.**

1. Twelve preset documents, each carrying `ruleset_version`, `last_verified_date`, a
   `sources[]` block, and per-rule `source_ref`, `confidence`, `last_verified_date`.
2. Every rule value **verbatim** from the register, with units explicit.
3. Conflicts encoded per spec §6.6.4 — the permissive value at `FAIL`, the stricter at
   `WARN`, or `UNKNOWN`. Specifically:
   - **LinkedIn organic duration** (L-C2): `WARN` 10–15 min, `FAIL` above 15 min.
   - **TikTok duration/size** (T-C1, T-C2): path-specific presets; each preset also
     carries an `INFO` rule surfacing the other paths' limits.
   - **Instagram Reels vs Stories AR lower bound** (C-4): 0.01:1 and 0.1:1 preserved
     verbatim in their own presets, never normalised.
   - **LinkedIn byte convention** (L-C5): decimal bytes, with a `WARN` band within ~2% of
     each ceiling, recorded in the preset's `caveats[]`.
4. `UNKNOWN` rules with explicit "not documented" / "not measured by PreflightQC V1"
   explanations for: Meta loudness, Meta HDR input requirement, Meta closed-GOP,
   TikTok's undocumented set, YouTube's `UNKNOWN` set including Dolby Vision, LinkedIn CTV
   loudness, and every gap G-1…G-6.
5. Preset `caveats[]` text surfaced in the UI, including LinkedIn CTV's "currently in
   testing / doesn't guarantee delivery to all publishers".
6. `presets/README.md` documenting how to add or amend a preset, and the register-first
   rule.

**Acceptance.**

| # | Criterion |
| --- | --- |
| P4-A1 | All twelve presets load and pass the Phase 3 loader, including the severity guard. |
| P4-A2 | **Across all shipped presets, zero rules classified `RECOMMENDATION`, `BEST_PRACTICE`, or `ELIGIBILITY` carry severity `FAIL`.** Global assertion. (Spec AC-07.) |
| P4-A3 | Every rule's `source_ref` resolves to a section present in `SOURCE-REGISTER.md`. Automated cross-check. |
| P4-A4 | Every rule has a non-empty `explanation`, `source_url`, `confidence`, and `last_verified_date`. |
| P4-A5 | The Instagram Reels-tab eligibility rule (5–90 s, 9:16) is classified `ELIGIBILITY` and carries severity `WARN`. |
| P4-A6 | The YouTube preset contains exactly two file-measurable `FAIL` rules: container-not-on-list and size > 256 GB. |
| P4-A7 | The YouTube Shorts preset contains no `FAIL` rule inherited from `youtube_standard`'s encoding recommendations. |
| P4-A8 | No preset contains the 200 MB LinkedIn ad figure, the 100 MB Reels figure, the 512 GB YouTube figure, or any third-party mobile file-size cap. Asserted by a forbidden-value test. |
| P4-A9 | Each of the six documented conflicts (C-1…C-6), both TikTok conflicts, and L-C1…L-C5 is represented in preset data or `caveats[]` in the manner prescribed by §5 deliverable 3. |
| P4-A10 | LinkedIn presets use decimal byte thresholds (500 MB = 500 000 000). Asserted. |
| P4-A11 | Presets are pure data: no preset references code, and the engine required **zero** changes to support them. Verified by the phase diff touching no file under `rules/`. |

**Tests.**

- `tests/presets/test_all_presets_load.py`
- `tests/presets/test_severity_invariant_global.py` — **AC-07's enforcement.**
- `tests/presets/test_source_traceability.py`
- `tests/presets/test_forbidden_values.py`
- `tests/presets/test_conflict_encoding.py`

**Risks.**
- *Transcription error.* → Highest-probability defect in the project. Mitigation: each
  preset is cross-checked against the register row-by-row as a discrete review step, and
  `test_source_traceability.py` machine-checks the linkage. **Numbers are never typed
  from memory.**
- *Temptation to fill an `UNKNOWN`.* → Forbidden. `test_forbidden_values.py` guards the
  known-bad numbers.

**Rework trigger.** Any correction to the source register.

**Parallelizable.** **Yes** — with Phase 5 and Phase 6, once Phase 3 is complete.

---

## 6. PHASE 5 — INSPECTION ADAPTERS AND BATCH ORCHESTRATION

**Objective.** A batch of files can be inspected, normalised and validated headlessly,
concurrently, cancellably, with per-file failure isolation — with no UI.

**Depends on.** Phases 2, 3. (Phase 4 not required; a fixture preset suffices.)

**Modules.**

```
platform/process.py         the single process runner: spawn, timeout, kill tree, caps
platform/paths.py           app dir, local app data, long-path handling, binary resolution
platform/binaries.py        absolute-path resolution + startup self-check + version capture
adapters/ffprobe.py         ffprobe adapter
adapters/mediainfo.py       MediaInfo adapter
scan/enumerate.py           file/folder enumeration, dedupe, extension filtering
orchestration/job.py        Job, JobState
orchestration/batch.py      Batch, BatchState, BatchSummary
orchestration/runner.py     worker pool, pipeline, progress, cancellation
orchestration/cache.py      session inspection cache keyed on (path, size, mtime_ns)
cli/headless.py             dev-only headless entry point (not shipped)
```

**Deliverables.**

1. A process runner that: uses no shell; passes argv as a list; sets explicit `cwd` and a
   minimal environment; hides the console window; enforces a per-call timeout; **kills the
   whole process tree** on timeout or cancel; caps stdout/stderr; reaps children; and
   **never raises**.
2. Both adapters returning the `InspectorOutcome` taxonomy from `ARCHITECTURE-V1.md` §4.1.
3. Binary resolution by **absolute path** under the application directory, with a startup
   self-check that launches each inspector, captures its version, and reports an
   actionable error on failure. **`PATH` is never consulted.**
4. Enumeration that is off-thread, cancellable, de-duplicating, symlink-safe, long-path
   safe, and treats extension as a candidate filter only.
5. A worker pool (default 4, configurable) executing inspect → normalise → validate per
   job, with **every exception converted to an `InspectionFailure`** at the job boundary.
6. Streaming results, input-order presentation, derived summary.
7. Cooperative cancellation with bounded grace, preserving completed results and marking
   the batch partial.
8. Session inspection cache enabling preset change without re-inspection.
9. A headless dev entry point: `python -m preflightqc.cli.headless <paths> --preset <id>`
   emitting JSON — used by the integration tests and the golden corpus runner.

**Acceptance.**

| # | Criterion |
| --- | --- |
| P5-A1 | A batch containing one file that crashes an inspector, one unreadable file, one permission-denied file, and one file deleted mid-scan completes; all other files produce results. |
| P5-A2 | Each failure above yields `NOT_INSPECTED` with a distinct, correct reason — and **not** `FAIL`. |
| P5-A3 | An inspector that hangs is terminated at the timeout, the whole process tree is gone, and the batch continues. Verified by process enumeration after the batch. |
| P5-A4 | Cancellation mid-batch returns within the grace period, preserves completed results, marks the batch partial, and leaves **zero** orphan inspector processes. |
| P5-A5 | Presentation order equals input order regardless of worker count (tested at 1, 2, 4, 8 workers) and results are otherwise identical. |
| P5-A6 | Changing the preset re-validates without re-invoking any inspector. Asserted by a spawn counter. |
| P5-A7 | Enumerating a folder tree with >5000 files remains cancellable and never blocks longer than the cancellation grace period. |
| P5-A8 | A path >260 characters and a UNC path are both handled; an unreachable UNC path times out as `NOT_INSPECTED` rather than hanging. |
| P5-A9 | An ffprobe binary present on `PATH` but **not** in `bin/` is never invoked. Asserted by planting a sentinel executable on `PATH`. |
| P5-A10 | Startup self-check failure (binary missing) produces an actionable error and no silent fallback. |
| P5-A11 | No source file is opened for writing; bytes, size and mtime are unchanged across a full batch. (Spec AC-13.) |
| P5-A12 | Zero outbound network connections during a full headless run. Asserted by patching the socket layer to raise. (Spec AC-12.) |
| P5-A13 | No module in this phase imports Qt. |

**Tests.**

- `tests/platform/test_process_runner.py` — timeout, tree kill, output caps, no shell.
- `tests/adapters/test_ffprobe_adapter.py`, `test_mediainfo_adapter.py` — using stub
  executables that emit canned output, exit non-zero, hang, or emit malformed JSON.
- `tests/scan/test_enumerate.py`
- `tests/orchestration/test_batch_isolation.py` — spec §23 rows reachable here.
- `tests/orchestration/test_cancellation.py`
- `tests/orchestration/test_determinism_across_workers.py`
- `tests/orchestration/test_cache.py`
- `tests/safety/test_no_network.py`, `tests/safety/test_source_files_unmodified.py`
- `tests/safety/test_no_path_binary.py`

**Risks.**
- *Windows process-tree termination is not the same as `kill`.* → Explicitly implemented
  and tested with a deliberately hanging stub that spawns a grandchild.
- *Cancellation deadlock.* → Cooperative flag checked between stages; no lock held across
  a subprocess call.

**Rework trigger.** Q-3 (CLI vs library) reversal; concurrency model change.

**Parallelizable.** **Yes** — with Phase 4.

---

## 7. PHASE 6 — DESKTOP UI

**Objective.** Every capability in `ARCHITECTURE-V1.md` §2.1 is usable, driving the Phase
5 orchestrator, with no domain logic and no platform data in the UI layer.

**Depends on.** Phases 4, 5.

**Prerequisites.** **GATE-3 must have passed** — the LGPLv3 Qt question (ADR-001 Q-1)
must be resolved before this phase begins. If it is unresolved, stop and report; do not
start building on a framework that may have to be replaced.

**Modules.**

```
ui/app.py                     application bootstrap, startup self-check surfacing
ui/main_window.py             layout, drag-drop target
ui/viewmodels/*.py            immutable snapshots: batch, file result, metadata, summary
ui/widgets/file_table.py      virtualised batch table
ui/widgets/preset_selector.py grouped selector with version/date/caveats
ui/widgets/findings_pane.py   ordered findings, detected vs expected, source links
ui/widgets/metadata_pane.py   normalised model with provenance and absent-state display
ui/widgets/summary_bar.py
ui/widgets/progress.py
ui/dialogs/export.py
ui/dialogs/about.py           offline notices, LGPL text, inspector versions
ui/severity_style.py          the single severity -> colour/icon/label mapping
ui/bridge.py                  command dispatch + snapshot publication (the only threading seam)
```

**Deliverables — stated as capability, state consumed, state emitted, proof.**

| Capability | Consumes | Emits | Proof of completion |
| --- | --- | --- | --- |
| Drag-and-drop of files **and** folders, mixed | OS drop payload | `AddPathsCommand` | Dropping a mixed selection enqueues every eligible file exactly once, de-duplicated |
| File picker (multi-select) | — | `AddPathsCommand` | Selecting 3 files enqueues 3 jobs |
| Folder picker with visible recurse toggle | — | `AddPathsCommand(recurse)` | Recurse off enumerates one level; on enumerates the tree |
| Preset selector | `PresetCatalogViewModel` | `SelectPresetCommand` | Shows all 12 presets grouped by family, each with `ruleset_version`, `last_verified_date`, and caveats; selecting one and re-running re-validates without re-inspection |
| Run / Cancel | `BatchState` | `StartBatchCommand`, `CancelBatchCommand` | Cancel during a 500-file batch returns within the grace period with results preserved and the batch marked partial |
| Batch table | `BatchViewModel` | `SelectFileCommand`, `RemoveFileCommand` | 1000 rows scroll smoothly; status badges update as results stream; order is input order |
| Progress | `BatchProgress` | — | "n of m" and in-flight count update continuously; UI never freezes |
| Findings pane | `FileResultViewModel` | — | For a selected file, findings render in the engine's order with severity, property, detected, expected, explanation, rule id, source (title + URL + access date + confidence), and inspector provenance |
| Metadata pane | `NormalisedMetadataViewModel` | — | `NOT_PRESENT`, `UNDETERMINED` and `CONFLICTED` render as distinct, labelled states — never as blank or zero |
| Summary bar | `BatchSummary` | — | PASS/WARN/FAIL/NOT_INSPECTED/NOT_APPLICABLE shown as five separate counters |
| Export dialog | `BatchResult` | `ExportReportCommand` | Format + destination chosen; default destination is not the source folder |
| Custom profile editor | `CustomProfile` | profile commands | Phase 7 |
| About / notices | `AboutInfo` | — | Renders version, both inspector versions, third-party notices and LGPL text entirely offline |

**Acceptance.**

| # | Criterion |
| --- | --- |
| P6-A1 | All three input methods work, including dropping folders. |
| P6-A2 | The UI thread performs no file I/O and spawns no process. Asserted by patching those calls to raise if invoked on the UI thread. |
| P6-A3 | A 1000-file batch keeps the UI responsive; cancel works throughout. |
| P6-A4 | **No module under `ui/` contains a platform name or a platform threshold literal.** Source-scanning test. |
| P6-A5 | Severity styling comes from exactly one mapping table; no severity string is hard-coded in a widget. Source-scanning test. |
| P6-A6 | Absent/undetermined/conflicted metadata renders as explicit labelled states, never as `0` or blank. |
| P6-A7 | Findings render in the engine's deterministic order; the UI does not re-sort by default. |
| P6-A8 | **No module below `ui/` imports Qt.** Import-boundary test — the enforcement of the ADR-001 fallback option. |
| P6-A9 | The About screen renders with all network access blocked. |
| P6-A10 | Startup self-check failure (missing inspector) surfaces an actionable dialog, not a stack trace. |

**Tests.**

- `tests/ui/test_drag_drop.py`, `test_pickers.py` (pytest-qt)
- `tests/ui/test_viewmodels.py` — immutability and snapshot semantics
- `tests/ui/test_responsiveness.py` — large-batch smoke
- `tests/architecture/test_import_boundaries.py` — extended: **no Qt below L6**
- `tests/ui/test_no_platform_data_in_ui.py`
- `tests/ui/test_absent_state_rendering.py`

**Risks.**
- *Domain logic drifting into widgets.* → The import-boundary test plus the
  no-platform-data scan.
- *`pytest-qt` flakiness in CI.* → Keep UI tests thin; the value lives in Phases 2–5.
- *LGPLv3 reversal after this phase.* → Mitigated by GATE-3 preceding it.

**Rework trigger.** GATE-3 reversal → the UI layer is rebuilt on the ADR-001 fallback
stack. Nothing below L6 changes.

**Parallelizable.** Partially — can start once Phase 5's orchestrator interface is frozen,
concurrently with Phase 4.

---

## 8. PHASE 7 — CUSTOM CLIENT PROFILES

**Objective.** A user can author, save, edit, delete, export and import a local profile
covering the spec §16.1 property set, evaluated by the same engine as platform presets.

**Depends on.** Phases 3, 6.

**Modules.**

```
profiles/model.py         CustomProfile
profiles/compiler.py      CustomProfile -> PresetDocument
profiles/store.py         atomic load/save/delete/import/export in %LOCALAPPDATA%
ui/dialogs/profile_editor.py
```

**Deliverables.**

1. An editor covering **exactly** the spec §16.1 set: dimensions, aspect ratio,
   containers, video codecs, frame rate, duration, file size, video bitrate, audio codec,
   audio sample rate, audio channels. **No additional properties.**
2. Per-property *required* / *recommended* toggle, compiling to `HARD_REQUIREMENT` /
   `RECOMMENDATION` — which passes the §7.3 guard without weakening it.
3. Unconfigured properties compile to **no rule at all**.
4. Compilation to a `PresetDocument` that passes the Phase 3 loader unchanged.
5. Atomic storage (temp + fsync + replace); a crash mid-save never corrupts an existing
   profile.
6. Export = single file; import = validate then copy, with a new id on collision.
7. Custom `preset_id`s cannot shadow shipped ones.
8. Reports from a custom profile print the **profile name**, never a platform name.

**Acceptance.**

| # | Criterion |
| --- | --- |
| P7-A1 | A profile can be created, saved, reloaded after restart, edited, and deleted. |
| P7-A2 | A compiled profile passes the Phase 3 loader, including the severity guard. |
| P7-A3 | An unconfigured property produces zero rules and zero findings. |
| P7-A4 | A property marked *recommended* can only ever produce `WARN`. |
| P7-A5 | Export then import on a clean profile store reproduces the profile exactly. |
| P7-A6 | Importing a profile whose id collides with a shipped preset is rejected or re-ided; a shipped preset is never shadowed. |
| P7-A7 | Interrupting a save (simulated crash between write and replace) leaves the previous profile intact and loadable. |
| P7-A8 | A report generated from a custom profile contains the profile name and **no** platform name. |
| P7-A9 | The editor exposes no property outside spec §16.1. Asserted by test against the §16.1 list. |

**Tests.** `tests/profiles/test_compiler.py`, `test_store_atomicity.py`,
`test_roundtrip.py`, `test_no_shadowing.py`, `test_property_set_bounds.py`.

**Risks.**
- *Scope creep into a broadcast-spec authoring suite* (explicitly forbidden by spec §16.6).
  → P7-A9 is the mechanical guard.

**Rework trigger.** A spec §16.1 change.

**Parallelizable.** **Yes** — with Phase 8.

---

## 9. PHASE 8 — REPORTING

**Objective.** A completed (or partial) batch exports a CSV and a self-contained
human-readable report containing every element of spec §17.2, with CSV and HTML built from
one shared model so they cannot disagree.

**Depends on.** Phases 3, 5. UI wiring depends on Phase 6.

**Modules.**

```
reporting/model.py        ReportModel — the single shared structure
reporting/csv_writer.py
reporting/html_renderer.py
reporting/templates/report.html.j2
reporting/templates/report.css      inlined at render time
reporting/claims.py       approved claim text + forbidden-phrase constants
```

**Deliverables.**

1. `ReportModel` built once from `BatchResult`, consumed by both writers.
2. CSV: UTF-8 **with BOM**, RFC 4180 quoting, `\r\n`, stable column order, one row per
   finding, plus a summary section or companion summary CSV.
3. HTML: fully self-contained — CSS inlined, **no** remote font, script, image, or CDN
   reference.
4. Both carry: PreflightQC version; scan start/end with timezone; preset name, id,
   `ruleset_version`, `last_verified_date`; **inspector versions actually used**; totals
   for PASS/WARN/FAIL/NOT_INSPECTED/NOT_APPLICABLE; per-file overall; per-finding detected
   value, expected/recommended value, explanation, severity, rule id, source ref;
   complete-vs-partial status; the approved claim language; the "does not modify source
   files" statement.
5. Atomic write (render fully in memory → temp file → replace). A write failure surfaces
   an actionable error **with results retained in memory**.
6. Default export directory is user-writable and **never** the source video folder.
7. **PDF is evaluated, not assumed.** Assess candidate paths against the spec §21.6
   dependency gate. If none survives, HTML remains the human-readable format and the
   decision is recorded in `docs/planning/PDF-DECISION.md`. **Do not silently drop it.**

**Acceptance.**

| # | Criterion |
| --- | --- |
| P8-A1 | Every element of spec §17.2 appears in both CSV and HTML. Checklist test. |
| P8-A2 | The HTML report contains no external URL scheme (`http:`, `https:`, `//`, `file:` to outside the document). Scanning test. |
| P8-A3 | The report renders correctly with all network access blocked. |
| P8-A4 | The report contains the approved claim language and **none** of the spec §4.1 forbidden phrases. Content assertion. (Spec AC-11.) |
| P8-A5 | CSV opens correctly in Excel with non-ASCII filenames (BOM present, quoting correct). |
| P8-A6 | A partial/cancelled batch produces a report explicitly marked partial, listing what was not processed. |
| P8-A7 | Simulated write failure (read-only destination, disk full) surfaces an actionable error and **loses no results**. |
| P8-A8 | CSV and HTML agree on every count and every per-file status, for a fixed corpus. Cross-format consistency test. |
| P8-A9 | Golden snapshot tests pass for a fixed corpus, preset and injected clock. |
| P8-A10 | The default export directory is not the source video folder. |
| P8-A11 | The PDF decision is recorded either as a shipped capability or as a documented, gate-justified deferral. |

**Tests.** `tests/reporting/test_report_contents.py`,
`test_html_self_contained.py`, `test_forbidden_claims.py`, `test_csv_format.py`,
`test_partial_batch_report.py`, `test_write_failure.py`, `test_cross_format_consistency.py`,
`tests/reporting/snapshots/`.

**Risks.**
- *A templating helper reaching for a remote asset.* → P8-A2 scanner.
- *Snapshot churn.* → Clock, version and paths are injected, so snapshots are stable.

**Rework trigger.** A spec §17 change.

**Parallelizable.** **Yes** — with Phase 7.

---

## 10. PHASE 9 — GOLDEN TEST CORPUS

**Objective.** A deterministic, reproducibly generated set of media files with known
expected findings, covering every category in spec §24, so that rule regressions are
caught mechanically.

**Depends on.** Phases 2, 3, 4, 5.

**Prerequisites.**
- A **development-only** FFmpeg encoder, used **solely** to generate test media on the
  developer's machine. It is **never bundled**, **never** referenced by application code,
  and **never** committed. This does not contradict spec §20 (which forbids the *product*
  from encoding); it is dev tooling, and this exemption is stated explicitly so a later
  session does not mistake it for scope creep — nor mistake it for permission to ship an
  encoder.

**Modules.**

```
test-assets/corpus-manifest.json        the committed source of truth (media is NOT committed)
tools/generate_corpus.py                manifest -> media files, deterministic
tools/verify_corpus.py                  checksum verification
tests/golden/test_golden_corpus.py
tests/golden/expectations/*.json        expected findings per (file, preset)
```

**Deliverables.**

1. `corpus-manifest.json`: for each fixture — id, purpose, target preset(s), generation
   recipe (exact encoder arguments), expected checksum, and expected outcome.
2. A generator producing **byte-identical output** for a given manifest entry and encoder
   version (fixed seeds, no timestamps in output containers, `-fflags +bitexact` or
   equivalent).
3. Coverage across all spec §24 categories:

| Category | Minimum coverage |
| --- | --- |
| PASS | One clean file per shipped preset (12) |
| WARN | One file per WARN-only rule class per preset — proving `WARN`, not `FAIL` |
| FAIL | One file per `FAIL` rule, violating exactly that rule |
| UNKNOWN | Files with metadata absent/undeterminable for each gap G-1…G-6 |
| Corrupt | Truncated mid-`mdat`; corrupted `moov`; zero-byte; valid header + garbage body |
| Unsupported | A non-media file with a video extension; an obscure but valid container outside every preset list |
| Batch mixed | One batch combining PASS + WARN + FAIL + corrupt + unsupported + missing-audio |
| Boundary | For **every** hard deterministic rule: one just-inside and one just-outside case |

4. **Boundary pairs are the core deliverable.** For each `FAIL` rule with a numeric
   threshold, two fixtures. Examples (non-exhaustive, derived from the register):

| Rule | Just inside | Just outside |
| --- | --- | --- |
| IG Reels duration min 3 s | 3.00 s | 2.99 s |
| IG Reels duration max 15 min | 900.0 s | 900.1 s |
| IG Reels / Stories frame rate 23–60 | 23 fps and 60 fps | 22.98 fps and 60.1 fps |
| IG Reels max width 1920 | 1920 px | 1921 px |
| IG Stories size max 100 MB | 100 000 000 B | 100 000 001 B |
| TikTok API dimension 360–4096 | 360 and 4096 | 359 and 4097 |
| TikTok API size max 4 GB | at limit | just over |
| TikTok In-Feed bitrate ≥ 516 kbps | 516 kbps | 515 kbps |
| TikTok TopView duration 5–60 s | 5.0 s and 60.0 s | 4.9 s and 60.1 s |
| YouTube size max 256 GB | *sparse-file strategy — see risks* | |
| LinkedIn organic resolution 256×144–4096×2304 | at both corners | one pixel outside each |
| LinkedIn organic AR 1:2.4–2.4:1 | at both bounds | just outside each |
| LinkedIn ads AR 0.563–1.778 ±5% | at the tolerance edge inside | just outside the tolerance |
| LinkedIn ads size 75 KB–500 MB | 76 800 B and 500 000 000 B | 76 799 B and 500 000 001 B |
| LinkedIn ads audio sample rate < 64 kHz | 48 000 Hz | 64 000 Hz |
| LinkedIn CTV duration 6–60 s | 6.0 s and 60.0 s | 5.9 s and 60.1 s |
| LinkedIn CTV bitrate ≥ 12 Mbps | 12 Mbps | 11.9 Mbps |
| LinkedIn CTV frame rate set | 29.97 (CFR) | 27 fps, and a VFR file |

5. Expectation files stating, per (fixture, preset): expected findings by rule id,
   expected severity of each, and expected overall status.
6. `verify_corpus.py` confirming regenerated media matches the recorded checksums.

**Acceptance.**

| # | Criterion |
| --- | --- |
| P9-A1 | Regenerating the corpus from the manifest on a second machine reproduces identical checksums. |
| P9-A2 | Every hard deterministic `FAIL` rule in every shipped preset has both a just-inside and a just-outside fixture. **Coverage is machine-verified against the preset rule set — an uncovered rule fails the build.** |
| P9-A3 | Every rule classified `RECOMMENDATION` / `BEST_PRACTICE` / `ELIGIBILITY` has a fixture that violates it and a test asserting the finding is `WARN` and the overall status is **not** `FAIL`. (Spec §24.3.) |
| P9-A4 | For each gap G-1…G-6 there is a fixture proving the affected rule yields `UNKNOWN` and the overall status is not `FAIL`. (Spec §24.4.) |
| P9-A5 | Corrupt and unsupported fixtures yield `NOT_INSPECTED` / `NOT_APPLICABLE`, never `FAIL`, and never terminate the batch. |
| P9-A6 | The mixed batch produces the exact expected per-file statuses and summary counts. |
| P9-A7 | A file with no audio stream produces `UNKNOWN` on audio rules and overall status **not** `FAIL`. |
| P9-A8 | The full corpus runs with network access blocked. |
| P9-A9 | No media file is committed to the repository (`.gitignore` enforced, asserted by test). |

**Tests.** `tests/golden/test_golden_corpus.py` (parametrised over every fixture × preset),
`tests/golden/test_rule_coverage.py` (P9-A2's enforcement),
`tests/golden/test_recommendations_never_fail.py`,
`tests/golden/test_missing_metadata_never_fails.py`.

**Risks.**
- *Non-deterministic encoder output* (timestamps, encoder version strings in metadata) →
  bitexact flags plus post-generation checksum verification; if a fixture cannot be made
  deterministic, it is checksum-pinned to a recorded encoder version and that version is
  documented.
- *256 GB YouTube boundary is impractical to generate.* → Use a sparse/synthetic strategy
  or, if infeasible, cover that rule with a unit test against a synthetic
  `NormalisedMedia` rather than real media, and **record the deviation explicitly**. Do
  not silently skip it.
- *Corpus generation time.* → Fixtures are seconds long and tiny; generation is a
  one-time, cached step.

**Rework trigger.** Any preset rule change requires a corresponding fixture review;
P9-A2's coverage check makes this mechanical.

**Parallelizable.** Partially — the manifest can be drafted alongside Phase 4.

---

## 11. PHASE 10 — INTEGRATION AND ROBUSTNESS TESTING

**Objective.** Every row of the spec §23 failure table and every acceptance criterion in
spec §25 has a passing end-to-end test through the real application path.

**Depends on.** Phases 4–9.

**Modules.**

```
tests/integration/test_failure_matrix.py     one test per spec §23 row
tests/integration/test_acceptance_criteria.py one test per spec §25 AC where automatable
tests/integration/test_end_to_end.py         add -> select -> run -> report
tests/integration/fixtures/hostile/          adversarial inputs
tools/fault_injection.py                     stub inspectors: hang, crash, garbage, partial
```

**Deliverables.**

1. A fault-injection harness providing stub inspectors that hang, crash, exit non-zero,
   emit malformed JSON, emit valid-but-empty JSON, emit enormous output, and emit
   partially-valid output.
2. One test per spec §23 row, exercised through the orchestrator, not the adapter in
   isolation.
3. Hostile-input fixtures: filenames with quotes, spaces, `%`, `&`, `;`, `|`, newlines,
   Unicode, right-to-left marks, and reserved Windows device names (`CON`, `NUL`,
   `LPT1`); paths at and beyond `MAX_PATH`; a file replaced with a different file
   mid-batch; a file locked by another process.
4. Soak test: a 1000-file mixed batch, asserting no orphan processes, no unbounded memory
   growth, and completion.
5. An automated map from each spec §25 acceptance criterion to its covering test, so
   uncovered criteria are visible.

**Acceptance.**

| # | Criterion |
| --- | --- |
| P10-A1 | Every spec §23 row has a passing test. (Spec AC-15.) |
| P10-A2 | Every automatable spec §25 criterion has a passing test; manual-only criteria (AC-17, AC-20) are listed for Phase 13. |
| P10-A3 | A filename containing shell metacharacters is handled correctly — **and is never interpreted**, proving argv-list invocation. |
| P10-A4 | A 1000-file batch completes with zero orphan processes and bounded memory. |
| P10-A5 | A file locked by another process yields `NOT_INSPECTED`, not a crash. |
| P10-A6 | Coverage over `core/`, `normalise/`, `rules/`, `results/`, `reporting/` is ≥ 90% line and ≥ 85% branch. UI coverage is explicitly excluded from the threshold. |
| P10-A7 | The whole suite passes with network access blocked. |
| P10-A8 | The whole suite passes with `PYTHONHASHSEED` randomised across 5 runs. |

**Risks.**
- *Chasing UI coverage.* → Explicitly excluded from the threshold; correctness lives below
  the UI.
- *Flaky timing tests.* → Timeouts are injected, not real-clock dependent.

**Rework trigger.** A new spec §23 row.

**Parallelizable.** No — it integrates everything.

> **GATE-4 fires at the end of this phase.** See §16.

---

## 12. PHASE 11 — WINDOWS PACKAGING

**Objective.** A signed, installable Windows package that runs on a clean machine under a
standard user account, with correctly laid out third-party binaries.

**Depends on.** Phases 6–10.

**Modules.**

```
packaging/build.py                   orchestrates the whole build
packaging/preflightqc.spec           PyInstaller one-dir spec
packaging/installer.iss              Inno Setup script
packaging/fetch_binaries.py          pinned-URL + checksum download of ffprobe/MediaInfo
packaging/binaries.lock.json         pinned versions, URLs, SHA-256
packaging/sign.py                    Authenticode signing of app, binaries, installer
packaging/layout_check.py            asserts the shipped tree matches ADR-001 §5
```

**Deliverables.**

1. A one-dir PyInstaller build (**never one-file** — required for the LGPL
   shared-library posture).
2. `fetch_binaries.py` downloading only from pinned official URLs, verifying SHA-256
   against `binaries.lock.json`, and **failing hard on mismatch**.
3. The exact layout from ADR-001 §5, with `bin/` holding `ffprobe.exe`, the `libav*` DLLs,
   and MediaInfo — **all unobfuscated, all unmodified**.
4. An Inno Setup installer, per-user by default, installing and running without
   administrator rights.
5. Authenticode signing of the application, first-party binaries, and installer.
   Third-party DLLs may be re-signed but **must not be modified**.
6. `layout_check.py` asserting: no `ffmpeg.exe`; no prohibited component; no obfuscated
   DLL name; `licenses/` present and populated.

**Acceptance.**

| # | Criterion |
| --- | --- |
| P11-A1 | The build is reproducible from a clean checkout plus `binaries.lock.json`. |
| P11-A2 | A checksum mismatch in `fetch_binaries.py` **fails the build**, never warns. |
| P11-A3 | The shipped tree matches ADR-001 §5 exactly; `layout_check.py` passes. |
| P11-A4 | **No `ffmpeg.exe`** is present anywhere in the package. |
| P11-A5 | No prohibited GPL/nonfree component is present. |
| P11-A6 | All shared-library filenames are unobfuscated. |
| P11-A7 | The installer installs per-user without administrator rights. |
| P11-A8 | Application, first-party binaries and installer are Authenticode-signed; `signtool verify` passes on each. |
| P11-A9 | The packaged app resolves inspectors by absolute path under `bin/` and never consults `PATH`. Re-verified on the packaged build. |
| P11-A10 | Total package size is recorded and reported. |

**Risks.**
- *PyInstaller misses a PySide6 plugin* (image formats, platform plugin) → caught by
  Phase 13 clean-machine validation, not by a developer machine that has Qt installed.
- *Code-signing certificate unavailable* → an operator prerequisite; flag early, do not
  ship unsigned.
- *Antivirus false positive on the PyInstaller bootloader* → known risk; mitigation is
  signing plus, if needed, vendor submission. Record if it occurs.

**Rework trigger.** Stack change; inspector version change.

**Parallelizable.** No.

---

## 13. PHASE 12 — DEPENDENCY AND LICENSING AUDIT

**Objective.** The release package satisfies every licensing gate in spec §26.1 plus
G-13, with a generated dependency manifest and third-party notices that provably match
the package contents.

**Depends on.** Phase 11.

**Modules.**

```
packaging/generate_manifest.py       scans the built package -> DEPENDENCY-MANIFEST.json
packaging/generate_notices.py        manifest + licence texts -> THIRD-PARTY-NOTICES.txt
packaging/scan_prohibited.py         scans binaries for prohibited components
licenses/                            LGPL-2.1, LGPL-3.0, BSD-2-Clause, PSF, zlib, ...
docs/licensing/EULA-DRAFT.md         with the required carve-outs
```

**Deliverables.**

1. `DEPENDENCY-MANIFEST.json` **generated from the actual built package** — never
   hand-maintained — listing every component with name, exact version, exact build
   identifier, licence, official source URL, and SHA-256 of the shipped file.
2. `THIRD-PARTY-NOTICES.txt` generated from the manifest, with the correct notice form per
   licence, including:
   - *"This software uses libraries from the FFmpeg project under the LGPLv2.1"*
   - Full LGPL-2.1 text
   - A statement that PreflightQC does not own FFmpeg
   - The exact configure line / build variant of the shipped ffprobe
   - A same-server link to version-matched corresponding FFmpeg source
   - *"This product uses MediaInfo library, Copyright (c) 2002-2026 MediaArea.net SARL"*
     plus BSD-2-Clause text
   - ZenLib zlib attribution
   - IJG credit **if** libjpeg-derived files are present in the shipped build
   - PySide6 / Qt LGPLv3 notice and full LGPL-3.0 text (**if** the ADR-001 primary stack
     is in force)
   - Notices for every other shipped runtime dependency
3. `scan_prohibited.py` inspecting the shipped ffprobe's reported configuration and the
   binary contents for every prohibited component, **failing the build** on any hit.
4. An archived copy of the exact FFmpeg source tarball and build configuration that
   produced the shipped binaries, plus a hosting plan for same-server availability.
5. `EULA-DRAFT.md` containing: no reverse-engineering prohibition conflicting with LGPL
   rights (or an explicit carve-out); a disclaimer of FFmpeg ownership; naming of FFmpeg
   and the LGPL 2.1; and a note that all translations require the same edits.
6. A staleness report flagging any preset rule whose source has not been re-verified
   within 6 months.

**Acceptance — the spec §26.1 gates, mechanised.**

| Gate | Criterion |
| --- | --- |
| G-1 | Manifest is complete and every entry's checksum matches the shipped file. |
| G-2 | Notices cover every manifest entry with the correct notice form. |
| G-3 | Prohibited-component scan is clean. (Spec AC-19.) |
| G-4 | The shipped ffprobe's reported configuration contains no `--enable-gpl` and no `--enable-nonfree`; output captured verbatim. |
| G-5 | Version-matched FFmpeg source is archived and a same-server hosting location is confirmed. |
| G-6 | The configure line / build recipe for the exact shipped build is recorded and shipped. |
| G-7 | DLL names are unobfuscated. |
| G-8 | The EULA draft carries all required carve-outs; translation requirement recorded. |
| G-9 | MediaInfo BSD-2-Clause attribution and ZenLib zlib notice present; the third-party list matches the shipped MediaInfo's actual compiled feature set (verified — not assumed — including whether libcurl is present). |
| G-10 | Every third-party binary's official-source URL and published checksum are recorded and verified. |
| G-11 | Authenticode signatures verified. |
| **G-13** | The GUI-framework licence posture is documented and satisfied: if LGPLv3 Qt ships, the shared-library mechanism is demonstrated (Qt libraries present as separate, unobfuscated, replaceable files) and LGPL-3.0 text plus notices ship. |

**Blocking, non-automatable.**

| Gate | Criterion |
| --- | --- |
| **G-12** | **Owner licensing & compliance risk acceptance** *(amended 2026-08-09 by SPEC LOCK v1.1.0; was: attorney review — `docs/decisions/ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md`)*. Manifest complete, notices present, source obligations prepared, EULA present, unresolved legal questions documented, and the Product Owner's written residual-risk acceptance for the specific release. No document in this repository claims legal clearance, and no attorney review occurred. The acceptance itself cannot be satisfied by any engineering artefact. |

**Risks.**
- *Manifest drift.* → Eliminated by generating it from the package.
- *A transitive Python dependency with an unexpected licence.* → The generator enumerates
  the frozen environment, not `requirements.in`.
- *G-12 turnaround time.* → Originally: start attorney engagement at GATE-3, not at
  Phase 12. Superseded 2026-08-09: the amended G-12 (owner risk acceptance, ADR-G12)
  has no external turnaround; the schedule risk it addressed no longer applies, and the
  engagement it called for did not occur.

**Rework trigger.** Any dependency, version, or build-variant change.

**Parallelizable.** No.

> **GATE-5 fires at the end of this phase.** See §16.

---

## 14. PHASE 13 — CLEAN-MACHINE RELEASE VALIDATION

**Objective.** Prove on real, clean Windows 10 and Windows 11 x64 machines that the
signed installer produces a working product for a user who has none of the developer's
environment.

**Depends on.** Phases 11, 12.

**Prerequisites.** Clean Windows 10 x64 and Windows 11 x64 VMs or machines with: no
Python, no FFmpeg, no MediaInfo, no Visual C++ redistributable beyond a stock image, no
developer tooling. A standard (non-administrator) user account. SmartScreen enabled.

**Deliverables.**

1. A written validation run-book with pass/fail per step.
2. Execution on both Windows 10 and Windows 11.
3. Results recorded in `docs/planning/RELEASE-VALIDATION-V1.md`.

**Acceptance — every manual criterion the automated suite cannot cover.**

| # | Criterion |
| --- | --- |
| P13-A1 | The installer runs under a standard user account without an administrator prompt. |
| P13-A2 | SmartScreen does not block the signed installer (or the observed behaviour is recorded and accepted). |
| P13-A3 | The application launches on a machine with no Python and no pre-installed inspector. |
| P13-A4 | The startup self-check passes and reports both inspector versions. |
| P13-A5 | An ffprobe planted on the machine's `PATH` is **never** invoked. (Spec AC-17.) |
| P13-A6 | Drag-and-drop, file picker and folder picker all work. |
| P13-A7 | A representative batch produces the same results as the golden corpus run on the development machine. |
| P13-A8 | CSV and HTML export succeed to a user-writable location. |
| P13-A9 | The full cycle completes with the machine's outbound network blocked at the firewall. (Spec AC-12.) |
| P13-A10 | The About screen renders notices and licence texts offline. |
| P13-A11 | Custom profile create / save / restart / reload works under a standard account. |
| P13-A12 | Uninstall removes the application and leaves user profiles and config intact (documented behaviour either way). |
| P13-A13 | Source video files on the test machine are unmodified after the batch (bytes, size, mtime). |
| P13-A14 | Both Windows 10 and Windows 11 pass the whole run-book. |

**Risks.**
- *A missing runtime DLL only visible on a clean machine.* → Exactly what this phase
  exists to catch.
- *SmartScreen reputation for a new certificate.* → Known; record the observed behaviour
  and the mitigation plan rather than treating it as a blocker for correctness.

**Rework trigger.** Any failure returns to Phase 11 or 12.

**Parallelizable.** No — the final phase.

> **GATE-6 fires at the end of this phase.** See §16.

---

## 15. CRITICAL PATH

```
P0 ──► P1 ──► P2 ──► P3 ──┬──► P4 ─────────┐
 repo   spike  model  engine │  presets      │
                             │               ├──► P9 ──► P10 ──► P11 ──► P12 ──► P13
                             ├──► P5 ────────┤   golden  integr  packag  licence clean
                             │  orchestration│
                             │               │
                             └──► P6 ──┬─────┘
                                UI     │
                                       ├──► P7  profiles
                                       └──► P8  reporting
```

**The critical path is:**

```
P0 → P1 → P2 → P3 → P4 → P9 → P10 → P11 → P12 → P13
```

### 15.1 Why this is the critical path

The product's value is **correct findings**. Everything on the path either establishes
what can be measured (P1, P2), how it is judged (P3), what the judgements are (P4), or
proves the judgements are right (P9, P10) — then ships it compliantly (P11–P13).

**P3 → P4 → P9 is the heart of the product.** The severity guard (P3), the preset data
(P4), and the boundary corpus (P9) together are what distinguish PreflightQC from a
checklist blog post. If schedule pressure appears, it must not fall here.

### 15.2 Off-path work

| Phase | Can run concurrently with | Slack |
| --- | --- | --- |
| P5 orchestration | P4 | Needed by P9; moderate slack |
| P6 UI | P4, P5 (after the orchestrator interface freezes) | Blocked by GATE-3 |
| P7 profiles | P8 | Needed only by P10 |
| P8 reporting | P7 | Needed only by P10 |

### 15.3 Cheapest reversals, most expensive reversals

| Reversal | Cost |
| --- | --- |
| Preset value correction (P4) | **Cheap** — data only, no code change. This is the whole point of the data-driven design. |
| Adding a rule for a newly published platform requirement | **Cheap** — register row + preset rule + boundary fixtures. |
| MediaInfo CLI ↔ library (Q-3) | **Moderate** — one adapter, if decided by end of P1. |
| GUI framework reversal (Q-1) | **Moderate if before P6, expensive after P11.** This is why GATE-3 precedes P6. |
| Severity-model change | **Very expensive** — touches the spec, engine, every preset, and the whole corpus. Hence SPEC LOCK. |
| Inspection architecture change (§10) | **Very expensive and locked.** |

---

## 16. STOP / GATE CONDITIONS

Gates are **blocking**. Execution stops, the condition is reported, and work does not
continue past the gate until it is resolved by an explicit decision.

### 16.1 Phase gates

| Gate | After | Condition to pass | If it fails |
| --- | --- | --- | --- |
| **GATE-1** | P1 | The obtained ffprobe build is confirmed **LGPL shared**, with no `--enable-gpl`, no `--enable-nonfree`, and none of the prohibited components. Both inspector versions and checksums recorded. | **STOP.** Do not build on a non-conforming binary. Report and request a conforming build. |
| **GATE-2** | P3 | The severity guard rejects every (RECOMMENDATION\|BEST_PRACTICE\|ELIGIBILITY × FAIL) combination, and the overall-status truth table is exhaustively correct. | **STOP.** The severity invariant is the product. Do not proceed to preset data with a permissive engine. |
| **GATE-3** | Before P6 | ADR-001 Q-1 resolved: bundling the chosen GUI framework in a closed-source commercial product is acceptable, or the fallback stack is adopted. | **STOP.** Do not build a UI on a framework that may have to be replaced after packaging. |
| **GATE-4** | P10 | Every spec §23 row and every automatable spec §25 criterion passes. | **STOP.** Do not package a product with unproven failure handling. |
| **GATE-5** | P12 | All of G-1…G-11 and G-13 pass automatically. **G-12 is initiated** — under the amended gate (ADR-G12), the unresolved-questions documentation exists. | **STOP.** Do not proceed to release validation. |
| **GATE-6** | P13 | The full clean-machine run-book passes on both Windows 10 and Windows 11, **and G-12 is complete** — under the amended gate, the owner's written risk acceptance for this release exists. | **STOP.** Not releasable. |

### 16.2 Standing stop conditions

Execution stops immediately, at any point, if any of these becomes true:

| # | Condition |
| --- | --- |
| S-1 | A change would require a rule classified `RECOMMENDATION`, `BEST_PRACTICE`, or `ELIGIBILITY` to emit `FAIL`. |
| S-2 | A rule value is needed that has no row in `docs/sources/SOURCE-REGISTER.md`. |
| S-3 | Missing or undeterminable metadata would produce `FAIL`. |
| S-4 | A GPL or nonfree component would enter the build. |
| S-5 | An `ffmpeg` encoder binary would be bundled. |
| S-6 | Any code path would make a network call at runtime. |
| S-7 | Any code path would open a source video file for writing. |
| S-8 | A dependency would be added that imposes copyleft on PreflightQC's own source. |
| S-9 | A conflicting specification would be silently resolved rather than surfaced. |
| S-10 | The plan is ambiguous about **what the product should do** (as opposed to how to build it). |
| S-11 | A spec §20 non-goal would be implemented. |
| S-12 | Any claim of legal clearance would be made. |
| S-13 | The forbidden claim language of spec §4.1 would appear in UI, report, or documentation. |

### 16.3 Reporting at each gate

At every gate, report: phase, acceptance results (pass/fail per criterion), files created
and modified, decisions made, open questions, blockers, and `SPEC DEVIATIONS = NONE` or an
explicit list.

---

## 17. WORK NOT IN ANY PHASE

Deliberately excluded from V1 execution, recorded so no session adds them:

| Item | Why | Where it goes |
| --- | --- | --- |
| macOS build | Spec §20, §22.8 | `docs/FUTURE.md` |
| Licence key / activation | Spec §20, §28.2 | `docs/FUTURE.md` |
| Payment provider integration | Spec §28.3 | `docs/FUTURE.md` |
| Auto-updater | Spec §19 | `docs/FUTURE.md` |
| Preset auto-update | Spec §19 | `docs/FUTURE.md` |
| Loudness measurement (LUFS) | Spec §20.1, gap G-4 | `docs/FUTURE.md` |
| YouTube metadata (title/description/tags) validation | Spec §20.1 | `docs/FUTURE.md` |
| GOP / closed-GOP verification | Gap G-2, spec §10.5 | `docs/FUTURE.md` |
| Persistent cross-run cache | `ARCHITECTURE-V1.md` §20 | `docs/FUTURE.md` |
| Plugin system | Presets are the extension point | `docs/FUTURE.md` |
| Additional TikTok / Meta ad presets | Source gaps; see register §1.5, §2.6 | `docs/FUTURE.md` |

---

## 18. PHASE SUMMARY

| Phase | Name | Depends on | Parallelizable | Gate |
| --- | --- | --- | --- | --- |
| 0 | Repository, spec and source normalisation | — | No | — |
| 1 | Inspector technical spike | 0 | No | **GATE-1** |
| 2 | Normalised metadata model | 1 | No | — |
| 3 | Rule and preset engine | 2 | No | **GATE-2** |
| 4 | Platform preset data | 3 | Yes (with 5, 6) | — |
| 5 | Adapters and batch orchestration | 2, 3 | Yes (with 4) | — |
| 6 | Desktop UI | 4, 5 | Partially | preceded by **GATE-3** |
| 7 | Custom client profiles | 3, 6 | Yes (with 8) | — |
| 8 | Reporting | 3, 5, 6 | Yes (with 7) | — |
| 9 | Golden test corpus | 2, 3, 4, 5 | Partially | — |
| 10 | Integration and robustness testing | 4–9 | No | **GATE-4** |
| 11 | Windows packaging | 6–10 | No | — |
| 12 | Dependency and licensing audit | 11 | No | **GATE-5** |
| 13 | Clean-machine release validation | 11, 12 | No | **GATE-6** |
