# PREFLIGHTQC — V1 PRODUCT SPECIFICATION

| Field | Value |
| --- | --- |
| Document | `PREFLIGHTQC-V1-SPEC.md` |
| Status | **LOCKED BASELINE** |
| Version | 1.1.0 |
| Date | 2026-08-09 |
| Scope | PreflightQC V1, Windows 10/11 x64 |
| Authority | This document is the single authoritative product baseline for V1. |

### Changelog

| Version | Date | Change | Procedure |
| --- | --- | --- | --- |
| 1.0.0 | 2026-08-09 | Locked baseline. Same-day SPEC LOCK amendment: FFmpeg licence requirement widened from LGPL v2.1-only to LGPL v2.1-or-v3 (`--enable-version3` permitted); recorded inline at §21 and §26, detail in `docs/licensing/LICENSING-GATE-V1.md` §2.0 | §29.2 |
| 1.1.0 | 2026-08-09 | §26.1 gate **G-12 amended**: mandatory attorney review superseded by **OWNER LICENSING & COMPLIANCE RISK ACCEPTANCE**, on the Product Owner's explicit written instruction. Decision record, reasons, accepted risks and reopening conditions: `docs/decisions/ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md`. **No attorney review occurred; no legal clearance is claimed.** | §29.2 |

This specification is **implementation-neutral**. It defines *what* PreflightQC V1 must
be and must do. It does not select a language, framework, or library. Those decisions
live in `docs/architecture/ARCHITECTURE-V1.md` and
`docs/architecture/ADR-001-TECH-STACK.md`, and are subordinate to this document.

Where this document and any other document in the repository disagree, **this document
wins**, unless the SPEC LOCK procedure in §29 has been followed.

---

## 1. PRODUCT DEFINITION

PreflightQC is an **offline Windows desktop application** that inspects local video files
and validates their technical properties against platform or custom delivery
specifications.

The product performs exactly four operations, in order:

```
INSPECT   read technical metadata from a local file, without modifying it
VALIDATE  evaluate normalised metadata against a selected preset's rule set
EXPLAIN   state, per finding, what was detected and what was expected, and why
REPORT    export the results in machine-readable and human-readable form
```

PreflightQC is a **read-only inspection and validation tool**. It is not an editor, an
encoder, a transcoder, a repair tool, or an uploader. It never writes to, re-muxes,
re-encodes, moves, renames, or otherwise alters a source video file.

PreflightQC is a **commercial, closed-source, downloadable desktop product**.

---

## 2. BUYER AND USERS

Primary users:

- Freelance video editors
- Social-media managers
- Content creators
- Small creative and video agencies
- Production teams

These users share three characteristics that shape the product:

1. They deliver or publish video files under time pressure, often in batches.
2. They are technically literate about video but are not expected to memorise or track
   per-platform encoding specifications.
3. They are frequently accountable to a client or an employer for a delivery that must
   not be rejected or silently degraded.

The buyer is typically the same person as the user (freelancer, creator) or the person
directly responsible for delivery quality in a small team (agency producer, post lead).
V1 assumes a single-seat, per-machine purchase with no account and no server-side
entitlement check required for core operation.

---

## 3. PROBLEM

Video files fail on delivery for technical reasons that are invisible in a preview
window and knowable only from file metadata:

- The container, codec, chroma subsampling, or scan type is outside the platform's
  documented acceptance set.
- The duration, dimensions, aspect ratio, frame rate, bitrate, or file size falls outside
  a documented limit.
- The audio track is missing, has an unsupported codec, the wrong channel count, or a
  sample rate above a documented ceiling.
- A file was exported with a preset intended for a different destination.

Today, users address this by reading platform help pages of varying accuracy, by
consulting third-party blogs that are frequently stale or wrong, by re-exporting
speculatively, or by discovering the failure after upload. In a batch, one bad file is
easily missed.

The compounding problem is **specification authority**. Platform documentation is
inconsistent, JavaScript-rendered, sometimes internally contradictory, and revised
without changelogs. Third-party guides confidently publish numbers that the platform
never stated. A validation tool that treats recommendations as requirements, or invents
thresholds to fill documentation gaps, produces confident false rejections — which is
worse than no tool at all.

---

## 4. PRODUCT PROMISE

> **Inspect local video exports before upload or delivery and validate them against
> platform or custom technical delivery specifications.**

Supporting promises:

- **Offline.** Inspection and validation work with no network connection.
- **Non-destructive.** Source files are opened read-only and never modified.
- **Traceable.** Every rule states its source, confidence, and last-verified date.
- **Honest.** Recommendations are reported as warnings, not failures. Where a
  specification is unknown or sources conflict, PreflightQC says so.
- **Batch-capable.** Many files, one preset, one summary, one report.

### 4.1 Claims that are forbidden

PreflightQC must **never** claim, in UI, reports, documentation, or marketing, that a
file is:

- "Guaranteed accepted by Instagram / TikTok / YouTube / LinkedIn"
- "Approved by" or "certified by" any platform
- "Guaranteed to upload successfully"

### 4.2 Approved claim language

> "Validated against the technical rules contained in the selected PreflightQC preset."

Variants must preserve the same three qualifications: *validated against*, *the technical
rules contained in*, *the selected preset*. Reports must additionally carry the preset
version and the rule-set last-verified date.

---

## 5. V1 WORKFLOW

```
ADD VIDEO FILES / FOLDER
        |
        v
SELECT PRESET
        |
        v
LOCAL METADATA INSPECTION          (ffprobe + MediaInfo, local subprocesses)
        |
        v
NORMALIZE METADATA                 (into one internal model; missing = explicitly absent)
        |
        v
APPLY RULE ENGINE                  (data-driven rules from the selected preset)
        |
        v
PASS / WARN / FAIL / INFO / UNKNOWN findings per file
        |
        v
SHOW EXPLANATION                   (detected vs expected, per finding, with source)
        |
        v
EXPORT REPORT                      (CSV + human-readable)
```

The user may re-run validation against a different preset without re-inspecting files,
because inspection results are cached for the session per file (keyed on path, size, and
modification time).

---

## 6. SUPPORTED PLATFORM PRESETS

