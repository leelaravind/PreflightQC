# PREFLIGHTQC — UI DESIGN SPECIFICATION V1

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Authority | Subordinate to `docs/specification/PREFLIGHTQC-V1-SPEC.md` and `docs/architecture/ARCHITECTURE-V1.md` |
| Implementation | **PySide6 / Qt Widgets.** Not a web application. Tokens are Python constants; styling is Qt Style Sheets and `QPalette`. |
| Scope | Presentation only. No rule, severity or engine behaviour changes. |
| Answers | The findings in `docs/design/UI-AUDIT-V1.md` |

---

## 1. VISUAL DIRECTION

### 1.1 Where this product actually lives

PreflightQC does not sit on a marketing page. It sits on an editor's second monitor, in a
dim room, next to DaVinci Resolve, Premiere and Media Encoder — all of which are dark,
neutral and dense. A grading suite is deliberately kept near 18% grey so nothing on the
walls or the screen distorts colour judgement.

So the direction is not "dark mode" as a style choice. It is **the register this product's
neighbours already use**, and matching it is what makes the tool feel like part of the
bench rather than a browser tab someone left open.

> **The instrument, not the dashboard.** A dashboard tells you how things are going. An
> instrument tells you a measurement and how much to trust it. PreflightQC is the second
> kind, and every decision below follows from that.

### 1.2 The three decisions that carry the identity

**1 — A neutral graphite surface with a single graticule-cyan accent.**
The greys are near-neutral with a very slight cool cast, the way measurement equipment is
finished. Exactly one interactive accent, taken from the cyan of a vectorscope graticule
rather than from a product palette. It is the only saturated colour in the interface that
is not a severity, so "this is something you can act on" never competes with "this is a
verdict".

**2 — Measured values are monospace. Everything we say about them is not.**
This is the typographic signature and it does real work. `1920x1080`, `h264`,
`n8.1.2-34-g9b6c8969e0`, `ig_reels.faststart`, `29.97 fps` — anything read out of the file
or naming a rule is set in mono. Explanations, labels and guidance are proportional. The
user can tell *what the file says* from *what PreflightQC says about it* without reading a
word, on every screen, forever.

It also costs nothing: both faces are already on the target OS, so no font ships, no
licence obligation is added, and the dependency gate is untouched.

**3 — The verdict readout.**
The five status counters currently sit in the footer as text, competing with the export
buttons. They become a single segmented readout, proportionally sized to the batch, always
in the same place and always in the same order. It is the one element that is allowed to
be striking, it is borrowed from the levels meters and scopes in the room, and it replaces
reading five numbers with recognising one shape.

Everything else stays quiet.

### 1.3 What this direction rejects

Not defaults to fall into, but specific temptations for this brief:

| Rejected | Why |
| --- | --- |
| Cream-and-serif "editorial" treatment | Belongs to a reading experience; this is a measurement tool used at speed |
| A bright acid accent on near-black | The current AI-design house style, and it fights the severity palette |
| Cards with elevation and generous padding | Turns a 200-file batch into scrolling. Density is a feature here |
| Gradients, glass, shadows as decoration | Nothing in a scope or a waveform monitor is decorated |
| Animated transitions between states | The user is waiting on ffprobe, not on us. Motion is limited to the progress readout and hover feedback |
| Numbered step markers (01 / 02 / 03) | The workflow is a sequence, but it is a *three-second* sequence. Numbering it is condescending |
| A light theme as well | Two themes is two things to keep correct. Recorded in `docs/FUTURE.md`, not built |

---

## 2. COLOUR

All values are defined once in `src/preflightqc/ui/design.py` and consumed from there.
No widget may contain a hex literal.

### 2.1 Surfaces and text

