# PREFLIGHTQC — V1 ARCHITECTURE

| Field | Value |
| --- | --- |
| Status | Proposed. Subordinate to `docs/specification/PREFLIGHTQC-V1-SPEC.md`. |
| Date | 2026-08-09 |
| Stack | See `ADR-001-TECH-STACK.md` (PROPOSED) |

This document describes structure and boundaries. It does not prescribe implementation
detail beyond what the boundaries require. It **does not prematurely optimise**: the
concurrency model, caching, and data structures described here are the simplest ones that
satisfy the specification, and nothing more.

---

## 1. LAYERS

```
┌──────────────────────────────────────────────────────────────────────┐
│  L6  UI LAYER                        Qt Widgets. The only Qt code.   │
│      windows, views, dialogs, drag-drop, progress, preset selector   │
└───────────────▲──────────────────────────────────┬───────────────────┘
                │ view models / signals            │ commands
┌───────────────┴──────────────────────────────────▼───────────────────┐
│  L5  APPLICATION / ORCHESTRATION                                     │
│      batch runner, job queue, cancellation, progress aggregation     │
└───────────────▲──────────────────────────────────┬───────────────────┘
                │                                  │
┌───────────────┴──────────────┐   ┌───────────────▼───────────────────┐
│  L4  REPORTING               │   │  L3  VALIDATION                   │
│      CSV writer              │   │      rule engine, severity guard, │
│      HTML renderer           │   │      result aggregation           │
│      summary builder         │   └───────────────▲───────────────────┘
└──────────────────────────────┘                   │
                                   ┌───────────────┴───────────────────┐
                                   │  L2  NORMALISATION                │
                                   │      raw inspector output ->      │
                                   │      normalised metadata model    │
                                   └───────────────▲───────────────────┘
                                                   │
                                   ┌───────────────┴───────────────────┐
                                   │  L1  INSPECTION ADAPTERS          │
                                   │      ffprobe adapter              │
                                   │      MediaInfo adapter            │
                                   └───────────────▲───────────────────┘
                                                   │
┌──────────────────────────────────────────────────┴───────────────────┐
│  L0  PLATFORM BOUNDARY                                               │
│      process runner, filesystem access, paths, config, logging       │
└──────────────────────────────────────────────────────────────────────┘

              ┌───────────────────────────────────────┐
              │  PRESET / PROFILE STORE (data)        │
              │  shipped presets  +  custom profiles  │
              └───────────────────────────────────────┘
                        consumed by L3, edited via L6
```

### 1.1 Dependency rule

Dependencies point **downward only**. Specifically:

| Layer | May import | Must never import |
| --- | --- | --- |
| L6 UI | L5, and read-only view types from L3/L4 | — |
| L5 Orchestration | L1–L4, L0 | **Qt** |
| L4 Reporting | L3 result types, L0 | **Qt**, L1, L5 |
| L3 Validation | L2 model types, preset store, L0 | **Qt**, L1, L4, L5 |
| L2 Normalisation | L1 raw types, L0 | **Qt**, L3, L4, L5 |
| L1 Adapters | L0 | **Qt**, L2–L5 |
| L0 Platform | stdlib only | **Qt**, everything above |

**"No Qt below L6" is an enforced invariant**, verified by an automated import-boundary
test. It is what makes the ADR-001 fallback (swap the UI framework) affordable, and it is
what makes the engine testable headlessly.

Preset data is a **leaf**: it imports nothing and is imported by L3 and L6.

---

## 2. UI LAYER (L6)

### 2.1 Capabilities