V1 ships preset **families**. Within each family, a preset corresponds to one delivery
surface with its own documented rule set. Surfaces with materially different documented
technical rules are **never merged into one preset**.

### 6.1 Meta / Instagram

| Preset | Included in V1 | Basis |
| --- | --- | --- |
| Instagram Reels | Yes | Content Publishing API Reel Specifications (Tier 1, HIGH confidence) |
| Instagram Stories | Yes | Content Publishing API Story Video Specifications (Tier 1, HIGH confidence) |
| Instagram Feed video | Yes, reduced | No dedicated Tier 1 file-spec block exists; Ads Guide values are MEDIUM confidence and mostly recommendations. Ships as a WARN/INFO-dominant preset. |

### 6.2 TikTok

TikTok's own documentation gives four different official numbers for maximum organic
duration and file size across overlapping upload paths. The upload path is therefore an
explicit user choice, not an inference.

| Preset | Included in V1 | Basis |
| --- | --- | --- |
| TikTok — Content Posting API | Yes | Media Transfer Guide "Video restrictions" table (HIGH confidence) |
| TikTok — Studio / Web upload | Yes | Help Center "Tools for creators" (HIGH confidence) |
| TikTok — In-Feed Auction ad (Non-Spark) | Yes | Business Help Center, Auction In-Feed Ads |
| TikTok — TopView / Reservation ad | Yes | Business Help Center, TopView specifications |

### 6.3 YouTube

| Preset | Included in V1 | Basis |
| --- | --- | --- |
| Standard YouTube Upload | Yes | Supported file formats + recommended upload encoding settings + upload limits |
| YouTube Shorts | Yes, minimal | YouTube publishes only aspect ratio and duration for Shorts classification. Almost all other Shorts thresholds are UNKNOWN and must not be inherited from the standard preset. |

### 6.4 LinkedIn

| Preset | Included in V1 | Basis |
| --- | --- | --- |
| LinkedIn Organic (Pages / native video) | Yes | LinkedIn Help numeric spec (HIGH confidence) |
| LinkedIn Video Ads | Yes | Marketing Solutions Video Ads Specifications + Microsoft Learn Videos API |
| LinkedIn CTV | Yes | Marketing Solutions Connected TV Ads Specifications |

LinkedIn Live and Conversation/Message Ads are **out of scope**: the former has no
delivered media file to inspect, the latter has no video asset.

### 6.5 Custom

| Preset | Included in V1 |
| --- | --- |
| Custom Client Profile (user-authored, stored locally) | Yes — see §16 |

### 6.6 Preset construction rules

1. A preset is a data document, not code (§11).
2. Every rule in a preset carries a source reference into `docs/sources/SOURCE-REGISTER.md`.
3. A rule may only be severity `FAIL` if the source register classifies its basis as a
   hard requirement or a documented platform limit for that specific surface.
4. Where the source register records a conflict, the preset must either (a) use the more
   permissive value at `FAIL` and the stricter value at `WARN`, or (b) emit `UNKNOWN`.
   It must never silently pick one number.
5. Presets from different surfaces must never share a rule set by inheritance in a way
   that could leak a limit from one surface into another.

---

## 7. SEVERITY MODEL

**This section is a hard invariant. Any implementation that violates it is defective.**

Every validation rule must be classified as exactly one of:

| Severity | Meaning | Permitted basis |
| --- | --- | --- |
| `FAIL` | The file violates an authoritative hard requirement or a documented platform limit for the selected surface. | Only a Tier 1 / first-party hard requirement or documented limit. |
| `WARN` | The file departs from an official recommendation or best practice. | Official recommendation, best practice, eligibility condition, or a documented value whose confidence is below HIGH. |
| `INFO` | Useful technical information. | Anything measurable and worth reporting. |
| `UNKNOWN` | Insufficient source authority, or insufficient technical certainty, to judge. | Missing source, conflicting sources with no safe resolution, or metadata that could not be determined. |

### 7.1 Prohibitions

PreflightQC must **never**:

- Convert a recommendation into `FAIL`.
- Invent a platform requirement that no authoritative source states.
- Silently infer an unsupported numeric threshold.
- Treat unavailable or unreadable metadata as a failure.
- Promote a rule's severity because a third-party source is stricter than the
  first-party source.

### 7.2 Overall file status

```
if any finding has severity FAIL:
    overall = FAIL
else if any finding has severity WARN:
    overall = WARN
else:
    overall = PASS
```

`INFO` and `UNKNOWN` findings **do not independently downgrade** the overall result. A
file whose findings are all `PASS`, `INFO`, and `UNKNOWN` has overall status `PASS`.

### 7.3 Severity is derived, not hand-assigned

Each rule carries a `classification` (`HARD_REQUIREMENT`, `DOCUMENTED_LIMIT`,
`RECOMMENDATION`, `BEST_PRACTICE`, `ELIGIBILITY`, `UNKNOWN`). A guard in the engine maps
classification to the maximum permitted severity:

| classification | maximum permitted severity |
| --- | --- |
| `HARD_REQUIREMENT` | `FAIL` |
| `DOCUMENTED_LIMIT` | `FAIL` |
| `RECOMMENDATION` | `WARN` |
| `BEST_PRACTICE` | `WARN` |
| `ELIGIBILITY` | `WARN` |
| `UNKNOWN` | `INFO` |

A preset that declares `severity: FAIL` on a rule classified `RECOMMENDATION` is a
**malformed preset** and must be rejected at load time (§23). This guard is the
mechanical enforcement of §7.1.

### 7.4 Additional file-level states

Two states exist that are *not* rule severities, and are reported separately from
`PASS/WARN/FAIL`:

- `NOT_INSPECTED` — the file could not be inspected at all (unreadable, permission
  denied, deleted mid-scan, both inspectors failed). This is not `FAIL`; the file was
  never validated.
- `NOT_APPLICABLE` — the file is not a media file that the selected preset can be
  applied to.

Both must be counted separately in the batch summary and must never be silently folded
into the `FAIL` count.

---

## 8. INPUT HANDLING

### 8.1 Input methods (all three are V1 requirements)

1. **Drag-and-drop** of one or more files, one or more folders, or a mixture, onto the
   application window.
2. **File picker** — multi-select.
3. **Folder picker** — with an explicit, user-visible recurse on/off control.