| Token | Value | Use |
| --- | --- | --- |
| `SURFACE_SUNKEN` | `#14171A` | Window background, behind panels |
| `SURFACE_BASE` | `#1B1F23` | Panels, tables, text views |
| `SURFACE_RAISED` | `#232830` | Toolbar, table headers, chips, cards |
| `SURFACE_OVERLAY` | `#2B313A` | Hover, menus, popups |
| `BORDER_SUBTLE` | `#2E343C` | Panel edges, grid lines |
| `BORDER_STRONG` | `#3B434D` | Control outlines, dividers that must read |
| `TEXT_PRIMARY` | `#E6EAEE` | Body and headings |
| `TEXT_SECONDARY` | `#A7B0B9` | Labels, column headers |
| `TEXT_MUTED` | `#7A848E` | Provenance, source lines, timestamps |
| `ACCENT` | `#4FB6C4` | Focus ring, selection, primary action, links |
| `ACCENT_HOVER` | `#63C6D3` | Hover |
| `ACCENT_PRESSED` | `#3C97A4` | Pressed |
| `ACCENT_SUBTLE` | `#16323A` | Selected row background |

### 2.2 Severity — semantics unchanged

Severity meaning is fixed by the specification and is **not** a design decision. What is a
design decision is making the five states distinguishable without relying on colour.

| State | Label | Marker | Foreground | Chip background | Chip border |
| --- | --- | --- | --- | --- | --- |
| PASS | `Pass` | `✓` | `#6FD08C` | `#17331F` | `#2C6B41` |
| WARN | `Warning` | `▲` | `#E8B44A` | `#3A2E12` | `#7A5C1B` |
| FAIL | `Fail` | `✕` | `#F2726A` | `#3B1B1A` | `#8C332D` |
| INFO | `Info` | `i` | `#9AA6B2` | `#232830` | `#3B434D` |
| UNKNOWN | `Unknown` | `?` | `#B79BE0` | `#2A2338` | `#574577` |

Three signals, always together: **marker, text label, colour.** Any one of them removed
still leaves the state readable — which is the requirement, not a nicety.

The marker set was rationalised. It was `✓ ▲ ! — ?`, mixing a tick, a triangle, an ASCII
bang and an em dash; they read as different families. It is now `✓ ▲ ✕ i ?`: a
confirmation, a caution triangle, a rejection, an information mark, a question. All render
in the default Windows UI font, so no glyph fallback and no icon font.

**A recommendation must never look like a hard failure.** WARN is amber and carries a
caution triangle. FAIL is red and carries a cross. They are not adjacent hues and not
adjacent shapes.

### 2.3 Inconclusive — a qualifier, not a sixth severity

Audit finding F-1: a zero-byte file reports **PASS**.

The severity model is right and does not change. What changes is that the presentation
layer now states when a pass is **vacuous** — when the inspection could not establish that
the file contains a video stream at all.

| | |
| --- | --- |
| Presented as | The canonical status, plus the word `Inconclusive` and the UNKNOWN colour family |
| Derived from | `media.primary_video` absent, or its codec not `KNOWN` |
| Changes `FileStatus` | **No** |
| Changes exported status | **No** — CSV and HTML report the canonical value |
| Changes any severity | **No** |

The rule stated in one line, which is also what the tooltip says:

> *No video stream could be read from this file, so there was nothing to check against the
> preset.*

### 2.4 Contrast is computed, not asserted

Every foreground/background pair defined above is checked against WCAG 2.1 contrast ratios
**by a test**, not by eye. Body text pairs must reach 4.5:1; large text and non-text
boundaries must reach 3:1. A palette edit that breaks a ratio fails the suite.

---

## 3. TYPOGRAPHY

### 3.1 Families

| Role | Stack | Why |
| --- | --- | --- |
| UI | `Segoe UI Variable Text`, `Segoe UI`, system default | Native on Windows 10/11, correct hinting at every scale factor, nothing to ship |
| Data | `Cascadia Mono`, `Consolas`, `Courier New` | Present on the target OS. Consolas is on every supported Windows |

**No font is bundled.** Shipping a display face to add personality would add a licence
obligation to a product whose licensing gate is the hardest part of its release, in
exchange for a look nobody asked for.

### 3.2 Scale

Points, because Qt sizes type in points and Windows scaling is applied on top.

