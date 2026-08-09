# PREFLIGHTQC — FINAL PRE-BUILD AUDIT (V1)

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Phase | Final product refinement, per `Temp/PREFLIGHTQC-FINAL-PREBUILD-IMPLEMENTATION-PLAN.md` |
| Baseline commit | `98aa3255fda5548b87390d25d24f4d04fe774603` |
| Tests | **1266 passed, 3 skipped, 0 failed** (was 1114). **130 of them are new UI tests; there were none.** |
| Static analysis | mypy clean (55 files) · ruff clean (`src tests tools packaging spikes`) |
| Package | Verification build only — 268 files, 231.8 MB, **unsigned, no installer, not released** |
| **Status** | **FINAL PRE-BUILD REVIEW READY** |
| Open gates | **G-11 signing, G-12 attorney, corresponding-source hosting (bundle staged 2026-08-09), Phase 13 clean-machine** — all human. MS runtime notice resolved 2026-08-09 from the CPython licence's Additional Conditions; EULA pass-through confirmation folded into G-12 |

---

## 1. WHAT THIS PHASE FOUND

The plan asked for polish. The audit found two things that were not cosmetic, and they are
the reason to read this document rather than skim it.

### 1.1 A zero-byte file reported **PASS**

Reproduced against the Instagram Reels preset with the real bundled inspectors:

| File | Was shown as | Checks passed | Unknown |
| --- | --- | --- | --- |
| `93_zero_bytes.mp4` (0 bytes) | **✓ Pass** | 1 | 21 |
| `92_not_media.mp4` (43 bytes, not a video) | **✓ Pass** | 1 | 21 |

The severity model was behaving exactly as specified — `UNKNOWN` never fails, missing
metadata never auto-fails — and the single "passed" check was a maximum-file-size rule
that a zero-byte file satisfies truthfully. **The engine was right and the interface was
lying.** A QC tool that shows a green Pass for an empty file destroys trust in every other
verdict it has ever given.

Fixed in the presentation layer only. When the inspection cannot establish that a file
contains a video stream at all, the interface shows **Inconclusive** and says why:

> No video stream could be read from this file, so there was nothing to check against the
> preset.

**No severity changed. No `FileStatus` changed. Exports still record the canonical
status.** The predicate is evidence-based — no readable video stream — and it separates the
error corpus exactly: `92`, `93` and `94` are inconclusive; the truncated and header-only
files, which *are* readable, are not.

### 1.2 Custom profiles could be saved and never seen again

`compile_profile` was written, tested, and **never called by the application**. A user
could create a custom delivery specification, save it, and it would not appear in the
preset selector — the store, the compiler and the export/import were all complete apart
from the line that joined them to the interface.

Fixed: saved profiles are compiled and appear under a `Custom profiles` separator, and one
unreadable profile no longer costs the user every other preset.

**What is still missing is the way to create one.** There is no profile editor and no
import action; a profile must be placed in `%LOCALAPPDATA%\PreflightQC\profiles` as a
file. Building an editor is a new surface, and the plan is explicit that a newly discovered
feature is recorded rather than implemented — so it is recorded in `docs/FUTURE.md` §3A.3
and was flagged as **D-8** in the marketplace material.

**D-8 RESOLVED (2026-08-09, human decision).** V1 ships without an in-app editor. Custom
profiles are described in every customer-facing surface — the marketplace feature list,
its limitations section, and the README — as an advanced, file-based capability: a
manually authored or supplied JSON profile file. The JSON profile functionality stays as
built and tested; the editor remains deferred scope in `docs/FUTURE.md` §3A.3.

---

## 2. THE UI AUDIT AND WHAT CAME OF IT

`docs/design/UI-AUDIT-V1.md` records 39 findings against the pre-refinement build — 14
high, 18 medium, 7 low — each one visible in a real render or reproducible from a probe.

