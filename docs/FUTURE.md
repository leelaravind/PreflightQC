# PREFLIGHTQC — FUTURE / DEFERRED SCOPE

| Field | Value |
| --- | --- |
| Status | Parking lot. **Nothing here is committed, scheduled, or approved.** |
| Date | 2026-08-09 |

## Purpose

This file exists so that good ideas do not silently expand V1.

Per spec §29.3, an implementation session that encounters an idea outside the V1
specification **records it here and continues**. Adding anything below to V1 requires the
SPEC LOCK procedure (spec §29.2): an explicit written instruction, a specification update,
and re-verification of the affected acceptance criteria.

Entries are grouped by why they were deferred, because the reason determines how hard the
door is.

---

## 1. LOCKED NON-GOALS — the door is closed for V1

These are on spec §20's locked list. They are not "not yet"; they are "not V1", and
several of them would change what the product *is*.

| Item | Why it is locked out of V1 |
| --- | --- |
| Video upload / platform publishing | Would require platform API integrations, accounts, and network — contradicting the offline, no-account promise |
| Encoding, transcoding, compression, resizing, cropping | PreflightQC inspects; it does not modify. Would require shipping an encoder, with GPL/patent consequences |
| Repair, re-mux, metadata rewriting, "fix video" | Same: the product never writes to a source file |
| Audio modification, loudness normalization | Same |
| AI video analysis, copyright analysis, content moderation | Not file-metadata properties; would require decoding, models, or network |
| Subjective visual-quality scoring | Not measurable from metadata; would undermine the product's claim to determinism |
| Meta / TikTok / YouTube / LinkedIn API integration | Accounts, network, tokens — all contradicted by spec §18 |
| Cloud processing, SaaS backend, telemetry, analytics | Contradicted by spec §18 |
| macOS release, mobile release | Windows-first is the V1 scope (spec §22) |

**A later major version could revisit some of these.** Encoding and "fix video" in
particular would change the product's licensing posture fundamentally (x264/x265
commercial licences plus codec patent-pool licences would be required *before* any work
started) and should be treated as a new product decision, not a feature.

---

## 2. DEFERRED FOR TECHNICAL COST — plausible for V1.x

These are within the product's identity. They were deferred because they exceed the V1
inspection cost boundary (spec §10.5) or add dependency weight.

### 2.1 Loudness measurement (LUFS / true peak)

**Why deferred.** Requires an `ffmpeg -af ebur128` decode-and-measure pass over the whole
file — orders of magnitude more expensive than metadata inspection, and it engages the
decoder for the full duration rather than one frame.

**Why it matters.** LinkedIn CTV publishes a real, first-party target (−23 integrated
LUFS). Today PreflightQC reports that rule as `UNKNOWN` with "not measured by PreflightQC
V1". That is honest, but it is a genuine capability gap for one shipped preset.

**What it would need.** A second, opt-in analysis pass with its own progress and
cancellation; a re-run of the patent-posture question (full decode, not one frame); and a
UI that makes the cost visible before the user commits to it.

**Do not** import a loudness target for any platform that does not publish one. Meta and
TikTok publish none, and the −14 LUFS figure people cite is a music-streaming norm.

### 2.2 GOP / closed-GOP verification

**Why deferred.** Gap G-2 — requires packet-level analysis, beyond the V1 boundary.

**Why it matters.** Instagram Reels and Stories both document "Closed GOP" as a hard
requirement. PreflightQC currently reports it `UNKNOWN`. Closing this gap would make two
FAIL-class rules actually checkable.

### 2.3 Edit-list (`elst`) detection

**Why deferred.** Gap G-1 — needs atom-level container inspection. Phase 1 may find it
partially available; if not, it stays `UNKNOWN`.

**Why it matters.** Instagram's API documents "no edit lists" as a hard requirement, and
edit lists are a common, invisible export artefact.

### 2.4 Robust VFR detection

**Why deferred.** Gap G-5 — a single metadata field is often insufficient; reliable
detection needs packet-PTS analysis.

**Why it matters.** LinkedIn CTV requires a constant frame rate. Today PreflightQC only
emits `FAIL` when VFR is *positively reported*, and `UNKNOWN` otherwise — correct, but
weaker than it could be.

### 2.5 Native PDF report export

**Why deferred.** Every viable path adds either a heavy native dependency (Pango, Cairo,
GObject) or a licence complication, against a "prefer if feasible" requirement. V1 ships a
print-clean self-contained HTML report instead (ADR-001 §6.3).

**What it would need.** A candidate that survives the spec §21.6 dependency gate.

---

## 3. DEFERRED FOR SOURCE GAPS — blocked on the platforms, not on us