| Token | Size | Weight | Use |
| --- | --- | --- | --- |
| `TYPE_DISPLAY` | 20 pt | 600 | Product name in About |
| `TYPE_TITLE` | 13 pt | 600 | Dialog and section headings |
| `TYPE_HEADING` | 10.5 pt | 600 | Panel headers, finding property names |
| `TYPE_BODY` | 9 pt | 400 | Default UI text |
| `TYPE_LABEL` | 8.5 pt | 500 | Column headers, field labels, chips |
| `TYPE_CAPTION` | 8 pt | 400 | Provenance, source lines, rule IDs |

Line height 1.45 for prose, 1.2 for tabular text. Letter-spacing `+0.04em` on chips and
column headers only — the one place where small uppercase text needs it.

### 3.3 The monospace rule

| Monospace | Proportional |
| --- | --- |
| Detected values | Explanations |
| Expected values | Property names |
| Codecs, containers, profiles | Guidance and captions |
| Dimensions, rates, bitrates, durations | Preset and platform names |
| Rule IDs, inspector versions, hashes | Everything else |

Applied consistently, this is what lets a user skim a findings pane and separate evidence
from commentary without reading.

---

## 4. SPACING, RADIUS, DIMENSION

### 4.1 Spacing scale

`2, 4, 6, 8, 12, 16, 20, 24, 32, 40` px. Nothing between; a value not on the scale is a bug.

| Context | Value |
| --- | --- |
| Window margin | 12 |
| Section gap | 12 |
| Control gap in a group | 6 |
| Group gap in the toolbar | 20 |
| Panel padding | 12 |
| Chip padding | 1 / 6 |
| Finding block padding | 10 / 12 |
| Table cell padding | 4 / 8 |

### 4.2 Radius

| Token | Value | Use |
| --- | --- | --- |
| `RADIUS_CHIP` | 2 px | Status chips |
| `RADIUS_CONTROL` | 3 px | Buttons, inputs, combo boxes |
| `RADIUS_PANEL` | 4 px | Panels, dialogs, finding blocks |

Nothing is more rounded than 4 px. Instruments have edges.

### 4.3 Dimensions

| Element | Value |
| --- | --- |
| Default control height | 28 px |
| Primary action height | 30 px |
| Toolbar height | 46 px |
| Table row height | 28 px |
| Status readout height | 26 px |
| Minimum window | **960 × 640** |
| Default window | 1240 × 820 |
| Splitter default | 58% batch / 42% detail |

The minimum window size is a fix for audit F-36: the window could previously be resized
until the toolbar clipped.

---

## 5. COMPONENTS

### 5.1 Toolbar — the workflow, in order

Three groups, left to right, separated by a 20 px gap and a hairline divider, in workflow
order. Grouping *is* the instruction; no numbered badges, no wizard.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [Add files…] [Add folder…] [Clear] │ Preset [ Instagram Reels        ▾] │ [▶ Run check] [Cancel] │
│  ── 1. bring files in ────────────  ── 2. choose the spec ──────────────  ── 3. check ─────────── │
└──────────────────────────────────────────────────────────────────────────────┘
```

- **Run check** is the only filled accent button in the window. Everything else is a
  bordered secondary. One primary action per screen.
- The preset combo grows; the buttons do not.
- Every button gets a keyboard mnemonic and a tooltip naming its shortcut.

### 5.2 Empty state — the fix for F-3 and F-4

The blank pane is replaced by a centred panel in the batch area:

```
        ┌─────────────────────────────────────────────┐
        │                                             │
        │            Drop video files here            │
        │        or use Add files / Add folder        │
        │                                             │
        │   1  Add the files you are about to deliver │
        │   2  Choose the preset for the destination  │
        │   3  Run check, review findings, export     │
        │                                             │
        │   Nothing leaves this machine. Source files │
        │   are opened read-only and never modified.  │
        └─────────────────────────────────────────────┘