### 8.2 Enumeration rules

- Folder input enumerates files by extension against a configurable candidate-extension
  list. Extension is a *candidate filter only*; the authoritative container
  determination comes from the inspector, never from the extension.
- Symlinks and junctions are followed at most one level and de-duplicated by resolved
  path.
- Duplicate paths added more than once are de-duplicated within a batch.
- Hidden and system files are included only if the user explicitly enables it (default:
  off).
- Enumeration must be cancellable and must not block the UI.

### 8.3 Constraints

- Files are opened **read-only**. The application must never obtain a write handle to a
  source file.
- No file is copied, moved, renamed, or written to.
- Long paths (>260 characters) must be supported on Windows.
- UNC/network paths must be accepted; slow or unavailable network paths must time out
  gracefully per §23 rather than hanging the batch.
- There is no hard limit on batch size in V1, but the batch must remain responsive and
  cancellable at any size.

---

## 9. METADATA REQUIREMENTS

The normalised internal metadata model must represent at least the following. Every
field is **explicitly three-valued**: a known value, an explicit "not present in file",
or an explicit "could not be determined". A field is never defaulted, guessed, or
zero-filled.

### 9.1 File

- File name
- Absolute path
- File size (bytes)
- Duration (seconds; container-level, with stream-level recorded separately)
- Last modified timestamp (used for inspection cache keying)

### 9.2 Container

- Container / format name(s)
- Container long name / commercial name
- Major brand and compatible brands where applicable
- Stream count, and count by stream type (video / audio / subtitle / data / timecode)
- Container-level tags
- Overall (container) bitrate
- `moov` atom position / fast-start status where applicable
- Presence of edit lists (`elst`) where applicable

### 9.3 Video stream

- Codec
- Codec profile
- Codec level
- Width, height
- Coded width, coded height where they differ from display dimensions
- Sample aspect ratio (SAR / pixel aspect ratio)
- Display aspect ratio (DAR), computed from dimensions × SAR and cross-checked
- Rotation / display-matrix metadata, and the **displayed** dimensions after rotation
- Frame rate (as an exact rational where available, e.g. 24000/1001)
- Frame-rate mode (CFR / VFR) where obtainable
- Bitrate (stream-level, with container-level and computed fallbacks recorded distinctly)
- Pixel format
- Bit depth
- Chroma subsampling
- Scan type / field order (progressive / interlaced / unknown)
- Colour range (full / limited)
- Colour space / matrix coefficients
- Transfer characteristics
- Colour primaries
- GOP / keyframe interval where safely obtainable
- HDR metadata where safely obtainable (mastering display, MaxCLL, MaxFALL)

### 9.4 Audio stream

- Presence (and count of audio streams)
- Codec
- Sample rate
- Channel count
- Channel layout / positions
- Bitrate where available

### 9.5 Advanced

- HDR identification (HDR10 / HLG / HDR10+ / none / unknown)
- Dolby Vision identification, including profile where the inspector reports it reliably

### 9.6 Determination rules

1. **Missing is not zero.** An absent bitrate is `NOT_PRESENT`, never `0`.
2. **Undetermined is not missing.** A field the inspector reported as `unknown` is
   `UNDETERMINED`, distinct from `NOT_PRESENT`.
3. **Every normalised field records its provenance**: which inspector produced it, and
   from which raw field. This provenance appears in detailed findings and in the report.
4. **Derived values are marked derived.** A DAR computed from width, height and SAR is
   flagged as derived, not as a value read from the file.
5. **Disagreement between inspectors is preserved**, not averaged or silently resolved
   (§10.4).

---

## 10. INSPECTION ARCHITECTURE

### 10.1 Locked dependency chain

```
PreflightQC
    -> ffprobe subprocess                    (primary structured metadata, JSON)
    -> MediaInfo complementary inspection    (gap-fill: scan type/order, HDR/DV naming)
    -> normalized internal metadata model
    -> rule engine
    -> findings
    -> reports
```

### 10.2 ffprobe constraints (locked)

- Use an **unmodified LGPL shared build** of ffprobe.
- Invoke ffprobe as a **separate child process**. Consume its structured JSON output.
- **Do not** statically link FFmpeg libraries into the proprietary application.
- **Do not** link `libav*` in-process.
- **Do not** ship a GPL build. **Do not** ship a nonfree build.
- The build may be LGPL **v2.1 or v3**. `--enable-version3` is permitted; the version
  actually shipped must be detected and named in the notices. *(Amended 2026-08-09 by
  SPEC LOCK; see `docs/licensing/LICENSING-GATE-V1.md` §2.0.)*
- **Do not** bundle: `libx264`, `libx265`, `libxvid`, `libfdk-aac`, `libnpp` / CUDA
  nonfree components, `frei0r`, `libvidstab`, `libzvbi`, `libsmbclient`, `libaribb24`,
  or any other GPL/nonfree component identified by the source pack.
- **Do not** ship the `ffmpeg` encoder binary in V1.

### 10.3 MediaInfo constraints (locked)

- Use **current BSD-era MediaInfo only** (≥ 0.7.63; the source pack pins 26.05).
- **Do not** ship legacy pre-0.7.63 GPL/LGPL versions.
- **Do not** ship the MediaInfo GUI.
- CLI or library, chosen on engineering grounds in the architecture document, with the
  source-pack licensing constraints intact either way.
- Do not enable or ship the libcurl network feature.

### 10.4 Reconciliation

- ffprobe is the **primary** source for structured stream parameters.
- MediaInfo is the **gap-filler** for fields where ffprobe is documented as weak:
  scan type / scan order, and HDR format / Dolby Vision profile naming.
- A per-field precedence table is defined in the architecture document. It is data, not
  scattered conditionals.
- Where both inspectors report a field and they **disagree**, the normalised model
  records both values and marks the field `CONFLICTED`. A `CONFLICTED` field must not
  produce a `FAIL`; it produces at most a `WARN`, and an `INFO` finding stating both
  values and their sources.

### 10.5 Inspection cost boundary

Extracting frame-attached HDR side data requires reading the first frame, which engages
the decoder. V1 therefore performs, at most, a **bounded first-frame read** for HDR side
data, gated behind an explicit setting, and never a full-file decode. No decode is
performed for any other purpose. This boundary is a licensing and patent posture
decision recorded in `docs/licensing/LICENSING-GATE-V1.md`.

