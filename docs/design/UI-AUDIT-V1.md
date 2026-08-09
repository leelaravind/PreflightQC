# PREFLIGHTQC — UI/UX AUDIT (PRE-REFINEMENT)

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Baseline commit | `98aa3255fda5548b87390d25d24f4d04fe774603` |
| Method | Real widgets rendered by `tools/capture_screens.py`, driven with a real batch over real media using the bundled ffprobe n8.1.2 and MediaInfo 26.05 |
| Evidence | `docs/design/screens/before/` — 11 captured states, plus headless behavioural probes |
| Purpose | Plan §4 — audit every customer-facing surface **before** redesign |

Nothing below is inferred from reading code alone. Every finding is visible in a capture
or reproducible from a recorded probe.

---

## 1. THE FINDING THAT MATTERS MOST

### F-1 — A zero-byte file reports **PASS**

Reproduced headlessly against the Instagram Reels preset with the real inspectors:

| File | Status shown | Checks passed | Unknown |
| --- | --- | --- | --- |
| `93_zero_bytes.mp4` (0 bytes) | **PASS** | 1 | 21 |
| `92_not_media.mp4` (43 bytes, not a video) | **PASS** | 1 | 21 |
| `94_corrupt_moov.mp4` | FAIL | 1 | 20 |

Visible in `05-mixed-batch.png`: the row `92_not_media.mp4` renders as **✓ Pass** in green,
while the Metadata tab for that same file (`09-metadata-tab.png`) shows *every* property as
`UNDETERMINED` and a file size of 43 bytes.

**This is not a severity-model defect.** The model is behaving exactly as specified:
`UNKNOWN` never fails, and missing metadata never auto-fails (spec §7.1, §23, S-3). The
single "passed" check is a maximum-file-size rule, which a zero-byte file satisfies
trivially and truthfully.

It is a **presentation** defect, and a serious one. The product's most prominent output —
the status column — tells a video professional that an empty file is fine. The first time
that happens on a real delivery, every other verdict the tool has ever given becomes
suspect.

**Constraint on the fix.** Plan §8 forbids changing severity semantics, and the exported
status must stay canonical. So the fix must be presentational only: derive an
*inconclusive* qualifier from data already present, and never alter `FileStatus`.

**Predicate.** A probe over the six error-corpus files shows one clean discriminator:

| File | `primary_video` established | Video codec KNOWN |
| --- | --- | --- |
| `01_h264_…` conformant | yes | yes |
| `90_truncated` | yes | yes |
| `91_header_only` | yes | yes |
| `92_not_media` | **no** | **no** |
| `93_zero_bytes` | **no** | **no** |
| `94_corrupt_moov` | **no** | **no** |

If the inspection could not establish that the file contains a video stream at all, a PASS
verdict is vacuous. That is principled, explainable to a user in one sentence, and derived
entirely from existing normalised data.

### F-2 — An inspector can fail completely and the user is never told

For `92`, `93` and `94`, ffprobe fails outright and only MediaInfo returns anything. The
number of diagnostic notes surfaced to the user in all three cases is **zero**.

`docs/FUTURE.md` §3A.1b anticipated wanting a degraded-inspection indicator. The audit
finds the situation is worse than recorded there: the diagnostics channel carries nothing
at all for these files, so no amount of UI work on diagnostics would have surfaced it.
F-1's inconclusive treatment is what actually closes this for the user.

---

## 2. FIRST-RUN AND WORKFLOW

Evidence: `01-empty-state.png`, `02-files-loaded.png`, `03-preset-selected.png`.

| # | Finding | Severity |
| --- | --- | --- |
| F-3 | **The empty state is blank.** Two large empty panes and a table with headers. The only instruction is a 12-px status-bar line at the very bottom edge: *"Drop video files or folders here to begin."* Plan §7 requires a new user to understand what to do without documentation; this does not meet it. | High |
| F-4 | **The workflow is not expressed anywhere.** ADD → PRESET → CHECK → REVIEW → EXPORT exists only as a row of equally-weighted buttons. Nothing indicates order, and the final step (export) is the least prominent control in the window. | High |
| F-5 | **No product identity.** No wordmark, no publisher, nothing but the window title. Plan §11 requires ITISYOU attribution. | Medium |
| F-6 | **The default preset is arbitrary** — LinkedIn CTV Ads, first alphabetically. A user who forgets to change it validates against a preset they never chose. | Medium |
| F-7 | **Detail pane shows two empty tabs at rest.** Findings and Metadata are visible and blank before anything has been checked. | Low |
| F-8 | **The progress bar is always present**, full width, empty and unlabelled when idle. | Low |

