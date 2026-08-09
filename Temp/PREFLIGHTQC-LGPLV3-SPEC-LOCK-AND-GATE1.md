# PreflightQC — LGPLv3 Spec-Lock Amendment + Gate-1 Continuation

## Purpose

Resolve the current GATE-1 blocker caused by the actual BtbN
`win64-lgpl-shared` FFmpeg build being LGPLv3 rather than the repository's
original LGPLv2.1 assumption.

This instruction explicitly authorises a controlled SPEC LOCK amendment.

It does NOT grant legal clearance for commercial release.

## Evidence / Current State

The supplied BtbN build:

- is Windows x64
- is shared
- has no `--enable-gpl`
- has no `--enable-nonfree`
- explicitly disables GPL libraries such as x264/x265/xvid
- carries `--enable-version3`
- enables `gmp` and `libaribb24`
- ships LGPLv3 licence text
- MediaInfo 26.05 has already passed dependency verification
- regression suite currently reports 979 passed, 3 skipped, 0 failed

The existing gate incorrectly assumes FFmpeg must remain LGPLv2.1.

## Decision

APPROVE OPTION B.

PreflightQC V1 may use the verified BtbN Windows x64 LGPL-shared FFmpeg /
ffprobe build under LGPLv3, provided all corresponding LGPLv3 obligations are
implemented and final attorney review remains mandatory before commercial
release.

Do NOT custom-build FFmpeg merely to force LGPLv2.1.

## Required Spec-Lock Changes

Update the authoritative repository documents consistently.

At minimum inspect/update:

- docs/specification/PREFLIGHTQC-V1-SPEC.md
- docs/licensing/LICENSING-GATE-V1.md
- docs/architecture/ADR-001-TECH-STACK.md where relevant
- docs/sources/SOURCE-REGISTER.md where dependency classification is recorded
- packaging/generate_manifest.py
- packaging/layout_check.py
- packaging/binaries.lock.json
- application About/licence notices
- draft EULA/licence references
- tests validating dependency/licence wording

Replace FFmpeg-specific LGPLv2.1 assumptions with the verified LGPLv3 posture.

Do NOT blindly global-replace text. Update only statements whose meaning
actually changes.

## FFmpeg Dependency Policy

Approved V1 posture:

- unmodified BtbN `win64-lgpl-shared` build
- Windows x64
- shared libraries
- ffprobe invoked as a separate process
- no `--enable-gpl`
- no `--enable-nonfree`
- no FFmpeg encoder shipped in V1
- no GPL/nonfree optional dependencies

`--enable-version3` is permitted.

`gmp` and `libaribb24` are permitted only as part of the verified LGPLv3 build
and must be recorded accurately in the dependency manifest/notices.

## libzvbi Correction

Re-evaluate `libzvbi` against the current authoritative FFmpeg source
classification.

If current FFmpeg `configure` does NOT classify libzvbi as GPL/nonfree and the
verified build remains LGPLv3 without `--enable-gpl`, correct the stale local
gate entry with source traceability.

Do not remove a prohibition merely to make the gate pass; document the
authoritative evidence supporting the correction.

## LGPLv3 Compliance

Update generated and shipped materials to identify the actual licence version.

At minimum plan/maintain:

- LGPLv3 licence text
- FFmpeg attribution
- exact FFmpeg build/version/configuration
- corresponding source availability matching shipped binaries
- required notices
- DLL replaceability / shared-library posture
- EULA carve-outs required by LGPL
- no conflicting reverse-engineering prohibition
- dependency manifest
- third-party notices

PySide6/Qt's existing LGPLv3 obligations remain separate and must also continue
to be tracked.

## Legal Gate

DO NOT mark attorney/legal review complete.

G-12/G-13 or their current equivalents remain HARD RELEASE GATES.

The engineering build may proceed before attorney review, but commercial
release may not be declared READY while those gates remain open.

## Re-verification

After amendments:

1. rerun dependency scanner against the actual installed ffprobe;
2. verify no GPL/nonfree configuration;
3. verify licence classification = accepted LGPLv3;
4. verify MediaInfo remains approved;
5. run licence/manifest tests;
6. run full regression suite.

If any technical/licensing engineering check fails, STOP and report.

## Automatic Gate-1 Continuation

If and ONLY if the amended dependency gate passes:

Immediately continue into the real Phase-1 Inspector Technical Spike and
GATE-1 defined in `docs/planning/IMPLEMENTATION-PLAN-V1.md`.

Do not require another user prompt.

Use the actual installed ffprobe and MediaInfo binaries.

Use legitimate real/synthetic media allowed by the test strategy.

Verify real extraction and normalization of:

- container
- duration
- streams
- codec/profile/level
- dimensions
- SAR/DAR
- frame rate
- bitrate
- pixel format
- scan/field metadata
- colour/HDR where available
- audio metadata

Test required error cases including corrupt/no-audio media, inspector
failure/timeout and batch isolation.

Missing/undetermined metadata stays UNKNOWN.

Inspector conflicts must be preserved according to the architecture.

Source media must remain unchanged.

Run Phase-1 tests, integration tests and the complete regression suite.

GATE-1 may pass only when every documented Phase-1 acceptance criterion passes
with real binaries.

## Documentation

Create/update:

`docs/reports/LGPLV3-SPEC-LOCK-REPORT.md`

and

`docs/reports/INSPECTOR-GATE-1-REPORT.md`

Record:

- exact documents changed
- reason for each spec-lock amendment
- authoritative dependency evidence
- FFmpeg licence/build result
- libzvbi classification decision
- MediaInfo status
- licence/manifest tests
- regression results
- real media tested
- Phase-1 results
- GATE-1 status
- remaining release gates
- spec deviations
- git status --short

## Git / Release Rules

Do NOT commit.
Do NOT push.
Do NOT publish.
Do NOT release commercially.

Do not modify unrelated product scope.

Final state must be one of:

`GATE-1 PASS — engineering gate cleared; legal/manual release gates remain open`

or

`GATE-1 BLOCKED — <exact unresolved reason>`