| Capability | Consumes | Emits |
| --- | --- | --- |
| **Input surface** — drag-drop target, "Add files…", "Add folder…", recurse toggle | — | `AddPathsCommand(paths, recurse)` |
| **File list / batch table** — virtualised, one row per file: name, status badge, counts by severity, progress | `BatchViewModel` (immutable snapshots) | `RemoveFileCommand`, `SelectFileCommand` |
| **Preset selector** — grouped by platform family, showing preset name, rule-set version, last-verified date, and any preset caveat text | `PresetCatalogViewModel` | `SelectPresetCommand(preset_id)` |
| **Run / Cancel control** | `BatchState` | `StartBatchCommand`, `CancelBatchCommand` |
| **Progress surface** — overall bar, "n of m", in-flight count | `BatchProgress` | — |
| **Findings detail pane** — for the selected file: ordered findings, each with severity, property, detected, expected, explanation, source link, rule id, inspector provenance | `FileResultViewModel` | — |
| **Metadata inspector pane** — the full normalised model for the selected file, with per-field provenance and `NOT_PRESENT` / `UNDETERMINED` / `CONFLICTED` states shown explicitly | `NormalisedMetadataViewModel` | — |
| **Batch summary bar** — PASS / WARN / FAIL / NOT_INSPECTED / NOT_APPLICABLE counts | `BatchSummary` | — |
| **Export dialog** — format (CSV / HTML), destination | `BatchResult` | `ExportReportCommand(format, path)` |
| **Custom profile editor** — the §16.1 property set, each with required/recommended toggle | `CustomProfile` | `SaveProfileCommand`, `DeleteProfileCommand`, `ImportProfileCommand`, `ExportProfileCommand` |
| **About / notices** — version, inspector versions, third-party notices, LGPL text — all offline | `AboutInfo` | — |

### 2.2 UI rules

1. The UI owns no domain logic. It renders view models and emits commands.
2. **All view models are immutable snapshots.** The orchestrator publishes a new snapshot;
   the UI diffs and re-renders. No shared mutable state across threads.
3. The UI thread never performs file I/O, never spawns a process, and never blocks.
4. Severity is rendered from a single mapping table (colour, icon, label). No severity
   string is hard-coded in a widget.
5. No platform-specific number, threshold, or rule text appears anywhere in L6. All such
   text originates in preset data (spec §11.1).
6. Findings render in the deterministic order produced by L3 (spec §15). The UI must not
   re-sort by default.

---

## 3. BATCH ORCHESTRATION (L5)

### 3.1 Model

```
Batch
 ├─ batch_id, created_at, preset_id, ruleset_version
 ├─ Job[]            one per input file
 │    ├─ path, size, mtime            (identity, captured at enqueue)
 │    ├─ state  QUEUED → INSPECTING → VALIDATING → DONE | FAILED | CANCELLED
 │    └─ result FileResult | InspectionFailure
 └─ BatchSummary     derived, never stored redundantly
```

### 3.2 Pipeline

```
enumerate → dedupe → enqueue
    ↓
  [worker pool]  inspect (L1) → normalise (L2) → validate (L3)
    ↓
  publish FileResult → aggregate summary → notify UI
```

### 3.3 Rules

1. **Per-file isolation.** Every job is executed inside a boundary that converts *any*
   exception into an `InspectionFailure` with a cause. No exception escapes a job.
   (Spec §13.3.)
2. **Results stream.** A `FileResult` is published as soon as its job completes. The UI
   does not wait for the batch.
3. **Presentation order is input order**, independent of completion order (spec §13.8).
4. **Cancellation** sets a cooperative flag checked between pipeline stages, and signals
   the process runner to terminate in-flight children with a bounded grace period.
   Completed results are preserved; the batch is marked `partial`.
5. **Re-validation without re-inspection.** Inspection output is cached per job keyed on
   `(absolute_path, size, mtime_ns)`. Changing the preset re-runs L2→L3 only. The cache
   is session-scoped and in-memory; it is not persisted in V1.
6. **Enumeration is a job too** — it runs off the UI thread and is cancellable, because a
   deep folder on a slow network share must not freeze the application (spec §8.2).

### 3.4 Concurrency strategy

- A `ThreadPoolExecutor` with `max_workers = min(4, os.cpu_count())`, configurable.
- Threads are appropriate because the work is **process-spawn + I/O bound**, not CPU
  bound. The GIL is released during `subprocess` waits and file reads.
- **Bounded, not maximal.** Spawning one inspector per core on a 32-core machine would
  thrash a spinning disk or a network share for no gain. 4 is the default; the setting
  exists so it can be tuned with evidence, not guessed now.
- Determinism does not depend on worker count: workers produce results, ordering is
  imposed at presentation and aggregation.

---

## 4. INSPECTION ADAPTERS (L1)

### 4.1 Contract

Both adapters implement the same shape:

```
inspect(path, timeout) -> InspectorOutcome
    InspectorOutcome = Success(raw: dict, tool_version: str, duration_ms: int)
                     | Failure(kind, message, exit_code?, stderr_excerpt?)

    kind ∈ { NOT_FOUND, LAUNCH_FAILED, TIMEOUT, CRASHED, BAD_EXIT,
             MALFORMED_OUTPUT, FILE_UNREADABLE, PERMISSION_DENIED, CANCELLED }
```

