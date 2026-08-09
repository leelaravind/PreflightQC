# PreflightQC

Offline Windows desktop application for inspecting local video exports and validating
them against platform or custom technical delivery specifications.

PreflightQC does four things and nothing else:

```
INSPECT  ->  VALIDATE  ->  EXPLAIN  ->  REPORT
```

It never modifies the source video files.

## Project status

**Phase: PLANNING / SPEC LOCK.**

- No production application code exists in this repository.
- No binaries are bundled.
- No release, installer, or distribution artefact has been produced.
- `src/`, `tests/`, `test-assets/`, `packaging/` and `third-party/` are reserved
  placeholders. They are populated only when the implementation plan is explicitly
  approved for execution.

Implementation must not begin until an explicit instruction approves
`docs/planning/IMPLEMENTATION-PLAN-V1.md` for execution.

## What V1 is

A local, offline tool that takes video files (drag-and-drop, file picker, or folder
picker), reads their metadata with locally bundled inspectors (`ffprobe` and MediaInfo),
normalises that metadata into a single internal model, evaluates it against a selected
preset's data-driven rule set, and reports PASS / WARN / FAIL / INFO / UNKNOWN findings
with detected-vs-expected explanations, exportable as CSV and as a human-readable report.

V1 preset families: Instagram/Meta, TikTok, YouTube, LinkedIn, and locally saved
Custom Client Profiles.

No telemetry. No cloud upload. No account. No backend required for core operation.

## What V1 is not

PreflightQC does not encode, transcode, compress, resize, crop, repair, re-mux, rewrite
metadata, normalise loudness, upload, publish, or "fix" video. It does not integrate with
any platform API. See `docs/specification/PREFLIGHTQC-V1-SPEC.md` §20 for the locked
non-goals list, and `docs/FUTURE.md` for ideas deliberately deferred.

## Where the documents live

| Document | Path |
| --- | --- |
| Authoritative V1 product specification | `docs/specification/PREFLIGHTQC-V1-SPEC.md` |
| Source register (all platform + dependency research) | `docs/sources/SOURCE-REGISTER.md` |
| Original research source material (PDF) | `docs/sources/{meta,tiktok,youtube,linkedin,mediainfo,ffmpeg}/` |
| System architecture | `docs/architecture/ARCHITECTURE-V1.md` |
| Tech stack decision (proposed) | `docs/architecture/ADR-001-TECH-STACK.md` |
| **Implementation plan (primary deliverable)** | `docs/planning/IMPLEMENTATION-PLAN-V1.md` |
| Test strategy | `docs/testing/TEST-STRATEGY-V1.md` |
| Licensing and release gate | `docs/licensing/LICENSING-GATE-V1.md` |
| Deferred scope | `docs/FUTURE.md` |

## Accuracy posture

PreflightQC validates files against the technical rules contained in the selected
PreflightQC preset. It does not and cannot guarantee acceptance by Instagram, TikTok,
YouTube, or LinkedIn. Every rule carries a source reference, a confidence level, and a
last-verified date. Where authoritative sources conflict, the conflict is preserved and
surfaced rather than silently resolved.

## Legal

Dependency licensing analysis in `docs/licensing/LICENSING-GATE-V1.md` is engineering
research, **not legal advice**. Commercial licence, EULA, and third-party notice review by
a qualified software-IP attorney is a hard release prerequisite.