## 3. THE PRESET SELECTOR

| # | Finding | Severity |
| --- | --- | --- |
| **F-9** | **The platform name is duplicated in 9 of 12 presets.** The selector renders `f"{platform} — {display_name}"`, but nine `display_name` values already begin with the platform. Result: *"LinkedIn — LinkedIn — Connected TV (CTV) Ads"*, *"TikTok — TikTok — Studio / web upload"*, *"YouTube — YouTube — Shorts"*. Visible in `01-empty-state.png`. | **High** |
| F-10 | **The ruleset version and verification date are only in the status bar**, shown once on selection and then overwritten by the next message. A preset's `last_verified` date is a trust signal and should be persistent. | Medium |
| F-11 | **Preset caveats are never shown.** `PresetOption.caveats` is built and then never rendered anywhere in the UI. TikTok's "publishes four different maximum durations across overlapping upload paths" is exactly the context a user needs when choosing. | Medium |
| F-12 | Custom profiles are indistinguishable from shipped presets apart from the word "Custom profile" in the platform position. | Low |

## 4. THE BATCH TABLE

Evidence: `05-mixed-batch.png`.

| # | Finding | Severity |
| --- | --- | --- |
| F-13 | **The Result column truncates**: "1 warning, 4 …", "1 fail, 3 warning…". The column carries the per-file summary and is the second thing a user reads; it is clipped for most rows. | High |
| F-14 | **No row is selected when a batch finishes**, so the detail pane stays empty until the user clicks. The first thing worth showing — the first failure — is one click away and unhinted. | Medium |
| F-15 | Status markers are inconsistent in weight: `✓`, `▲`, `!`, `—` mix a tick, a filled triangle, an ASCII bang and an em dash. They read as different families rather than one set. | Medium |
| F-16 | **No sort, no filter, no grouping.** Sorting is off deliberately and that is defensible, but in a 200-file batch there is no way to see only the failures. | Medium |
| F-17 | Long filenames will elide with no tooltip on the Result column and only a path tooltip on the name column. | Low |
| F-18 | The five summary counters always render all five, including `Not Applicable: 0` and `Not Inspected: 0`, competing with the export buttons for the same footer strip. | Low |

## 5. THE FINDINGS PANE

Evidence: `08-fail-detail.png`.

| # | Finding | Severity |
| --- | --- | --- |
| F-19 | **Source URLs dominate.** Each finding block devotes three wrapped lines to a raw `https://developers.facebook.com/docs/instagram-platform/…` string. Traceability is a product requirement, but it currently outweighs the explanation visually. | High |
| F-20 | **Machine values leak into user copy.** *"Detected: False"*, *"Expected: required: True"* (double colon), *"Expected: recommended: 0.5625"* for an aspect ratio. A video professional reads 9:16, not 0.5625. | High |
| F-21 | **The same property appears twice with no way to tell why.** Two "Display aspect ratio" findings — one a recommendation, one an eligibility rule — render identically apart from the sentence beneath. The classification that makes them different is never shown. | High |
| F-22 | **Findings are in rule order, not severity order.** The FAIL is at the top by luck; nothing guarantees it. | Medium |
| F-23 | The "N checks passed" line is the only positive signal and is rendered in body text at the top, easily missed. | Low |
| F-24 | Finding blocks have a coloured left border but no surface separation, so they run together when scrolled. | Medium |

## 6. THE METADATA PANE

Evidence: `09-metadata-tab.png`.