An adapter **never raises** to its caller and **never** returns partially-parsed data
without saying so.

### 4.2 ffprobe adapter

- Invoked by **absolute path** to the bundled binary. `PATH` is never consulted
  (spec §22.4).
- Base invocation: `-v error -print_format json -show_format -show_streams -show_error`.
- Optional bounded HDR pass, behind an explicit setting:
  `-show_frames -read_intervals "%+#1" -select_streams v:0`. This is the **only**
  operation that engages the decoder, and it reads at most one frame (spec §10.5).
- Output is read from stdout with a size cap; stderr is captured separately and truncated
  for diagnostics.
- Non-zero exit with parseable `error` JSON is a structured failure, not a crash.

### 4.3 MediaInfo adapter

- JSON output (`--Output=JSON` for the CLI, or `Option("Output","JSON")` for the library).
- **The CLI-vs-library choice is deferred to the Phase 1 spike** (ADR-001 Q-3). The
  adapter interface is identical either way, so the decision does not propagate.
- **Current recommendation: CLI subprocess.** Rationale: PreflightQC ingests untrusted
  customer files, and an in-process parser crash or hang would take down the application.
  The MediaInfo research explicitly names subprocess isolation as a genuine
  security/stability advantage for exactly this case. Uniform process handling with the
  ffprobe adapter (one timeout mechanism, one kill path, one failure taxonomy) is also
  simpler than maintaining two. Spawn cost is amortised across a batch and is not the
  bottleneck. The spike measures this and may overturn it.
- Never the GUI. Never a libcurl-enabled build (spec §10.3).

### 4.4 Process runner (L0)

One implementation, used by both adapters:

- Spawns with no shell, no inherited console window, explicit `cwd`, and a minimal
  environment.
- Enforces a **per-call timeout**. On expiry, terminates the **whole process tree** and
  reports `TIMEOUT`.
- Caps stdout and stderr sizes to prevent a pathological file producing unbounded output.
- Reaps children on cancellation and on application shutdown. **No orphan processes.**
- Never raises; returns a structured outcome.

---

## 5. NORMALISED METADATA MODEL (L2)

### 5.1 Three-valued fields

Every field is one of:

```
Known(value, provenance)     a determined value, and where it came from
NotPresent(provenance)       the property is genuinely absent from the file
Undetermined(reason)         the inspectors could not determine it
Conflicted(a, b)             both inspectors reported it and disagreed
```