---

## 11. RULE-ENGINE PRINCIPLES

### 11.1 Data-driven

Platform rules are **data**. Platform-specific numbers must not appear in UI code or
business logic. Adding, changing, or retiring a platform rule must require editing
preset/rule data, not rewriting the engine.

### 11.2 Rule record

Every rule must support at least:

| Field | Purpose |
| --- | --- |
| `rule_id` | Stable unique identifier, referenced by reports and tests |
| `platform` | Owning platform family |
| `preset_id` | Owning preset |
| `property` | Canonical path into the normalised metadata model |
| `operator` | `eq`, `neq`, `in`, `not_in`, `range`, `lt`, `lte`, `gt`, `gte`, `present`, `absent`, `matches`, `constant_only` |
| `expected` | Scalar, `{min, max}`, or list — verbatim from the source, with explicit units |
| `tolerance` | Optional numeric tolerance (e.g. aspect-ratio 5%) |
| `classification` | `HARD_REQUIREMENT` / `DOCUMENTED_LIMIT` / `RECOMMENDATION` / `BEST_PRACTICE` / `ELIGIBILITY` / `UNKNOWN` |
| `severity` | `FAIL` / `WARN` / `INFO` / `UNKNOWN`, bounded by §7.3 |
| `applies_when` | Guard predicate; the rule is skipped, not failed, when the guard is false |
| `explanation` | Human-readable statement of the rule |
| `message_pass` / `message_fail` | Display templates for detected-vs-expected text |
| `source_ref` | Reference into the source register |
| `source_url` | Direct URL |
| `confidence` | `HIGH` / `MEDIUM` / `LOW` |
| `last_verified_date` | Date the source was last confirmed |
| `enabled` | Whether the rule is active |
| `measurable_offline` | Whether the property is determinable from a local file at all |

### 11.3 Engine behaviour

1. **Deterministic.** Same file + same preset + same rule-set version = same findings,
   in the same order, on any machine. No wall-clock, locale, or randomness may affect
   evaluation or ordering.
2. **Generic.** The engine knows operators and the metadata model. It knows nothing about
   Instagram, TikTok, YouTube, or LinkedIn.
3. **Guarded severity.** Severity is bounded by classification per §7.3 at load time.
4. **Missing input is UNKNOWN.** If a rule's `property` is `NOT_PRESENT` or
   `UNDETERMINED` in the normalised model, the rule emits an `UNKNOWN` finding stating
   that the property could not be determined. It **never** emits `FAIL`.
5. **Guards skip, they do not fail.** If `applies_when` evaluates false, the rule is
   skipped and contributes no finding (or an `INFO` "not applicable" entry).
6. **Rules are independent.** No rule may read another rule's result. Aggregation happens
   only in §14.
7. **Unknown operator or unknown property path** in a preset is a malformed preset, not a
   file failure (§23).

---

## 12. SOURCE TRACEABILITY

1. `docs/sources/SOURCE-REGISTER.md` is the authoritative register of every source and
   every rule derived from it.
2. The original research documents are retained unaltered under
   `docs/sources/{meta,tiktok,youtube,linkedin,mediainfo,ffmpeg}/`.
3. Each register entry records, where practical: platform, preset / content type,
   property, rule / value / range, classification, authoritative source title, source
   URL, date accessed, confidence, implementation behaviour, and notes / conflicts.
4. **Uncertain source material must not be converted into hard rules.**
5. **Conflicts are preserved.** Where sources conflict, the register records both values
   and their sources. The preset resolves conservatively (§6.6 rule 4) or emits
   `UNKNOWN`.
6. Every shipped rule must be reachable from a report finding back to a register entry
   and from there to a named source and access date.
7. Preset data carries a rule-set version and a `last_verified_date`. Reports print both.

---

## 13. BATCH BEHAVIOUR

1. A batch is: a set of input files + exactly one selected preset.
2. Files are inspected and validated **independently**. One file's outcome never affects
   another's.
3. **One broken file must never terminate the batch.** A file that cannot be inspected is
   recorded as `NOT_INSPECTED` with a reason, and the batch continues.
4. Progress is reported continuously: total, completed, in-flight, remaining.
5. Per-file results appear as they complete; the user does not wait for the whole batch
   to see the first result.
6. The batch is **cancellable at any time**. Cancellation stops new work, allows in-flight
   inspections to terminate within a bounded timeout, and preserves all results completed
   up to that point.
7. Partial batches are reportable. A cancelled or partially failed batch produces a
   report that explicitly states it is partial and lists what was not processed.
8. Results are stable and reproducible in order regardless of completion order
   (presentation order is input order, not completion order).

---

## 14. RESULT LOGIC

### 14.1 Per-file

Per §7.2. The per-file result carries:

- Overall status: `PASS` / `WARN` / `FAIL`, or the separate states `NOT_INSPECTED` /
  `NOT_APPLICABLE`
- Counts of findings by severity
- The full ordered list of findings
- The preset id and rule-set version used
- Inspection provenance (which inspectors ran, their versions, whether either failed)

### 14.2 Batch summary

- Total files added
- Files inspected
- Counts: `PASS`, `WARN`, `FAIL`, `NOT_INSPECTED`, `NOT_APPLICABLE`
- Total findings by severity across the batch
- Selected preset and rule-set version
- Scan start and end timestamps
- Whether the batch was completed or cancelled

`NOT_INSPECTED` and `NOT_APPLICABLE` are reported as their own columns and are never
added to the `FAIL` count.

---

## 15. DETAILED FINDINGS

Every finding must present, at minimum:

| Element | Requirement |
| --- | --- |
| Severity | `FAIL` / `WARN` / `INFO` / `UNKNOWN` |
| Property | Human-readable name of the property checked |
| Detected value | The value found, with units — or an explicit "not present" / "could not be determined" |
| Expected value | The rule's expected value, range, or list, with units, phrased as *required* or *recommended* matching the classification |
| Explanation | Plain-language statement of what this means |
| Source | Source title + URL + date accessed + confidence |
| Rule id | Stable id, for support and for report cross-reference |
| Provenance | Which inspector supplied the detected value |