| Finding | Was | Now |
| --- | --- | --- |
| **F-1** | A zero-byte file shows PASS | Shows **Inconclusive**, with the reason |
| **F-2** | An inspector could fail completely with no signal to the user | Covered by the inconclusive treatment |
| **F-3** | Empty state was two blank panes and a 12-px status-bar hint | A panel naming the three steps and the privacy position |
| **F-4** | Workflow was an undifferentiated row of buttons | Three toolbar groups in order, one filled primary action |
| **F-5** | No product identity anywhere | Wordmark and `by ITISYOU` in the shell; publisher and URLs in About |
| **F-9** | **9 of 12 presets said their platform twice** — *"LinkedIn — LinkedIn — Connected TV (CTV) Ads"* | Fixed in the view model; the preset data was not touched |
| **F-10** | Ruleset version and verification date shown once, then overwritten | Persistent context strip under the toolbar |
| **F-11** | Preset caveats were built and never rendered | An `i` chip in the context strip, with the notes |
| **F-13** | Result column truncated to *"1 warning, 4 …"* | Minimum width; no truncation |
| **F-14** | Nothing selected when a batch finished | The worst-status row is selected automatically |
| **F-15** | Markers mixed `✓ ▲ ! —` from different families | One set: `✓ ▲ ✕ i ?` |
| **F-16** | No way to see only the failures | Filter chips with live counts |
| **F-19** | Raw source URLs took three wrapped lines per finding | Source title, date and confidence in caption type; URLs in the export |
| **F-20** | *"Detected: False"*, *"Expected: required: True"*, *"recommended: 0.5625"* | `Detected: no` / `Required: yes` / `Recommended: 9:16 (0.5625)` |
| **F-21** | Two identical-looking "Display aspect ratio" findings | Classification shown: `Hard requirement`, `Recommendation`, `Eligibility` |
| **F-22** | Findings in rule order | Ordered by severity, fails first |
| **F-25** | *"could not be determined…"* repeated on 40 rows | Stated once; rows show a compact `Not determined` |
| **F-26** | 45 flat metadata rows | Grouped File / Container / Video / Audio |
| **F-27** | File size rendered as `43` | `43 bytes`; `104.9 MB (104,857,600 bytes)` |
| **F-29/30** | No publisher, no support/legal/source locations | All four ITISYOU URLs in About, as text |
| **F-33** | No accessible names anywhere | Every control named and tooltipped, asserted by test |
| **F-35** | No mnemonics, no shortcuts | Mnemonics on every button; `Ctrl+O`, `F5`, `Esc`, `Ctrl+E` |
| **F-36** | Window resizable until the toolbar clipped | Minimum 960 × 640 |
| **F-37** | Focus was Qt default only | 2-px accent ring, never removed, asserted by test |
| **F-39** | Palette never contrast-checked | 21 pairs **computed** by test |

One finding is unchanged on purpose: **F-6**, the default preset is still the first
alphabetically. With no persistence and nothing to infer a preference from, any other
default would be invented. The persistent context strip now makes the active preset the
second-most prominent thing in the window, which addresses the risk without guessing.

---

## 3. BEFORE AND AFTER

Real renders of real widgets, driven by a real batch over real media with the bundled
ffprobe n8.1.2 and MediaInfo 26.05. Nothing is a mock-up.

| | Before | After |
| --- | --- | --- |
| Screens captured | `docs/design/screens/before/` (12) | `docs/design/screens/after/` (14 + INDEX) |
| Empty state | Two blank panes | Titled panel, three steps, privacy note |
| Batch table | Truncating, unselected, no filter | Filtered, auto-selected, full-width results |
| Findings | Wrapped URLs, machine values | Cards ordered by severity, humanised values, classification |
| Metadata | 45 flat rows, 40 repeated sentences | Four groups, one legend, compact states |
| About | Unstyled text, no publisher | Publisher, versions with licences, privacy, four URLs |
| Look | Qt default light | Neutral graphite instrument panel, one accent |

**Reproduce any of it:**

```
python tools/capture_screens.py --out docs/design/screens/after
python tools/capture_screens.py --out docs/design/screens/scale-2_0 --scale 2.0
```

---

## 4. SCREENS REQUIRING HUMAN INSPECTION

All 13 states the plan asks for exist. **Please look at these; they are the ones where
judgement, not a test, is the check.**