These cannot be built responsibly today because the authoritative source material does not
exist or was not obtainable. **They must not be filled from third-party blogs.**

| Item | Blocker |
| --- | --- |
| Instagram Reels **ad** preset | The Ads Guide Reels video page body was not extractable (register §1.5). Third-party transcriptions exist but are non-authoritative. |
| Instagram / Meta per-objective ad presets | The Ads Guide numeric tables are JavaScript-rendered and only partially capturable. |
| TikTok Spark Ads, Global App Bundle, Pangle, Streaming/Automotive presets | Values exist in the source pack but were out of V1 preset scope. **These are cheap to add** — preset data only, no engine change (register §2.6). |
| Meta HDR / colour-space rules | Meta publishes no creator-facing input requirement. `UNKNOWN` until it does. |
| TikTok codec profile/level, HDR, faststart, GOP, loudness rules | TikTok publishes nothing. `UNKNOWN` until it does. |
| YouTube Shorts encoding rules | No separate Shorts spec is published. `UNKNOWN` until it is. |
| YouTube Dolby Vision support | Not listed among supported HDR upload formats. `UNKNOWN`. |
| LinkedIn Live | RTMP ingest — there is no delivered file to inspect. May never be in scope. |

**Promotion rule (register §8.3):** any of these may move to `WARN` or `FAIL` **only**
when a first-party source publishes the requirement. Never from a third-party source.

---

## 4. PRODUCT AND WORKFLOW IDEAS

Not blocked by anything except V1 scope discipline.

| Idea | Note |
| --- | --- |
| **Preset update channel** | Deliberately excluded from V1 (spec §19): a network dependency, a supply-chain surface, and rule changes need human source re-verification. A signed, manually-triggered, offline-importable preset bundle would preserve the offline promise. |
| **Profile sharing between agency and freelancer** | V1 already supports export/import of a single profile file. A lightweight "client pack" of several profiles is a natural extension. |
| **Per-file preset override in one batch** | V1 is one preset per batch. Mixed-destination batches are a real workflow, but multi-preset result presentation and reporting need design. |
| **"Which preset would this pass?" mode** | Evaluate one file against all presets and show where it fits. Cheap given the engine; a genuinely useful diagnostic. |
| **Watch-folder mode** | Inspect on arrival. Needs care around partially-written files. |
| **CLI for pipeline integration** | A headless entry point already exists as dev tooling (Phase 5). Productising it is small and would serve agency automation. |
| **Comparison against a reference file** | "Match this approved master's specs" — a custom profile generated from an existing file. |
| **Rule-level mute per profile** | Risky: must never become a way to silence a `FAIL`. Would need to be restricted to `INFO`/`WARN` and recorded in the report. |
| **Localisation** | Findings text lives in preset data, so translation is a data problem. Note: the EULA translation obligation (licensing gate G-8) already applies. |
| **Accessibility pass** | Keyboard navigation, screen-reader labels, and not relying on colour alone for severity. Should arguably have been V1; recorded here honestly rather than claimed. |

---

## 5. TECHNICAL DEBT ACCEPTED IN V1

Recorded so it is visible rather than discovered.

| Item | Consequence | Revisit when |
| --- | --- | --- |
| Session-only inspection cache | Re-scanning the same folder in a new session re-inspects everything | Users report it as friction |
| No persistent batch history | A crash loses results not yet exported | Users report it as friction |
| Fixed 4-worker default | May be suboptimal on fast NVMe or slow network shares | Real measurements exist |
| Single primary video/audio stream validated | Multi-stream files are enumerated but only stream 0 is judged | A real multi-stream delivery workflow appears |
| UI coverage excluded from thresholds | UI regressions are caught by manual validation, not tests | UI complexity grows |
| No sandboxing of inspector processes beyond OS defaults | Process isolation limits blast radius but is not a sandbox | A relevant CVE, or an enterprise requirement |

---

## 6. HOW TO ADD SOMETHING TO THIS FILE

Record: **what** it is, **why** it is not in V1, and **what it would need**. Do not record
a solution design — this is a parking lot, not a backlog.

## 7. HOW TO MOVE SOMETHING OUT OF THIS FILE

1. An explicit written instruction naming the item.
2. For anything in §1 or §3: confirm the blocking condition has actually changed (a
   locked non-goal being reconsidered, or a first-party source now publishing the rule).
3. Update `docs/specification/PREFLIGHTQC-V1-SPEC.md` per the SPEC LOCK procedure (§29.2).
4. For new rules: add the source register row **first** (register §8.5), then the preset
   rule, then the boundary fixtures.
5. Re-verify every affected acceptance criterion.