Additional requirements:

- Findings must never display a value the tool did not actually measure.
- A `WARN` finding's text must not read as a rejection. It states a recommendation.
- An `UNKNOWN` finding must state *why* it is unknown: metadata unavailable, sources
  conflict, or no authoritative specification exists.
- A `CONFLICTED` metadata field must show both inspector values and both provenances.
- Findings are ordered deterministically: `FAIL`, then `WARN`, then `UNKNOWN`, then
  `INFO`; within a severity, by rule id.

---

## 16. CUSTOM CLIENT PROFILES

V1 supports **locally stored** custom profiles. They are ordinary preset documents
authored by the user through the UI, stored on the user's machine, and evaluated by the
same engine as platform presets.

### 16.1 Configurable properties (V1 set)

- Dimensions (width, height; exact, minimum, maximum, or an allowed list)
- Aspect ratio (value or range, with optional tolerance)
- Containers (allowed list)
- Video codecs (allowed list)
- Frame rate (exact value, allowed list, or range)
- Duration (minimum, maximum)
- File size (minimum, maximum)
- Video bitrate (minimum, maximum)
- Audio codec (allowed list)
- Audio sample rate (exact value, allowed list, or range)
- Audio channels (exact value or range)

### 16.2 Rules

1. Each configured property may be set to severity `FAIL` or `WARN` by the user. Custom
   profiles are the user's own delivery specification, so the §7.3 classification guard
   is satisfied by classifying user-authored constraints as `HARD_REQUIREMENT` when the
   user marks them required and `RECOMMENDATION` when the user marks them recommended.
2. A property the user does not configure is simply not checked. It does not default to
   any value.
3. Profiles are stored as human-readable documents in the user's application data
   directory, and can be exported and imported as a single file (so an agency can hand a
   client profile to a freelancer).
4. Profiles carry a name, an optional client/notes field, a created date, and a modified
   date.
5. Custom profiles must not be able to express platform claims. Reports generated from a
   custom profile state the profile name, not a platform name.
6. **Scope bound:** V1 must not become a broadcast-specification authoring suite. The
   property set above is the complete V1 set. Additions require the SPEC LOCK procedure
   (§29).

---

## 17. REPORTING

### 17.1 Required export formats

1. **CSV** — machine-readable, one row per finding, with a companion summary row set or
   a separate summary CSV.
2. **Human-readable report** — HTML is the V1 baseline. PDF is delivered if it can be
   produced without adding a dependency that conflicts with §21; otherwise the HTML
   report must be print-clean so the user can produce a PDF from it.

### 17.2 Required contents (both formats)

- PreflightQC version
- Scan timestamp (start and end), with timezone
- Selected preset name, preset id, rule-set version, and rule-set last-verified date
- Inspector versions actually used (ffprobe build identifier, MediaInfo version)
- Files scanned: total, and counts by outcome
- PASS / WARN / FAIL totals, plus `NOT_INSPECTED` and `NOT_APPLICABLE` totals
- Per-file overall result
- Per-file detailed findings, each with detected value, expected/recommended value,
  explanation, severity, rule id, and source reference
- An explicit statement that the batch was complete or partial/cancelled
- The §4.2 approved claim language
- A statement that PreflightQC does not modify source files

### 17.3 Report constraints

- Reports must be generated **offline** with no external resource fetches. HTML reports
  must be fully self-contained (inlined CSS, no remote fonts, no CDN references,
  no analytics).
- Reports must never contain the §4.1 forbidden claims.
- CSV must be UTF-8 with a BOM (for Excel compatibility on Windows), RFC 4180 quoting,
  and stable column order.
- Report generation failure must not lose results (§23).
- The user chooses the output location; the default is a user-writable location, never
  the folder containing the source videos.

---

## 18. PRIVACY AND OFFLINE REQUIREMENTS

1. **No telemetry.** No usage analytics, crash reporting, ping, heartbeat, or update
   check that transmits data.
2. **No cloud upload.** Video files, metadata, findings and reports never leave the
   machine.
3. **No account.** No sign-in, no user identity, no server-side entitlement check for
   core operation.
4. **No backend.** Core operation requires no server of any kind.
5. Logs are local, written to a user-scoped location, and must not contain file contents.
   File paths appear in logs; a user-facing setting must allow path redaction.
6. Custom profiles and application configuration are local files under the user's control.
7. The application must function fully with all outbound network access blocked by a
   firewall. This is a testable acceptance criterion (§25).

---

## 19. INTERNET REQUIREMENTS

| Function | Internet required |
| --- | --- |
| Inspection | No |
| Validation | No |
| Reporting | No |
| Custom profiles | No |
| Preset updates | Not in V1 (presets ship with the application) |
| Licence activation | Not required for core operation in V1 |

V1 ships preset data inside the application. There is no preset auto-update mechanism,
because an auto-updater would be a network dependency and a supply-chain surface, and
because rule changes require source re-verification by a human (§12). Preset updates ship
with application updates.

---

## 20. NON-GOALS — LOCKED

PreflightQC V1 must **not** implement:

- Video upload
- Social-platform publishing
- Video encoding
- Transcoding
- Compression
- Resizing
- Cropping
- Repair
- Audio modification
- Loudness normalization
- Metadata rewriting
- AI video analysis
- Copyright analysis
- Content moderation
- Subjective visual-quality scoring
- Account integrations
- Meta API integration
- TikTok API integration
- YouTube API integration
- LinkedIn API integration
- Cloud processing
- Telemetry
- Analytics
- SaaS backend
- macOS release
- Mobile release
- FFmpeg encoding
- Automatic "fix video" functionality

Any useful idea outside V1 belongs in `docs/FUTURE.md`. Nothing on this list may enter V1
without the SPEC LOCK procedure (§29).

### 20.1 Derived non-goals

Consequences of the list above, stated explicitly to prevent drift:

- No safe-zone, watermark, text-overlay, or composition analysis (not a file-metadata
  property).
- No perceptual quality scoring.
- No loudness *normalization*. Loudness *measurement* is not in V1 either, because the
  only preset that references a loudness target (LinkedIn CTV, −23 LUFS) requires a
  decode-and-measure pass that exceeds the §10.5 inspection cost boundary. That rule
  ships as `UNKNOWN` in V1 with an explicit "not measured by PreflightQC V1" explanation.
  Loudness measurement is a FUTURE candidate.
