# PreflightQC V1 — Final Pre-Build Implementation Plan

## Status

FINAL PRODUCT REFINEMENT PHASE

This phase begins from the current engineering baseline:

- GATE-1 PASS with real ffprobe + MediaInfo
- 1,114 tests passed / 3 skipped / 0 failed
- mypy clean
- ruff clean
- G-1 through G-10 and G-13 passed
- final commercial build NOT authorised
- legal/manual release gates remain open

This phase must end at:

FINAL PRE-BUILD REVIEW READY

It must NOT create or release the final customer build.

---

# 1. Mission

Take the technically working PreflightQC V1 application and prepare it for final human approval.

Work includes:

1. stable Git checkpoint
2. complete UI/UX audit
3. visual design specification
4. PySide6 UI refinement
5. customer-facing copy refinement
6. branding integration
7. accessibility/usability refinement
8. complete workflow validation
9. commercial/store-readiness preparation
10. legal/support/source-link preparation
11. regression/security/privacy verification
12. final pre-build audit

STOP before final production packaging.

---

# 2. Hard Product Boundaries

Do NOT add:

- AI functionality
- cloud processing
- accounts/login
- licence-key activation
- telemetry
- analytics
- network-dependent core functionality
- social-platform APIs
- video upload
- video modification
- encoding/transcoding
- automatic repair
- subscription infrastructure
- backend services
- macOS/mobile support

PreflightQC remains:

INSPECT → VALIDATE → EXPLAIN → REPORT

and operates offline.

---

# 3. Preserve Stable Baseline

Before UI/product refinement:

- inspect git status
- preserve all current engineering work
- verify current tests
- verify GATE-1 report
- verify release audit
- verify dependency state

Create an appropriate development checkpoint commit before substantial UI changes.

Do NOT push unless explicitly authorised.

Record baseline commit hash.

---

# 4. UI Audit

Audit every customer-facing PySide6 surface before redesign.

Inspect:

- application shell
- initial/empty state
- file picker
- folder picker
- drag/drop
- preset selector
- batch list
- scan controls
- progress state
- results
- PASS state
- WARN state
- FAIL state
- UNKNOWN/INFO state
- detailed finding view
- corrupt-file state
- inspector-error state
- cancellation
- custom profiles
- report/export flow
- settings if present
- About
- licence/legal information
- dialogs
- tooltips
- keyboard behaviour
- resizing
- DPI/scaling
- accessibility

Document findings before implementation.

---

# 5. Design Specification

Create:

docs/design/UI-DESIGN-SPEC-V1.md

Define a consistent system for:

- visual direction
- typography
- type scale
- spacing scale
- margins/padding
- component dimensions
- visual hierarchy
- backgrounds/surfaces
- borders
- buttons
- inputs
- selectors
- tables/lists
- status indicators
- icons
- dialogs
- progress indicators
- empty states
- error states
- focus states
- hover/pressed/disabled states
- accessibility
- high-DPI behaviour

Use the installed Anthropic frontend-design capability only as DESIGN GUIDANCE.

Do NOT convert PreflightQC into a web application.

Implementation remains PySide6 / Qt Widgets.

---

# 6. Visual Direction

Target:

Premium professional media-production utility.

Desired characteristics:

- precise
- restrained
- modern
- calm
- trustworthy
- production-oriented
- information-dense where useful
- visually polished

Avoid:

- generic AI interface
- colourful SaaS dashboard
- excessive gradients
- excessive glassmorphism
- giant cards
- unnecessary animations
- decorative clutter
- childish styling
- marketing-page aesthetics inside the desktop app

Functionality must remain more important than decoration.

---

# 7. Core Workflow Refinement

The primary workflow must be immediately understandable:

ADD VIDEO
→ SELECT PRESET
→ PREFLIGHT
→ REVIEW FINDINGS
→ EXPORT REPORT

Prioritise this workflow visually.

A new user should understand what to do without documentation.

Do not alter underlying rule behaviour merely for UI convenience.

---

# 8. Status Design

PASS / WARN / FAIL / INFO / UNKNOWN must be immediately distinguishable.

Do NOT rely on colour alone.

Use combinations of:

- icon
- text
- hierarchy
- status label
- accessible colour treatment

Never change severity semantics.

Recommendation must never visually imply hard failure.

UNKNOWN must clearly communicate insufficient/undetermined information.

---

# 9. Results Experience

Improve readability of technical results.

Users should quickly understand:

- which file has a problem
- overall result
- property checked
- detected value
- expected/recommended value
- severity
- explanation

Advanced technical information should remain accessible without overwhelming the primary workflow.

---

# 10. Customer-Facing Copy

Audit all visible text.

Copy must be:

- concise
- professional
- technically accurate
- non-alarmist
- understandable to video professionals

Never claim:

- guaranteed platform acceptance
- certification by Meta/TikTok/YouTube/LinkedIn
- perfect detection
- legal compliance guarantees

Preferred concept:

“Validated against the technical rules contained in the selected PreflightQC preset.”

---

# 11. Branding

Product:

PreflightQC

Publisher/brand:

ITISYOU

Use ITISYOU attribution subtly.

Do not make the utility look like the existing relaxation experience.

Prepare customer-facing URLs conceptually as:

itisyou.app/products/preflightqc
itisyou.app/products/preflightqc/support
itisyou.app/products/preflightqc/legal
itisyou.app/products/preflightqc/source