| # | State | File | Look for |
| --- | --- | --- | --- |
| 1 | First launch | `01-empty-state.png` | Would a new user know what to do? |
| 2 | Files loaded | `02-files-loaded.png` | |
| 3 | Preset selected | `03-preset-selected.png` | Context strip: is the verification date legible enough to be a trust signal? |
| 4 | Scanning | `04-scanning.png` | |
| 5 | Mixed batch | `05-mixed-batch.png` | **The main one.** Does the readout bar read at a glance? |
| 6 | PASS | `06-pass-detail.png` | |
| 7 | WARN | `07-warn-detail.png` | **Does a recommendation clearly not look like a failure?** |
| 8 | FAIL | `08-fail-detail.png` | Is Detected/Required scannable? Is the source line enough traceability on screen? |
| 9 | Metadata | `09-metadata-tab.png` | Is *not present* vs *not determined* clear? |
| 10 | Error / not inspected | `10-error-state.png` | |
| 11 | Custom profile | `11-preset-list.png` | The profile appears — file-based by decision D-8, see §1.2 |
| 12 | Exported report | `12-export-report.html` | **Open in a browser.** Light and printable by design |
| 13 | About / legal | `13-about.png`, `13b-about-notices.png` | Is the offline claim credible? Are the notices right? |

**Judgement calls worth a second opinion**, since a test cannot settle them:

1. **Dark interface.** Chosen to match the NLEs this tool sits beside in a dim edit suite.
   Defensible, and a real commitment — a light theme is recorded as FUTURE §3A.4, not built.
2. **Inconclusive as a displayed status.** It appears in the table, the filter chips and
   the readout but never in an export. If you would rather it were only a badge on a PASS
   row, say so — it is a contained change.
3. **Source URLs moved off the finding card.** Title, date and confidence stay on screen;
   the URL is in the export. If on-screen URLs matter more than density, that reverses.
4. **Filter chips instead of sortable columns.** Sorting stays off deliberately: file order
   is deterministic and re-sorting hides that.

---

## 5. WORKFLOW

`ADD VIDEO → SELECT PRESET → PREFLIGHT → REVIEW FINDINGS → EXPORT REPORT`

| Step | How the interface expresses it |
| --- | --- |
| Add | Left toolbar group; drag-and-drop; step 1 on the empty state |
| Preset | Centre group, growing combo, persistent context strip beneath |
| Preflight | The only filled accent button in the window; `F5` |
| Review | Worst-status row auto-selected; findings ordered by severity |
| Export | Footer, enabled only once results exist; `Ctrl+E` / `Ctrl+Shift+E` |

Rule behaviour is unchanged. No rule, threshold, severity or classification moved, and the
architecture test still enforces that no platform name or threshold exists anywhere in the
UI package.

---

## 6. ACCESSIBILITY

| # | Requirement | Status | How it is held |
| --- | --- | --- | --- |
| A-1 | Status never colour-alone | **PASS** | Marker + label + colour; unique markers and labels asserted |
| A-2 | Visible focus everywhere | **PASS** | 2-px accent ring; test asserts nothing suppresses focus without replacing it |
| A-3 | Accessible name on every control | **PASS** | Walks the widget tree and fails on any unnamed button, combo, table or view |
| A-4 | Tooltip on every control | **PASS** | Same walk |
| A-5 | Full keyboard operation | **PASS** | Mnemonics; `Ctrl+O`, `Ctrl+Shift+O`, `F5`, `Esc`, `Ctrl+E`, `Ctrl+Shift+E`, `F1` |
| A-6 | Contrast ≥ 4.5:1 body, ≥ 3:1 large | **PASS** | **21 pairs computed**, not asserted by eye. Lowest is 3.89:1 for a non-text boundary; lowest body pair 4.36:1 |
| A-7 | No text clipping | **PASS** | Verified in renders at four scale factors |
| A-8 | Long filenames | **PASS** | Middle elision preserves the extension |
| A-9 | Minimum window size | **PASS** | 960 × 640 enforced |
| A-10 | DPI scaling | **PASS** | Full state set re-rendered at **100%, 125%, 150%, 200%**; no clipping or overlap |
| A-11 | Row semantics for a screen reader | **PASS** | Each row carries its verdict and summary as an accessible description |