- No platform metadata validation that requires user-entered title/description/tags in
  V1 (YouTube's API metadata limits are file-external). These ship as `INFO` guidance in
  the report, not as findings against the file. Optional metadata entry is a FUTURE
  candidate.

---

## 21. DEPENDENCY CONSTRAINTS

1. The metadata architecture in §10 is **locked**.
2. ffprobe: unmodified LGPL shared build, invoked as a child process, JSON output, no
   static linking, no GPL build, no nonfree build, none of the prohibited components
   listed in §10.2, no `ffmpeg` encoder binary.
3. MediaInfo: current BSD-era only, no GUI, no pre-0.7.63 build, no libcurl/network
   feature.
4. Third-party binaries are sourced only from their official distribution channels and
   verified by published checksum before entering a release.
5. Every bundled component must appear in the dependency manifest with: name, exact
   version, exact build identifier, licence, source URL, checksum, and notice text
   requirement.
6. Any dependency added to the application (not only the inspectors) must be assessed
   against the same gate before it can enter a release package. A dependency whose
   licence would impose copyleft on PreflightQC's own source is prohibited.
7. Application dependencies with LGPL-family licences are permitted only where the
   shared-library mechanism can be satisfied and the corresponding notices and source
   availability are shipped. This must be verified at the §26 release gate, not assumed.

---

## 22. WINDOWS-FIRST RELEASE

1. **Target: Windows 10 and Windows 11, x64.** No other platform is a V1 release target.
2. ARM64 Windows is not a V1 target.
3. The application must run on a **clean machine** with no developer runtime, no
   pre-installed FFmpeg or MediaInfo, and no Visual C++ redistributable that PreflightQC
   has not itself accounted for.
4. All inspector binaries and their shared libraries are bundled with the application.
   PreflightQC must never invoke an ffprobe or MediaInfo found on the user's `PATH`.
5. The application must install and run under a standard (non-administrator) user
   account. Per-user install is the default; a machine-wide install option is permitted.
6. The application and installer must be Authenticode code-signed.
7. Third-party DLL filenames must not be obfuscated (an LGPL compliance requirement,
   §26).
8. Portability to macOS is a design consideration but **not** a V1 deliverable. No V1
   effort is spent on macOS packaging, signing, or notarization.

---

## 23. FAILURE HANDLING

Each condition below has a defined, tested behaviour. In every case, the batch continues.

| Condition | Required behaviour |
| --- | --- |
| Corrupt video | `NOT_INSPECTED` if no usable metadata; if partial metadata is obtained, validate what is known and emit `UNKNOWN` for the rest. Never `FAIL` for corruption alone; report corruption as its own diagnostic. |
| Unsupported video | `NOT_APPLICABLE` or a `FAIL` on an explicit container/codec rule, depending on whether the preset has such a rule. Never an unhandled error. |
| Unreadable file | `NOT_INSPECTED`, reason "unreadable", with the OS error surfaced. |
| Permission denied | `NOT_INSPECTED`, reason "permission denied", with a remediation hint. |
| File deleted/moved during scan | `NOT_INSPECTED`, reason "file no longer available". Batch continues. |
| ffprobe crash | Recorded; MediaInfo result used alone if usable; otherwise `NOT_INSPECTED`. Never crashes the application. |
| MediaInfo crash | Recorded; ffprobe result used alone; fields MediaInfo would have filled become `UNDETERMINED`. |
| Inspector timeout | Per-file, per-inspector bounded timeout. Process is terminated (and its children reaped). Result is `NOT_INSPECTED` or partial with `UNDETERMINED` fields. Timeout duration is configurable. |
| Malformed inspector JSON | Parse failure is caught; treated as inspector failure for that file; raw output retained in the diagnostic log (truncated). |
| Missing metadata | Explicit `NOT_PRESENT` / `UNDETERMINED` in the model; rules over it emit `UNKNOWN`. **Never `FAIL`.** |
| Multiple video streams | The first video stream is designated primary and validated. All streams are enumerated in metadata. An `INFO` finding states that multiple video streams were found and which was validated. |
| Multiple audio streams | The first audio stream is designated primary and validated. All are enumerated. `INFO` finding as above. |
| No audio stream | Recorded as `audio.present = false`. Audio rules emit `UNKNOWN` unless the preset explicitly declares an audio-required rule with sufficient source authority. **Absence of audio is never an implicit `FAIL`.** |
| Malformed preset | Preset fails to load. The user is told which preset and which rule is invalid. The application remains usable with other presets. A malformed preset must never partially load. Validation includes the §7.3 severity guard. |
| Interrupted batch (crash/kill) | Results completed before the interruption are recoverable for report export where feasible; at minimum the application restarts cleanly with no corrupt state. |
| Cancellation | Bounded, prompt, preserves completed results, marks the batch partial. In-flight inspector processes are terminated. |
| Report-generation failure | Results are **not** lost. The user is told the export failed and why, and can retry or choose a different location/format. |
| Disk full / read-only output location | Treated as report-generation failure above, with a specific message. |
| Inspector binary missing or fails to launch | Application startup self-check detects it and presents an actionable message. The application does not silently fall back to a `PATH` binary (§22.4). |

### 23.1 General principles

1. **Isolation.** A failure is attributed to one file and contained there.
2. **Attribution.** Every failure names the file and the cause.
3. **Never fabricate.** A failure never produces a validation verdict about the file's
   conformance.
4. **Bounded.** Every external process call has a timeout and is reaped.
5. **Visible.** Failures appear in the UI and in the report, not only in a log.

---

## 24. TEST REQUIREMENTS

The full strategy is in `docs/testing/TEST-STRATEGY-V1.md`. The specification requires:

1. A **deterministic golden test corpus**, generated reproducibly from a committed
   manifest, covering: `PASS`, `WARN`, `FAIL`, `UNKNOWN`, corrupt, unsupported, mixed
   batch, and boundary conditions.
2. For **every hard deterministic rule**: a valid boundary case, an invalid boundary
   case, the expected severity, and the expected overall file status.
3. Tests proving that **every platform recommendation generates `WARN`, never `FAIL`**.
   This is enforced both by a per-rule test and by a global assertion over all shipped
   presets that no rule classified `RECOMMENDATION`, `BEST_PRACTICE`, or `ELIGIBILITY`
   carries severity `FAIL`.
4. Tests proving that **missing metadata does not generate `FAIL`**, per property class.
5. Tests proving that `INFO` and `UNKNOWN` findings do not downgrade overall status.
6. Tests for every row of the §23 failure table.
7. A test proving the application performs **zero outbound network calls** during a full
   inspect-validate-report cycle.
8. A test proving **no source file is opened for writing and no source file's bytes,
   size, or modification time change** across a full batch.
9. Golden report snapshot tests (CSV and HTML) for a fixed corpus, preset, and clock, so
   report regressions are caught.

---

## 25. ACCEPTANCE CRITERIA

V1 is complete when all of the following are demonstrably true on a clean Windows 10 and
Windows 11 x64 machine:

| # | Criterion |
| --- | --- |
| AC-01 | The user can add video files by drag-and-drop, by file picker, and by folder picker. |
| AC-02 | The user can select any shipped platform preset or a locally saved custom profile. |
| AC-03 | A batch of at least 100 mixed files completes without terminating on any individual file failure. |
| AC-04 | Each file receives an overall status of `PASS`, `WARN`, `FAIL`, `NOT_INSPECTED`, or `NOT_APPLICABLE`, computed per §7.2 and §7.4. |
| AC-05 | A batch summary shows totals per outcome, with `NOT_INSPECTED` and `NOT_APPLICABLE` counted separately from `FAIL`. |
| AC-06 | Every finding shows detected value, expected value, explanation, severity, rule id, and source reference with access date. |
| AC-07 | No shipped rule classified `RECOMMENDATION`, `BEST_PRACTICE`, or `ELIGIBILITY` carries severity `FAIL`, verified by an automated assertion over all shipped presets. |
| AC-08 | Missing or undeterminable metadata produces `UNKNOWN`, never `FAIL`, verified by test. |
| AC-09 | The user can create, edit, save, delete, export, and import a custom client profile covering the §16.1 property set. |
| AC-10 | The user can export a CSV report and a human-readable report containing all §17.2 elements. |
| AC-11 | Reports contain the §4.2 approved claim language and none of the §4.1 forbidden claims, verified by an automated content assertion. |
| AC-12 | The application completes a full inspect-validate-report cycle with all outbound network access blocked. |
| AC-13 | No source video file is modified: bytes, size, and modification time are unchanged across a full batch, verified by test. |
| AC-14 | A batch can be cancelled at any point; completed results are preserved and the report is marked partial. |
| AC-15 | Every row of the §23 failure table has a passing test. |
| AC-16 | The golden corpus passes with expected severities and overall statuses, on a machine with no network access. |
| AC-17 | The application installs and runs under a standard non-administrator account with no pre-existing FFmpeg or MediaInfo on the machine, and never invokes a `PATH` binary. |
| AC-18 | The release package contains a complete `DEPENDENCY-MANIFEST` and `THIRD-PARTY-NOTICES`, and passes the §26 licensing gate. |
| AC-19 | An automated scan of the release package finds no GPL or nonfree component from the prohibited list. |
| AC-20 | The application and installer are Authenticode code-signed and install cleanly on a machine with SmartScreen enabled. |

---

## 26. RELEASE PACKAGE

A V1 release package consists of:

1. The signed PreflightQC application and its installer.
2. Bundled `ffprobe` and its `libav*` shared libraries, from an unmodified official LGPL
   **shared** build, with unobfuscated filenames.
3. Bundled MediaInfo (current BSD-era, no GUI, no network feature).
4. Shipped preset data with rule-set version and last-verified dates.
5. `DEPENDENCY-MANIFEST` — every bundled component with name, exact version, exact build
   identifier, licence, official source URL, and verified checksum.
6. `THIRD-PARTY-NOTICES` — every required notice and licence text, matching the actual
   shipped binaries.
7. The full LGPL 3.0 licence text — the licence the verified FFmpeg build is actually
   under — together with the LGPL 2.1 text, which v3 incorporates by reference and
   which covers libzvbi. *(Amended 2026-08-09 by SPEC LOCK; see licensing gate §2.0.)*
8. FFmpeg attribution and configure/build information for the exact shipped build.
9. Version-matched corresponding FFmpeg source, made available from the same server as
   the PreflightQC download.
10. The EULA, with the carve-outs required by §26.1.
11. A local offline About screen carrying the required attributions.

### 26.1 Release gates (all blocking)

| Gate | Condition |
| --- | --- |
| G-1 | `DEPENDENCY-MANIFEST` exists, is complete, and matches the actual contents of the release package byte-for-byte by checksum. |
| G-2 | `THIRD-PARTY-NOTICES` exists and covers every component in the manifest, with the correct notice form for each licence. |
| G-3 | Automated scan confirms no GPL or nonfree component from the §10.2 prohibited list is present. |
| G-4 | The shipped ffprobe build is confirmed to be an LGPL shared build (not GPL, not nonfree, no prohibited component) by inspecting its reported configuration, **and the LGPL version it is actually under is recorded** so the shipped notices name the right one. |
| G-5 | Corresponding FFmpeg source, version-matched to the shipped binaries, is archived and hosted on the same server as the download. |
| G-6 | Configure line / build recipe for the exact shipped build is recorded and shipped. |
| G-7 | DLL names are unobfuscated. |
| G-8 | The EULA contains no reverse-engineering prohibition that conflicts with LGPL rights (or carves out the LGPL components), disclaims ownership of FFmpeg, and names FFmpeg and the LGPL version the shipped build actually carries (**LGPL 3.0** for the verified build). All EULA translations carry the same edits. |
| G-9 | MediaInfo BSD-2-Clause attribution present; ZenLib zlib notice present; the third-party notice list matches the actual compiled feature set of the shipped MediaInfo binary. |
| G-10 | Third-party binaries were obtained from official channels and their published checksums verified. |
| G-11 | Application and installer are Authenticode code-signed. |
| G-12 | **Owner licensing & compliance risk acceptance is complete** *(amended 2026-08-09 by SPEC LOCK, v1.1.0 — previously: attorney review; see `docs/decisions/ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md`)*: the dependency manifest is complete; all required licence texts and notices are present; corresponding-source obligations are prepared and published as applicable; the EULA is present with its required carve-outs; every known unresolved legal question is documented (currently L-1…L-14 in `docs/licensing/LEGAL-REVIEW-PACK-V1.md`); the **Product Owner has explicitly accepted the residual legal/licensing risk in writing for the specific release**; no claim of attorney review or legal clearance appears anywhere; and any material change to dependencies, licences, distribution, jurisdictions or functionality reopens the gate. |

**No legal clearance is claimed by this specification or by any document in this
repository. No attorney has reviewed this product.** G-12 in its amended form is a hard
release prerequisite: release without the owner's written risk acceptance remains
prohibited. Professional legal review is superseded as a *mandatory* V1 requirement, not
as a recommendation — it remains recommended, and the conditions that must reopen its
consideration are listed in the decision record.

---

## 27. PRODUCT POSITIONING

PreflightQC is positioned as a **pre-delivery technical QC step**, not as a guarantee of
platform acceptance and not as a quality judgement.

- It answers: *"Does this file meet the documented technical rules for where I am sending
  it?"*
- It does not answer: *"Will this perform well?"*, *"Is this good?"*, or *"Will the
  platform definitely accept this?"*

Differentiation rests on three things, in order:

1. **Correct severity discipline.** Competing checklists and blog-derived tools routinely
   present recommendations as requirements. PreflightQC's refusal to do so is the
   product.
2. **Source traceability.** Every verdict names its source and its date. A user can
   defend a delivery decision with it.
3. **Offline and private.** Client footage never leaves the machine. This matters to
   agencies under NDA.

Honest limitations, stated in-product:

- PreflightQC reads metadata; it does not watch the video.
- Platform specifications change without notice; rules carry a last-verified date.
- Where a platform documents nothing, PreflightQC says `UNKNOWN` rather than inventing a
  threshold.

---

## 28. COMMERCIAL AND DISTRIBUTION ASSUMPTIONS

These are **assumptions**, recorded so that implementation does not encode contradictory
expectations. They are not V1 deliverables.

1. Distribution is a **direct download** of a signed Windows installer.
2. Licensing model assumption: paid, per-seat, perpetual-with-current-major or annual.
   **No licensing enforcement mechanism is implemented in V1** (§20).
3. No payment-provider integration is implemented in V1. Vendor selection (Lemon Squeezy,
   Gumroad, or other) is deferred and must not influence V1 architecture.
4. Core operation must never depend on an activation server. Any future entitlement check
   must degrade to full offline function.
5. Updates are delivered as a new signed installer download. No auto-updater in V1.
6. Support is out-of-band (email / web); the application must not phone home for support.
7. The product name "PreflightQC" is a working name; trademark clearance is not claimed.
8. Third-party trademarks (Instagram, Meta, TikTok, YouTube, LinkedIn, MediaInfo, FFmpeg)
   are used descriptively only. No endorsement may be implied in product, reports, or
   marketing.

---

## 29. SPEC LOCK RULES

### 29.1 What is locked

The following are locked and may not be changed by an implementation session:

- §7 Severity model, including §7.1 prohibitions, §7.2 overall status logic, and §7.3
  classification-to-severity guard.
- §10 Inspection architecture and its dependency constraints.
- §12 Source traceability requirements.
- §18 Privacy and offline requirements.
- §20 Non-goals.
- §21 Dependency constraints.
- §22 Windows-first release scope.
- §26.1 Release gates.

### 29.2 Change procedure

A change to any locked item requires:

1. An explicit written instruction identifying the section and the change.
2. An update to this document, with the version incremented and a changelog entry.
3. Re-verification of every acceptance criterion affected.
4. For any change touching §10, §21, or §26.1: re-running the licensing gate.

### 29.3 Rules for implementation sessions

An implementation session executing `docs/planning/IMPLEMENTATION-PLAN-V1.md`:

1. **Must not invent product requirements.** If the plan is ambiguous, the session stops
   and asks. It does not choose on the user's behalf and proceed silently.
2. **Must not expand scope.** Anything not in this specification or the plan is out of
   scope. Ideas go to `docs/FUTURE.md`.
3. **Must not weaken the severity model** to make a test pass.
4. **Must not add a platform rule** that is not backed by an entry in
   `docs/sources/SOURCE-REGISTER.md`.
5. **Must not add a dependency** without running it through §21 and recording it in the
   dependency manifest.
6. **Must not claim legal clearance** anywhere in code, documentation, or UI.
7. **Must record every deviation** from this specification explicitly in its completion
   report, as `SPEC DEVIATIONS`. Silent deviation is a defect.

### 29.4 Precedence

```
PREFLIGHTQC-V1-SPEC.md          (this document — highest authority)
    > SOURCE-REGISTER.md         (authority for rule values and their sources)
    > ARCHITECTURE-V1.md
    > IMPLEMENTATION-PLAN-V1.md
    > ADR-001-TECH-STACK.md
    > code
```

---

## APPENDIX A — GLOSSARY

| Term | Meaning |
| --- | --- |
| Preset | A named, versioned data document containing a rule set for one delivery surface. |
| Rule | One evaluable constraint, per §11.2. |
| Finding | The result of evaluating one rule against one file. |
| Classification | The evidentiary strength of a rule's basis, per §7.3. |
| Severity | The reporting weight of a finding: `FAIL` / `WARN` / `INFO` / `UNKNOWN`. |
| Surface | A specific delivery path (e.g. Instagram Reels via the Content Publishing API) with its own documented rules. |
| Inspector | An external tool that reads metadata from a file (`ffprobe`, MediaInfo). |
| Normalised model | The single internal representation of a file's metadata, per §9. |
| `NOT_PRESENT` | The property is genuinely absent from the file. |
| `UNDETERMINED` | The property could not be determined by the inspectors. |
| `CONFLICTED` | Both inspectors reported the property and disagreed. |
| Golden corpus | The deterministic set of test media with known expected results. |
| Rule-set version | The version stamp of the shipped preset data, printed on every report. |