| # | Finding | Severity |
| --- | --- | --- |
| F-25 | **"could not be determined (no inspector reported this property)" is repeated on up to 40 rows**, wrapping to three lines each. The reason is worth stating once, not forty times. | High |
| F-26 | **45 flat rows with no grouping.** File, Container, Video and Audio properties run together in one undifferentiated list. | Medium |
| F-27 | **Raw values.** File size renders as `43` with the unit in the label; duration as a bare float. No human formatting. | Medium |
| F-28 | State is the raw enum (`UNDETERMINED`, `KNOWN`) with no legend explaining the difference between *not present in this file* and *we could not tell*, which is the distinction the whole severity model rests on. | Medium |

## 7. ABOUT, LEGAL AND BRANDING

Evidence: `13-about.png`, `13b-about-notices.png`.

| # | Finding | Severity |
| --- | --- | --- |
| F-29 | **No publisher.** ITISYOU appears nowhere in the product. | High (plan §11) |
| F-30 | **No support, legal or corresponding-source location.** The FFmpeg LGPL posture requires the corresponding-source location to be discoverable; the About dialog says texts are "included with the installed product" but names no location. | High (plan §15) |
| F-31 | The About tab is an unstyled `QTextBrowser` with no product identity. | Medium |
| F-32 | Inspector versions are shown, which is right, but the licence each runs under is not — despite the self-check already knowing it. | Low |

## 8. ACCESSIBILITY AND DESKTOP BEHAVIOUR

| # | Finding | Severity |
| --- | --- | --- |
| F-33 | **No accessible names on any control.** No `setAccessibleName`/`setAccessibleDescription` anywhere in the UI package, so a screen reader announces "button" for the primary action. | High |
| F-34 | **No tooltips** on the toolbar buttons or the preset selector. | Medium |
| F-35 | **No keyboard mnemonics or shortcuts.** No `&`-accelerators, no Ctrl+O / Ctrl+R / F5 equivalents; the only menu is Help. | Medium |
| F-36 | **No minimum window size.** The window can be resized until the toolbar clips. | Medium |
| F-37 | **Focus is the Qt default only.** No design decision has been made about focus visibility, which is the one accessibility affordance that cannot be replaced by anything else. | High |
| F-38 | Status colour is accompanied by a text label and a marker, which is correct and already meets "never colour alone" — **this one passes**. | — (pass) |
| F-39 | The severity palette has never been contrast-checked against its backgrounds. | Medium |
| F-40 | DPI scaling untested at 125/150/200%. | Medium |

## 9. WHAT IS ALREADY RIGHT

Worth recording so the refinement does not undo it:

- **Status is never colour-only.** `severity_style.py` pairs every colour with a text label
  and a marker, deliberately and with a comment explaining why.
- **One severity presentation table.** Colours and labels are centralised already; no widget
  hard-codes a severity string.
- **The view models are Qt-free** and testable headlessly — the refinement can add logic
  there without dragging Qt into the test path.
- **The UI thread does no I/O.** Scanning runs on a worker; the window stays responsive.
- **Provenance is shown per finding** — which inspector produced the value, and the source
  the rule came from. Presentation needs work; the substance is right and rare.
- **The metadata pane distinguishes KNOWN from UNDETERMINED** honestly, including for
  properties PreflightQC deliberately does not measure.

## 10. TEST COVERAGE GAP

**There are zero UI tests.** `pytest-qt` is a declared dev dependency and a `ui` marker is
registered in `pyproject.toml`, so the intent existed, but no test imports
`preflightqc.ui`. Every finding above was invisible to the 1,114-test suite — including
F-1, where a zero-byte file reports PASS.

---

## 11. SUMMARY

| Area | High | Medium | Low |
| --- | --- | --- | --- |
| Correctness of what the user is told | 2 | — | — |
| First run and workflow | 2 | 2 | 2 |
| Preset selector | 1 | 2 | 1 |
| Batch table | 1 | 3 | 2 |
| Findings pane | 3 | 2 | 1 |
| Metadata pane | 1 | 3 | — |
| About / branding / legal | 2 | 1 | 1 |
| Accessibility | 2 | 5 | — |
| **Total** | **14** | **18** | **7** |

The two findings in the first row are the ones that change what a user believes about their
file. Everything else is polish, hierarchy and accessibility — real work, but not work that
can mislead someone into shipping a broken delivery.