One honest limit: **no screen reader has actually been run against the build.** The Qt
accessibility properties are set and asserted; how NVDA or Narrator voices them is a
manual check that belongs in the clean-machine run-book.

---

## 7. BRANDING AND COPY

| Item | Status |
| --- | --- |
| Publisher | `ITISYOU`, in the shell and in About. Subtle, not a splash screen |
| Product URLs | All four defined in `preflightqc/__init__.py`, shown as text in About |
| Distinct from the relaxation product | A dark instrument panel is about as far from it as a Windows utility gets |
| Forbidden claims | Scanned across **every UI string, the EULA and the listing copy**. None present |
| Approved claim | *"Validated against the technical rules contained in the selected PreflightQC preset."* |

**A defect was found in the claim guard itself.** `contains_forbidden_claim` matched
substrings, so it flagged the EULA's *required* disclaimer — *"the Software is **not** …
certified by any platform"* — as a forbidden claim. The obvious way to make that pass would
have been to delete the disclaimer. The guard is now negation-aware within a sentence, with
tests in both directions, including that a negation in the *previous* sentence does not
launder a claim.

---

## 8. PRIVACY AND OFFLINE — RE-VERIFIED

| Check | Result |
| --- | --- |
| Networking imports anywhere in the application | **None** — checked against the syntax tree, not the text, because the prose deliberately contains these words |
| `Qt6Network.dll` in the package | **Absent** |
| `_socket`, `_ssl`, `libssl` | **Absent** — excluded from the freeze |
| Qt libraries shipped | **4**: Core, Gui, Widgets, Svg |
| Telemetry, analytics, update check, account, licence server | **None** |
| Displaying a URL | Text only. `setOpenExternalLinks(False)`, asserted by test |
| `libcrypto-3.dll` | Present and attributed. CPython's `hashlib` links it for message digests; it provides no transport |

Nothing was reintroduced. The verification build still ships no socket implementation at
all — a stronger statement than "we choose not to call one".

---

## 9. MARKETPLACE READINESS

`docs/marketing/MARKETPLACE-LISTING-V1.md` — prepared, **nothing published**.

Ready: product description, feature list, OS and system requirements, privacy statement,
screenshot checklist, limitations, trademark disclaimer, and an explicit list of what must
never appear.

Blocked, and each needs a human:

| Item | Blocker |
| --- | --- |
| Support / legal / source pages | Do not exist |
| Refund policy | Not written — a business decision |
| EULA | G-12 |
| Version number | `0.1.0-dev` must not appear in a listing |
| Certificate | G-11 |

The custom-profile feature bullet was blocked here as **D-8 — no in-app editor**. That is
now **resolved** (2026-08-09): the bullet describes custom profiles as an advanced,
file-based capability, and the same limitation is stated in the listing's §7.

No testimonials, review counts, user counts, speed claims or accuracy percentages appear
anywhere, because none exist.

---

## 10. LEGAL AND DEPENDENCIES

| Item | Status |
| --- | --- |
| FFmpeg / ffprobe | LGPL-3.0-or-later, named correctly in About and the notices |
| MediaInfo | BSD-2-Clause; libcurl deliberately not shipped |
| Qt / PySide6 | LGPLv3; four libraries, separate, unobfuscated, replaceable |
| Microsoft VC runtime | Attributed. Notice resolved 2026-08-09: `licenses/MS-VC-Redistributable.txt` is now a genuine Distributable Code notice grounded in the CPython licence's Additional Conditions, listing every shipped runtime file and both provenances (CPython, Qt wheels). EULA pass-through wording is confirmed under G-12 |
| Third-party notices | Generated from the built package; every file attributed |
| Corresponding source | **Location changed to `itisyou.app/products/preflightqc/source`** and now agrees with the About dialog. `hosting_status` says `NOT LIVE`, and a test fails if a URL is named without one |
| Attorney review | **G-12 OPEN. No clearance claimed anywhere.** |

---

## 11. CODE SIGNING

`docs/licensing/CODE-SIGNING-READINESS.md` — infrastructure ready, **G-11 OPEN**.