```

The numbers earn their place here and nowhere else: this **is** a sequence, and it is the
one moment the user does not yet know the order. The privacy line is on the first screen
because it is the product's main differentiator and the thing a professional most wants
confirmed before pointing a tool at a client master.

### 5.3 Preset selector

- Label reads `Platform — Preset name`, with the platform prefix stripped when the preset
  name already begins with it. Fixes F-9, which affected 9 of 12 presets.
- Beneath the toolbar, a persistent one-line **preset context strip**:
  `Instagram Reels · rules 2026-08-09.1 · sources verified 2026-08-09 · 21 rules`
  This fixes F-10 — the verification date is a trust signal and must not be a status-bar
  message that the next message overwrites.
- Where a preset carries caveats, an `i` chip in the strip reveals them (F-11). TikTok's
  "publishes four different maximum durations across overlapping upload paths" is exactly
  what a user needs *while choosing*, not after.
- Custom profiles are grouped under a `Custom profiles` separator.

### 5.4 Batch table

| Column | Width | Content |
| --- | --- | --- |
| Status | fixed to content | Status chip: marker + label |
| File | stretch | Filename, elided middle; full path as tooltip |
| Result | fixed, ≥ 220 px | Per-file summary, never truncated (F-13) |

- Selected row: `ACCENT_SUBTLE` background with a 2 px `ACCENT` left edge.
- Alternating row tint at 3% to keep long lists trackable.
- On completion, the first row with the worst status is selected automatically (F-14), so
  the detail pane opens on the thing that matters.
- A **filter strip** above the table: `All / Fail / Warning / Unknown / Pass`, as toggle
  chips carrying live counts (F-16).

### 5.5 Status readout — the signature element

Replaces five loose footer counters.

```
 6 files   ┃████████████▌▌▌▌▌▌▓▓▓▓░░░░┃   ✕ 3 Fail   ▲ 2 Warning   ✓ 1 Pass