**There is no fourth state and no default.** A missing bitrate is `NotPresent`, never
`0`. This is the mechanical guarantee behind spec §7.1 ("never treat unavailable metadata
as failure") — the rule engine cannot accidentally compare against a fabricated zero
because no fabricated zero exists.

`provenance` records the inspector, its version, and the raw field path
(e.g. `ffprobe:streams[0].pix_fmt`). Derived values carry `derived_from=[...]` and are
flagged as derived (spec §9.6.4).

### 5.2 Shape

```
NormalisedMedia
 ├─ file       name, path, size, duration, mtime
 ├─ container  format, long_name, major_brand, compatible_brands, tags,
 │             stream_count, stream_counts_by_type, overall_bitrate,
 │             faststart, edit_lists_present
 ├─ video[]    (primary = index 0; all enumerated)
 │             codec, profile, level, width, height, coded_width, coded_height,
 │             sar, dar, dar_displayed, rotation, frame_rate, frame_rate_mode,
 │             bitrate, bitrate_source, pixel_format, bit_depth,
 │             chroma_subsampling, scan_type, field_order, colour_range,
 │             colour_space, transfer_characteristics, colour_primaries,
 │             gop_closed, hdr_format, dolby_vision, mastering_display,
 │             max_cll, max_fall
 ├─ audio[]    (primary = index 0; all enumerated)
 │             present, codec, sample_rate, channels, channel_layout, bitrate
 └─ diagnostics  inspector outcomes, tool versions, conflicts, timings
```

### 5.3 Normalisation rules

1. **Precedence is data.** A per-field precedence table (from source register §5) decides
   which inspector wins. It is a table, not a chain of conditionals.
2. **Disagreement is preserved.** Where both inspectors report a field with different
   values, the field becomes `Conflicted`. A `Conflicted` field can produce at most a
   `WARN`, plus an `INFO` finding stating both values (spec §10.4).
3. **Vocabulary is canonicalised** through explicit lookup tables:
   `pix_fmt → (chroma_subsampling, bit_depth)`, `container name set → canonical
   container`, `codec name/tag → canonical codec`. Unmapped inputs become `Undetermined`
   with the raw value retained — **never** silently coerced.
4. **Rationals stay rational.** Frame rate is kept as an exact `Fraction`
   (e.g. `24000/1001`) and only converted to a float at comparison time, with an explicit
   tolerance. This prevents 29.97 ≠ 29.97 defects.
5. **Displayed geometry is computed**: `dar_displayed` applies SAR *and* rotation. Rules
   about aspect ratio evaluate against displayed geometry; coded dimensions are retained
   separately.
6. **Bitrate records its source** (`stream` / `container` / `computed`) so a report never
   implies a measured value that was actually derived.
7. **Primary stream selection** is the first video stream and the first audio stream, with
   an `INFO` finding when more than one exists (spec §23).

---

## 6. RULE ENGINE (L3)

### 6.1 Structure

```
PresetDocument (data)
 ├─ preset_id, platform, display_name, description, caveats[]
 ├─ ruleset_version, last_verified_date
 ├─ sources[]   { source_ref, title, url, access_date, confidence }
 └─ rules[]     per spec §11.2

Engine
 ├─ load(preset)     → schema validate → severity guard → resolve property paths
 ├─ evaluate(media, preset) → Finding[]
 └─ aggregate(Finding[]) → FileResult
```

### 6.2 Load-time validation (fail closed)

A preset is rejected — wholly, never partially (spec §23) — if any of:

- It fails JSON Schema validation.
- A `property` path does not exist in the normalised model.
- An `operator` is unknown.
- An `expected` value's shape does not match the operator.
- **A rule's `severity` exceeds the ceiling its `classification` permits** (spec §7.3).
  This is the single most important check in the system.
- A rule lacks `source_ref`, `confidence`, or `last_verified_date`.
- `rule_id` is not unique within the preset.

Rejection produces an actionable message naming the preset and the offending rule. Other
presets remain usable.

### 6.3 Evaluation

For each enabled rule, in `rule_id` order:

```
1. if applies_when is present and evaluates false  → SKIP (no finding, or INFO)
2. resolve rule.property against the normalised model
3. if the resolved field is NotPresent or Undetermined
       → emit UNKNOWN finding, stating why. NEVER FAIL.
4. if the resolved field is Conflicted
       → emit INFO finding with both values; evaluate against the
         more permissive value; cap resulting severity at WARN
5. apply operator(actual, expected, tolerance)
6. on pass → PASS finding (retained for INFO-level reporting)
   on fail → finding at rule.severity, bounded by the §7.3 ceiling
7. attach: detected value + units, expected value + units, explanation,
   source_ref, confidence, last_verified_date, rule_id, provenance
```

### 6.4 Engine invariants

| Invariant | Why |
| --- | --- |
| The engine contains **no platform name and no platform number** | Spec §11.1, §11.3.2 |
| Rules are **independent**; no rule reads another's result | Spec §11.3.6 |
| Evaluation is **pure**: `(media, preset) → findings`, no I/O, no clock, no locale, no randomness | Determinism (spec §11.3.1) |
| Comparison uses **explicit tolerances**, never bare float equality | 29.97 / 23.976 correctness |
| A guard evaluating false **skips**, never fails | Spec §11.3.5 |
| Severity is **bounded at load**, so it cannot be violated at evaluation time | Spec §7.3 |

### 6.5 Operators

`eq`, `neq`, `in`, `not_in`, `range` (inclusive, `{min,max}`, either bound optional),
`lt`, `lte`, `gt`, `gte`, `present`, `absent`, `matches` (anchored regex),
`constant_only` (for CFR requirements).

Each operator declares the value shapes it accepts. Numeric operators accept an optional
`tolerance` (absolute or fractional, declared explicitly).

---

## 7. PRESET STORAGE

| Aspect | Decision |
| --- | --- |
| Format | JSON, one document per preset, validated against `preset.schema.json` |
| Location (shipped) | `presets/` inside the application directory, **read-only** |
| Location (custom) | `%LOCALAPPDATA%\PreflightQC\profiles\` |
| Loading | All presets loaded and validated at startup; failures are reported and the preset is excluded, not silently skipped |
| Versioning | Each document carries `ruleset_version` and `last_verified_date`, printed on every report |
| Namespacing | Shipped `preset_id`s are reserved; a custom profile cannot shadow one |

Shipped presets are **never** written to by the application. A user cannot edit a
platform preset; they can only create a custom profile.

---

## 8. CUSTOM PROFILE STORAGE

- One JSON file per profile in `%LOCALAPPDATA%\PreflightQC\profiles\`, filename derived
  from a generated id (not the display name — display names are not path-safe and are not
  unique).
- The **same document format** as a shipped preset, with `origin: "custom"`, a display
  name, optional client/notes, and created/modified dates.
- Authored through the editor (spec §16.1 property set only). Each property the user
  configures becomes one rule, classified `HARD_REQUIREMENT` when marked *required* and
  `RECOMMENDATION` when marked *recommended* — which satisfies the §7.3 guard without
  weakening it.
- **Unconfigured properties produce no rules.** They are not checked and do not default.
- Export = copy the file. Import = validate, then copy in, with a new id on collision.
- Writes are **atomic**: write to a temp file in the same directory, `fsync`, then
  replace. A crash mid-save must never corrupt an existing profile.
- Reports from a custom profile print the **profile name**, never a platform name
  (spec §16.5).

---

## 9. RESULT AGGREGATION

```
FileResult
 ├─ job identity (path, size, mtime)
 ├─ overall  PASS | WARN | FAIL | NOT_INSPECTED | NOT_APPLICABLE
 ├─ findings[]  ordered: FAIL, WARN, UNKNOWN, INFO; then by rule_id
 ├─ counts by severity
 ├─ preset_id, ruleset_version
 └─ diagnostics (inspector outcomes, versions, conflicts)
```

`overall` is computed by exactly one function, per spec §7.2, and that function is
covered by an exhaustive truth-table test. `INFO` and `UNKNOWN` are structurally excluded
from the computation — not filtered out by a condition that could later be edited, but
absent from the function's inputs.

`BatchSummary` is **derived** from `FileResult[]` on demand. It is never stored
alongside as a second source of truth that could drift.

`NOT_INSPECTED` and `NOT_APPLICABLE` are separate counters and are never added to `FAIL`
(spec §14.2).

---

## 10. REPORTING (L4)

### 10.1 Structure

```
BatchResult ──► ReportModel ──┬──► CsvWriter    → findings.csv (+ summary.csv)
                              └──► HtmlRenderer → report.html (self-contained)
```

`ReportModel` is a plain, serialisable structure built once and shared by both writers, so
CSV and HTML **cannot disagree**. It is also the snapshot-test target.

### 10.2 Constraints

- **Fully offline.** The HTML report inlines all CSS. No remote fonts, no CDN, no script
  that fetches. This is asserted by an automated test that scans the output for external
  URL schemes (spec §17.3).
- **CSV**: UTF-8 **with BOM**, RFC 4180 quoting, `\r\n` line endings, stable column order.
- Reports carry: PreflightQC version, scan start/end with timezone, preset name + id +
  `ruleset_version` + `last_verified_date`, inspector versions actually used, all outcome
  counts, per-file results, per-finding detail, partial/complete status, the approved
  claim language, and the "does not modify source files" statement (spec §17.2).
- **Forbidden-claim assertion**: an automated content check rejects any report containing
  the §4.1 phrases.
- **Failure does not lose results** (spec §23): rendering happens fully in memory, is
  written atomically to a temp file, then moved into place. A write failure surfaces as an
  actionable error with the results still in memory.
- Default output directory is a user-writable location, **never** the source video folder.

---

## 11. DEPENDENCY BOUNDARY

```
        PreflightQC process (closed source)
        ├── L6..L0 application code
        └── L0 process runner
                 │  spawn, argv, stdout(JSON), exit code, kill
                 │  ── no shared memory, no linking, no callbacks ──
                 ▼
        ┌────────────────────┐   ┌────────────────────┐
        │ ffprobe.exe        │   │ MediaInfo          │
        │ + libav*.dll       │   │ (BSD-2-Clause)     │
        │ (LGPL 2.1 shared)  │   │                    │
        └────────────────────┘   └────────────────────┘
```

Boundary rules (all from spec §10 and §21, all **locked**):

1. `ffprobe` is invoked as a **child process**. `libav*` is **never** linked into the
   application, statically or dynamically.
2. Communication is command-line arguments in, JSON on stdout out. **No complex internal
   data structures cross the boundary** — this is deliberate, and is the FSF's own
   articulation of what keeps two programs separate.
3. Only an **unmodified LGPL shared** build ships. No GPL build, no nonfree build, none of
   the prohibited components, no `ffmpeg` encoder binary.
4. MediaInfo is BSD-era only, no GUI, no libcurl.
5. Shared-library filenames are **unobfuscated** and user-replaceable.
6. Binaries are resolved by **absolute path** under the application directory. `PATH` is
   never consulted, so the application can never silently run an unknown build.
7. A **startup self-check** verifies each inspector launches and reports its version, and
   records those versions for the report. Failure produces an actionable message, not a
   fallback.

---

## 12. FILESYSTEM BOUNDARIES

| Path class | Access | Notes |
| --- | --- | --- |
| Source video files | **read-only** | Never opened for write. The process runner passes paths to inspectors; the application itself opens them only to stat. |
| Application directory | read-only at runtime | Contains binaries, presets, licences |
| `%LOCALAPPDATA%\PreflightQC\` | read/write | Config, custom profiles, logs |
| User-chosen export directory | write | Chosen per export; must be user-writable |
| Everything else | none | |

Rules:

1. **The application never obtains a write handle to a source file** — enforced by a test
   asserting bytes, size, and mtime are unchanged across a full batch (spec §25, AC-13).
2. Long paths (>260 chars) supported; UNC paths accepted with graceful timeout.
3. Symlinks and junctions followed at most one level, de-duplicated by resolved path.
4. All writes to owned locations are atomic (temp + replace).
5. Export never defaults to the source video's folder.

---

## 13. ERROR HANDLING

Three tiers:

| Tier | Scope | Behaviour |
| --- | --- | --- |
| **Job** | One file | Any exception becomes an `InspectionFailure` with a cause. `NOT_INSPECTED` + reason. Batch continues. |
| **Batch** | The run | Orchestrator failures are surfaced; completed results are preserved; batch is marked partial. |
| **Application** | Process | A last-resort handler writes a local diagnostic and shows an actionable dialog. **No network transmission** (spec §18.1). |

Principles (spec §23.1): isolation, attribution, never fabricate a verdict, bounded
external calls, visible in UI *and* report.

Every row of the spec §23 failure table maps to a named failure kind with a defined
user-visible message and a test.

---

## 14. CONCURRENCY STRATEGY

- **UI thread**: rendering and commands only. Never blocks.
- **Orchestrator thread**: owns the batch state machine, publishes immutable snapshots.
- **Worker pool** (default 4): inspect → normalise → validate per job.
- **Cross-thread communication** is by immutable message only. There is no shared mutable
  object between the pool and the UI.
- **The rule engine is pure and therefore trivially thread-safe.** It holds no state.
- Preset documents are loaded once, validated, and treated as immutable.
- No lock is held across a subprocess call.

This is deliberately the simplest model that works. Process pools, async I/O, and
work-stealing are not used because nothing in the measured workload justifies them yet.

---

## 15. CANCELLATION

1. A single `CancellationToken` per batch, checked between pipeline stages and before
   each subprocess spawn.
2. On cancel, the process runner terminates in-flight process trees with a bounded grace
   period, then force-kills.
3. Queued jobs transition to `CANCELLED` without executing.
4. Completed results are **preserved** and reportable.
5. The batch is marked `partial`, and the report states this explicitly and lists what was
   not processed (spec §13.7).
6. Cancellation is **prompt and bounded** — the UI must reflect it within the grace period,
   not "eventually".
7. Application shutdown performs the same sequence, plus child reaping, so no orphan
   inspector process survives.

---

## 16. LOGGING

| Aspect | Decision |
| --- | --- |
| Destination | Local rotating file under `%LOCALAPPDATA%\PreflightQC\logs\` |
| Transmission | **None, ever** (spec §18.1) |
| Default level | `INFO` — lifecycle, per-file outcome, inspector failures |
| Diagnostic level | Opt-in — full inspector argv, truncated stdout/stderr excerpts, timings |
| Content | **Never file contents.** File paths appear; a setting enables path redaction (spec §18.5) |
| Rotation | Size-capped with a bounded number of files |
| Secrets | None exist in V1 |

Logging is a diagnostic aid, not a results channel. Anything a user needs to act on
appears in the UI **and** the report (spec §23.1.5).

---

## 17. LOCAL CONFIGURATION

- One JSON file at `%LOCALAPPDATA%\PreflightQC\config.json`, atomically written.
- Settings: worker count, per-inspector timeout, HDR first-frame read on/off, recurse
  default, hidden-file inclusion, candidate extension list, log level, path redaction,
  default export directory, last-selected preset.
- **A corrupt or unreadable config falls back to defaults and reports it.** It never
  blocks startup.
- **No setting can weaken the severity model.** There is deliberately no "treat warnings
  as errors" or "strict mode" option — that would violate spec §7.1 by user preference.

---

## 18. SECURITY AND PRIVACY MODEL

### 18.1 Privacy

No telemetry, no analytics, no crash reporting, no update check, no account, no backend.
The application functions fully with all outbound network access blocked, and this is a
tested acceptance criterion (AC-12).

### 18.2 Threat model

The realistic threat is a **malformed or hostile media file**, since PreflightQC's whole
purpose is ingesting files of unknown provenance.

| Control | Effect |
| --- | --- |
| Parsing happens in **separate processes** | A parser crash or hang kills a child, not the application |
| **Bounded timeouts** on every inspector call | A hang cannot stall a batch |
| **Capped stdout/stderr** | A pathological file cannot exhaust memory |
| **No shell invocation**; arguments passed as a list | No command injection via filename |
| Minimal child environment, explicit `cwd` | Reduces inherited-state surprises |
| Files opened **read-only** | A bug cannot damage a customer's master |
| **No network code paths at all** | Nothing to exfiltrate through |
| Binaries resolved by **absolute path** | No `PATH` hijack; no unexpected build |
| Inspector binaries checksum-verified at packaging | Supply-chain integrity |
| Application, first-party binaries and installer **Authenticode-signed** | Tamper evidence, SmartScreen |

### 18.3 Non-controls (stated honestly)

PreflightQC does not sandbox the inspector processes beyond OS defaults, and does not
attempt to defend against a hostile file exploiting a vulnerability *inside* ffprobe or
MediaInfo. Process isolation limits blast radius; it is not a sandbox. Keeping the pinned
inspector versions current is the mitigation, and it is a release-gate item.

---

## 19. PACKAGING BOUNDARY

```
                 built and signed by us
    ┌──────────────────────────────────────────┐
    │ PreflightQC.exe, _internal/, presets/    │
    └──────────────────────────────────────────┘
                 bundled, unmodified, third party
    ┌──────────────────────────────────────────┐
    │ bin/ffprobe.exe + libav*.dll  (LGPL 2.1) │
    │ bin/MediaInfo                 (BSD-2)    │
    └──────────────────────────────────────────┘
                 obligations
    ┌──────────────────────────────────────────┐
    │ licenses/ LGPL texts, THIRD-PARTY-       │
    │ NOTICES, DEPENDENCY-MANIFEST, FFmpeg     │
    │ build configuration                      │
    └──────────────────────────────────────────┘
```

Boundary rules:

1. Third-party binaries are **bundled unmodified**. Re-signing is permitted; modification
   is not (modification would make PreflightQC a "modifier" with source-correspondence
   duties).
2. Shared-library names are **unobfuscated**.
3. Third-party binaries are **never committed to this repository** — they are fetched at
   packaging time from pinned, checksum-verified official sources and recorded in the
   dependency manifest. (`.gitignore` enforces this.)
4. `DEPENDENCY-MANIFEST` and `THIRD-PARTY-NOTICES` are **generated from the actual package
   contents**, not hand-maintained, so they cannot drift.
5. The package must run on a **clean machine** with no pre-installed FFmpeg, MediaInfo,
   Python, or developer runtime, under a **standard user account**.
6. Release gates G-1 … G-12 (spec §26.1) plus G-13 (ADR-001 §4.1) are all blocking.

---

## 20. WHAT THIS ARCHITECTURE DELIBERATELY DOES NOT DO

Recorded so a later session does not "helpfully" add them:

- **No persistent database.** Session-scoped in-memory state is sufficient for V1.
- **No persistent inspection cache across runs.** Cache keys would need invalidation
  logic, and the benefit is unproven.
- **No plugin system.** Presets are data; that is the extension point.
- **No async/await rewrite.** Threads plus subprocesses match the workload.
- **No abstraction over the metadata model** beyond the three-valued field. One concrete
  model, not an interface hierarchy.
- **No inter-process protocol of our own.** Command line in, JSON out.
- **No preset auto-update.** A network dependency and a supply-chain surface, and rule
  changes need human source re-verification (spec §19).