Recorded there: what gets signed and what deliberately does not; the signing order and why
signing before the installer matters; the verification commands; why timestamping is not
optional; and the OV-versus-EV decision. `packaging/sign.py verify` reports `UNSIGNED` and
exits non-zero, which is the correct report before a certificate exists.

**Get the certificate before booking the clean-machine validation** — two run-book criteria
are meaningless without it.

---

## 12. TESTS

| Suite | Result |
| --- | --- |
| Full regression | **1266 passed, 3 skipped, 0 failed** (was 1114) |
| **UI tests** | **130 — there were zero** |
| mypy | Success, 55 files |
| ruff | All checks passed |
| Packaging gates (verification build) | 11 of 11 pass |
| Documentation invariants | All hold |

**No existing test was weakened.** Where a new test disagreed with the code, the code
changed:

- `format_ratio(1.234567)` produced `21:17`, a name nobody uses. Rational approximation
  replaced with a curated lookup of ratios that appear in real delivery specifications.
- The architecture test caught a local variable named `meta` in the UI package. Renamed;
  the check kept.
- The claim guard flagged the EULA disclaimer. The guard was fixed, not the disclaimer.

---

## 13. KNOWN LIMITATIONS

1. **No in-app custom-profile editor** (§1.2) — **decided, D-8 resolved**: V1 ships
   file-based, described as an advanced capability everywhere customer-facing.
2. **No screen reader has been run** against the build.
3. **Default preset is arbitrary** — mitigated by the context strip, not solved.
4. **Findings show source title and date, not the URL** — URLs are in the export.
5. **Dark only.** FUTURE §3A.4.
6. **Native file dialogs follow the OS theme**, so a light Windows shows a light picker
   against a dark app. Normal for professional tools; noted rather than fixed.
7. **No layout persistence** between sessions.
8. Unchanged from V1: metadata only, no loudness/GOP/edit-list measurement, one preset per
   batch, first stream judged, Windows x64 only.

---

## 14. FUTURE ITEMS RECORDED, NOT BUILT

| Item | Where |
| --- | --- |
| Custom-profile editor and import action | `docs/FUTURE.md` §3A.3 |
| Light theme | §3A.4 |
| Degraded-inspection indicator | §3A.1b — now largely served by the inconclusive treatment |
| Inspector-disagreement prominence | §3A.2 |

---

## 15. `git status --short`

```
 M docs/FUTURE.md
 M docs/licensing/CORRESPONDING-SOURCE-PLAN.md
 M packaging/binaries.lock.json
 M src/preflightqc/__init__.py
 M src/preflightqc/reporting/claims.py
 M src/preflightqc/ui/about.py
 M src/preflightqc/ui/app.py
 M src/preflightqc/ui/main_window.py
 M src/preflightqc/ui/severity_style.py
 M src/preflightqc/ui/viewmodels.py
 M tests/packaging/test_corresponding_source.py
 M tests/reporting/test_reporting.py
?? Temp/
?? docs/design/
?? docs/licensing/CODE-SIGNING-READINESS.md
?? docs/marketing/
?? docs/reports/FINAL-PREBUILD-AUDIT-V1.md
?? src/preflightqc/ui/design.py
?? src/preflightqc/ui/theme.py
?? src/preflightqc/ui/widgets.py
?? tests/ui/
?? tools/capture_screens.py
```

`HEAD` is the baseline checkpoint `98aa325`. The refinement is uncommitted and unpushed,
pending this review.

---

## 16. WHAT WAS NOT DONE, DELIBERATELY

- No final customer executable, signed or otherwise.
- No installer built in this phase. The verification build ran with `--skip-installer`
  purely to prove the freeze and the licensing gates still pass after the UI work.
- Nothing signed, published, uploaded or released.
- No legal review marked complete.
- No clean-machine validation run against a non-final build.
- No activation, licence key, account or anti-piracy infrastructure.
- No new runtime dependency, no bundled typeface, no icon font.

---

## FINAL PRE-BUILD REVIEW READY

The next phase requires explicit human authorisation: **FINAL BUILD APPROVED**.

**D-8 is resolved** (2026-08-09): V1 ships without a custom-profile editor, and every
customer-facing mention describes custom profiles as an advanced, file-based capability.