```

- A single horizontal bar segmented in fixed order **Fail → Warning → Unknown → Pass →
  Not inspected**, each segment proportional to its count.
- Counts are printed beside it with marker and label, so the bar is never the only signal.
- Zero-count states are omitted from the legend but the order never changes, so the shape
  is learnable.
- During a run the bar doubles as progress: unchecked files render as an unfilled track.

### 5.6 Findings pane

Rebuilt around the audit findings F-19 to F-24.

```
┌────────────────────────────────────────────────────────────┐
│ ✕ Fail   Fast start (moov at front)          Hard requirement │
│                                                              │
│   Detected   not enabled                                     │
│   Required   enabled                                         │
│                                                              │
│   The moov atom must be at the front of the file so playback │
│   can start before the whole file has downloaded.            │
│                                                              │
│   mediainfo · General.IsStreamable        ig_reels.faststart │
│   Instagram Reel specifications, verified 2026-08-09    ⌄    │
└────────────────────────────────────────────────────────────┘
```

- **Ordered by severity**, Fail first (F-22).
- **The classification is shown** — `Hard requirement`, `Recommendation`, `Eligibility`,
  `Documented limit` — as a right-aligned label. This is what makes two same-named findings
  distinguishable (F-21), and it is also what tells a user that a recommendation is not a
  blocker.
- **Detected / Required** as an aligned two-column readout in mono, not sentences. The
  label switches on classification: `Required` for hard requirements, `Recommended` for
  recommendations, `For eligibility` for eligibility rules — which removes the
  `Expected: required: True` double-colon (F-20).
- **Values are humanised**: `0.5625` → `9:16 (0.5625)`, `False` → `not enabled`,
  `3.0 s` → `3.0 s`. Formatting lives in the view model, is Qt-free, and is tested.
- **Provenance collapses.** The inspector field and rule ID stay visible in caption type;
  the full source title, URL and access date live behind a disclosure control (F-19). The
  traceability requirement is met — the URL is one click away and in every export — without
  three wrapped lines of URL per finding.
- A **passing summary** heads the pane: `17 of 21 checks passed` (F-23).

### 5.7 Metadata pane

- Grouped under **File / Container / Video / Audio** headers (F-26).
- `UNDETERMINED` renders as a compact `Not determined` chip. The explanation appears **once**
  above the table, not on forty rows (F-25). A per-row reason remains as a tooltip where it
  is specific — for example the deliberate V1 gaps.
- Values humanised: `43` → `43 bytes`, `104857600` → `100.0 MB (104,857,600 bytes)` (F-27).
- A one-line legend distinguishes the three states, because that distinction is the whole
  severity model (F-28):
  `Known — read from the file · Not present — the file does not carry it · Not determined — PreflightQC could not read it`

### 5.8 Buttons, inputs, tabs, dialogs

| State | Treatment |
| --- | --- |
| Secondary rest | `SURFACE_RAISED` fill, `BORDER_STRONG` 1 px, `TEXT_PRIMARY` |
| Secondary hover | `SURFACE_OVERLAY` fill |
| Secondary pressed | `SURFACE_SUNKEN` fill |
| Primary rest | `ACCENT` fill, `SURFACE_SUNKEN` text |
| Disabled | 45% opacity, no border change — never invisible, clearly inert |
| **Focus** | **2 px `ACCENT` outline, 1 px offset, on every focusable control, never removed** |

Dialogs use `SURFACE_BASE`, a 13 pt title, 16 px padding and a right-aligned button row.

---

## 6. ACCESSIBILITY

Addresses audit F-33 to F-40. These are requirements, not aspirations.

| # | Requirement | How it is met |
| --- | --- | --- |
| A-1 | Status never conveyed by colour alone | Marker + label + colour on every chip |
| A-2 | Visible keyboard focus everywhere | 2 px accent outline; no `outline: none` anywhere |
| A-3 | Every control has an accessible name | `setAccessibleName` on all interactive widgets; asserted by test |
| A-4 | Every control has a tooltip | Tooltip names the action and its shortcut |
| A-5 | Full keyboard operation | Mnemonics on all buttons; `Ctrl+O` add files, `Ctrl+Shift+O` add folder, `F5` run, `Esc` cancel, `Ctrl+E` export report, `Ctrl+Shift+E` export CSV |
| A-6 | Body text ≥ 4.5:1, large text and boundaries ≥ 3:1 | Computed by test over the token table |
| A-7 | No text clipping | Elide with tooltip; Result column has a minimum width |
| A-8 | Long filenames | Middle elision preserves the extension, which is the part that matters |
| A-9 | Minimum window size | 960 × 640, enforced by `setMinimumSize` |
| A-10 | DPI scaling | No pixel-fixed text containers; verified by rendering the full state set at 100 / 125 / 150 / 200% |
| A-11 | Table semantics | Row selection, header labels, `setAccessibleDescription` carrying the row's status |

---

## 7. HIGH-DPI

- Sizes are in points for type and layout-relative units for spacing; only borders and
  radii are fixed pixels, where sub-pixel scaling is imperceptible.
- No bitmap assets, so nothing to provide at 2×. Markers are text glyphs.
- Verified by re-rendering every captured state at 100%, 125%, 150% and 200% via
  `tools/capture_screens.py --scale`, and inspecting for clipping and overlap.

---

## 8. IMPLEMENTATION RULES

1. **`src/preflightqc/ui/design.py`** holds every token. Qt-free, so tokens and contrast
   ratios are testable headlessly.
2. **`src/preflightqc/ui/theme.py`** turns tokens into a `QPalette` and one application
   style sheet. Qt-only, UI layer.
3. **No hex literal outside `design.py`.** Asserted by test.
4. **No platform name or threshold in the UI package.** The existing architecture test
   already enforces this and continues to.
5. **No new runtime dependency.** No icon font, no bundled typeface, no theming library.
6. Formatting and ordering logic goes in `viewmodels.py`, which is Qt-free and tested; the
   widgets render what they are given.
7. Severity semantics are untouched. The presentation layer may add qualifiers; it may not
   change a status or a severity.

---

## 9. WHAT THIS SPEC DOES NOT DO

- No light theme. Recorded in `docs/FUTURE.md`.
- No icon set. Text markers only — no asset pipeline, no font licence, no 2× variants.
- No animation beyond the progress readout and hover feedback.
- No layout persistence between sessions.
- No change to the exported HTML report's light, printable styling. A dark application and
  a printable report is the correct pairing, not an inconsistency.