Do NOT add network dependency merely to display these references.

---

# 12. Activation Policy

V1 has:

NO customer account.
NO activation key.
NO online licence check.
NO licence server.

Paid distribution will be handled externally by the selected Merchant of Record.

The installed application remains offline-capable.

Do not implement anti-piracy infrastructure in this phase.

---

# 13. Privacy / Network Verification

Reconfirm:

- no telemetry
- no analytics
- no hidden HTTP requests
- no update checker
- no remote media processing
- no account services
- no unnecessary networking libraries

Do not reintroduce Qt Network, socket/SSL functionality or equivalent dependencies unless the locked specification explicitly requires them.

---

# 14. Marketplace Readiness

Prepare the product for later listing on Merchant-of-Record platforms such as Lemon Squeezy/Gumroad.

Do NOT publish anything.

Ensure PreflightQC presents as substantive professional software, not a low-effort AI wrapper.

Claude/AI development tooling is not the product proposition.

Prepare material needed later:

- accurate product description
- feature list
- supported OS
- system requirements
- privacy/offline statement
- screenshots checklist
- support information
- limitations
- version
- refund-policy dependency note
- licence/EULA dependency note

Do not fabricate testimonials, reviews, customer counts or performance claims.

---

# 15. Legal / Dependency Preparation

Preserve existing dependency decisions.

Verify customer-facing material accurately represents:

- FFmpeg/ffprobe LGPLv3 posture
- MediaInfo BSD posture
- PySide6/Qt LGPLv3 posture
- Microsoft runtime redistribution
- third-party notices
- dependency manifest
- corresponding-source obligations

The corresponding-source public location is intended to use:

itisyou.app/products/preflightqc/source

Prepare configuration/documentation for this URL where appropriate.

Do NOT claim attorney approval.

G-12 remains OPEN.

---

# 16. Code Signing

Do NOT purchase certificates or credentials.

Do NOT final-sign the product.

Ensure packaging/signing infrastructure is ready for later G-11 completion.

Document:

- binaries requiring signatures
- installer requiring signature
- expected signing order
- verification commands
- timestamp requirements
- clean-machine validation dependency

G-11 remains OPEN until genuinely completed.

---

# 17. UI Implementation

After UI-DESIGN-SPEC-V1.md is complete:

implement the approved refinement.

Rules:

- preserve architecture
- Qt only in UI layer
- no rule-engine rewrites without defect justification
- no platform-rule invention
- no unnecessary dependency additions
- centralise styles/tokens where practical
- keep modules maintainable
- maintain deterministic behaviour

If a useful new feature is discovered:

record it in docs/FUTURE.md.

Do NOT implement it.

---

# 18. Testing

After refinement run:

- UI tests
- unit tests
- integration tests
- real inspector tests where appropriate
- complete regression suite
- mypy
- ruff
- packaging/static checks that do not create final release

Existing tests must not be weakened to accommodate redesign.

Add tests for genuine defects discovered during UI work.

---

# 19. Accessibility / Desktop Behaviour

Verify:

- keyboard navigation
- visible focus
- meaningful labels
- status not colour-only
- readable contrast
- text clipping
- long filenames
- long error messages
- minimum window size
- resizing
- common DPI scaling
- 100%, 125%, 150%, 200% scaling where feasible
- screen-reader-friendly Qt properties where practical

---

# 20. Human Review Package

Prepare a review package for the user.

Create:

docs/reports/FINAL-PREBUILD-AUDIT-V1.md

Include:

- UI changes
- before/after summary
- screens requiring human inspection
- workflow status
- accessibility status
- branding status
- copy status
- privacy/offline verification
- marketplace-readiness status
- dependency/licensing status
- code-signing status
- open manual gates
- test results
- known limitations
- FUTURE items
- git status

Where practical, create screenshots of the principal application states for human review.

Do not fabricate screenshots if environment limitations prevent them.

---

# 21. Required Human Review States

The user should be able to inspect at minimum:

1. first launch / empty state
2. files loaded
3. preset selected
4. scanning
5. PASS result
6. WARN result
7. FAIL result
8. mixed batch
9. detailed finding
10. corrupt/error state
11. custom profile
12. export/report experience
13. About/legal information

---

# 22. Final Pre-Build Gate

After all work above:

STOP.

Do NOT create the final customer release.

Do NOT:

- create final signed EXE
- create final signed installer
- publish source files
- upload to ITISYOU
- upload to Lemon Squeezy
- upload to Gumroad
- publish GitHub release
- declare commercial readiness
- mark legal review complete
- perform final clean-machine release validation against a non-final build

The next phase requires explicit human authorization:

FINAL BUILD APPROVED

---

# 23. Success Criteria

This phase passes only when:

- current functionality remains intact
- UI refinement is complete
- core workflow is clear
- all customer-facing states are polished
- branding is consistent
- no activation exists
- offline/privacy architecture remains intact
- no unwanted networking is introduced
- marketplace materials are prepared
- legal/source URLs are defined
- dependency notices remain accurate
- tests pass
- lint/type checks pass
- open legal/manual gates are honestly reported
- human review package exists

Final status must be:

FINAL PRE-BUILD REVIEW READY

or

FINAL PRE-BUILD BLOCKED — <reason>

Never output FINAL BUILD APPROVED yourself.

Only the human user may issue that authorization.