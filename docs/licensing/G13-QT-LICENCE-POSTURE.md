# PREFLIGHTQC — GUI FRAMEWORK LICENCE POSTURE (GATE G-13)

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Gate | **G-13** — "the GUI-framework licence posture is documented and satisfied: if LGPLv3 Qt ships, the shared-library mechanism is demonstrated (Qt libraries present as separate, unobfuscated, replaceable files) and LGPL-3.0 text plus notices ship" |
| Framework | Qt 6.8.1 via PySide6 6.8.1.1, **LGPL-3.0-only** |
| Engineering status | **SATISFIED and verified against the built package** |
| Legal status | **No professional review has occurred.** G-12 was amended 2026-08-09 to owner risk acceptance (ADR-G12); the legal questions here are documented as L-1/L-3 and remain unresolved. Nothing here claims legal clearance. |

---

## 1. THE QUESTION G-13 ASKS

Shipping LGPLv3 Qt in a closed-source commercial product is standard and lawful — but only
if the recipient can actually exercise the LGPL §4 right to **replace the covered library
with their own build and still run the application**. If Qt is welded into the executable,
or renamed, or compressed beyond recognition, that right is theoretical and the licence
is not satisfied.

So G-13 is not a paperwork gate. It is a question about the *shape of the package*, and it
is answered by what the package physically contains.

---

## 2. THE ANSWER, MEASURED FROM THE BUILT PACKAGE

### 2.1 Separate files

Qt ships as ordinary DLLs in `_internal/PySide6/`:

| Library | Purpose |
| --- | --- |
| `Qt6Core.dll` | core types and event loop |
| `Qt6Gui.dll` | windowing, painting, fonts |
| `Qt6Widgets.dll` | the widget set the UI is built from |
| `Qt6Svg.dll` | SVG icon rendering |

Plus the platform, style and image-format plugins under `_internal/PySide6/plugins/`, and
the binding runtime in `_internal/shiboken6/`.

### 2.2 Unobfuscated names

Every file keeps its upstream name. `Qt6Core.dll` is `Qt6Core.dll` — not `pfqcore.dll`,
not `core1.dll`. FFmpeg's LGPL checklist states the principle for the libav case
(`avcodec-MyProg.dll` acceptable, `MyProgDec.dll` not); the same reasoning governs Qt, and
the packaging gate enforces it for both.

### 2.3 Not compressed, not merged

- **UPX is disabled** in the PyInstaller spec (`upx=False` on both `EXE` and `COLLECT`),
  precisely because packing would obscure the library identity.
- **The build is one-dir, never one-file.** A one-file build unpacks to a temporary
  directory at each launch; replacing a library there is not something a user can
  meaningfully do. `packaging/layout_check.py` fails the build if `_internal/` is missing,
  which is what a one-file build looks like from the outside.

### 2.4 Replaceable in practice

A user can drop a compatible `Qt6Core.dll` into `_internal/PySide6/` and the application
loads it — normal Windows DLL resolution, no signature pinning, no integrity check that
would reject a substitute. §3.3 of the EULA states that we do not restrict this.

### 2.5 Licence texts and notices ship

| Artefact | Location in the package |
| --- | --- |
| LGPL-3.0 full text | `licenses/LGPL-3.0.txt` |
| GPL-3.0 full text | `licenses/GPL-3.0.txt` — LGPLv3 §"incorporates the terms and conditions of version 3 of the GNU General Public License" |
| Qt notice | `licenses/THIRD-PARTY-NOTICES.txt`, naming Qt, PySide6, LGPLv3 and the replaceability of the DLLs |
| In-product notice | About screen, rendered offline |
| EULA carve-outs | `licenses/EULA.txt` §3, §3.2, §3.3 |

**Why the GPL text ships even though no GPL component does.** LGPLv3 is not a standalone
licence: its first substantive sentence incorporates GPLv3 by reference. Shipping LGPL-3.0
alone would deliver an incomplete licence. The notices state explicitly that no
GPL-licensed component is present, so the file cannot be misread as an admission.

---

## 3. WHAT CHANGED DURING PACKAGING — AND WHY IT MATTERED

The first real build shipped **thirteen** Qt libraries, including `Qt6Network.dll`,
`Qt6Qml.dll`, `Qt6Quick.dll`, `Qt6Pdf.dll` and `Qt6VirtualKeyboard.dll`.

The PyInstaller spec had excluded the *Python bindings* for those modules, and everyone
had reasonably assumed that was the end of it. It was not: PyInstaller still collected the
native libraries, because Qt's own DLLs depend on one another.

That is a licensing non-issue — Qt is LGPLv3 either way and the notice covers it — but it
was a **spec-fidelity problem**, and a sharp one. Spec §18 and AC-12 say the product
cannot make a network request. Shipping `Qt6Network.dll` while saying that is not a false
statement about the licence; it is a false statement about the product.

The build now prunes the QML/Quick/Pdf cluster, which takes `Qt6Network` with it, and then
**proves the prune was safe** rather than assuming it: every shipped PE's import table is
re-parsed and compared against what the package actually contains. The first run of that
check immediately caught two plugins (`qtuiotouchplugin.dll`, `qpdf.dll`) still bound to
removed libraries, so the pruning became iterative.

Result: **four Qt libraries instead of thirteen**, no `Qt6Network.dll`, and no dangling
import anywhere in the package.

The same reasoning was applied one level down. CPython's `_ssl` and `libssl` are excluded
from the freeze, so **no TLS stack ships**. What remains is `libcrypto-3.dll`, which
`hashlib` links for message digests — a hashing library, not a transport.

One retreat from the original posture, recorded honestly: the first 1.0.0 candidate also
excluded `_socket` and the whole `urllib.request` closure, and that build **crashed on
first launch on a clean machine** (Phase 13, 2026-08-12) — `jsonschema`, which validates
the preset schemas, imports `urllib.request` at module scope, and its closure needs
`socket`. So the base socket *module* ships again, as an import-graph obligation of a
bundled validator, not as a capability the product uses: no TLS stack, no `Qt6Network`,
no `libcurl`, no first-party networking import (AST-checked), and AC-12 still verifies a
full cycle with outbound traffic blocked. The full rationale and the minimum-closure
derivation live in `packaging/frozen_excludes.py`, and
`tests/packaging/test_frozen_import_closure.py` fails on any machine if the exclusion
list ever breaks the launch import closure again.

---

## 4. VERIFICATION

Not asserted — tested, in `tests/packaging/test_release_artefacts.py`:

| Test | Proves |
| --- | --- |
| `test_the_qt_libraries_ship_as_separate_named_files` | §2.1, §2.2 |
| `test_it_is_a_one_dir_build` | §2.3 |
| `test_no_network_capable_library_is_shipped` | §3 |
| `test_every_referenced_licence_text_is_present` | §2.5 |
| `test_the_gpl_text_ships_because_lgplv3_incorporates_it` | §2.5, checked against the LGPLv3 text's own wording |
| `test_every_shipped_file_is_attributed_to_a_component` | Qt cannot silently re-enter the package unnoticed |

That last one is the standing guard: if a future build reinstates `Qt6Network.dll`, the
file is attributed to the Qt component and shipped — but any *new* unlisted library makes
the manifest incomplete and fails G-1.

`packaging/build.py` re-runs the import-closure proof on every build.

---

## 5. RESIDUAL RISK AND THE REMAINING GATE

| Item | Status |
| --- | --- |
| Shared-library mechanism demonstrated | **Done** — §2 |
| LGPL-3.0 text and notices ship | **Done** — §2.5 |
| EULA does not restrict LGPL rights | **Drafted** — `EULA.txt` §3, §3.2, §3.3 |
| Qt commercial-vs-LGPL decision confirmed by counsel | **UNRESOLVED — L-1.** Under the amended G-12 (ADR-G12, 2026-08-09) counsel confirmation is no longer mandated for V1; the question is documented and carried as owner-accepted residual risk. |
| LGPLv3 "Installation Information" question | **UNRESOLVED — L-3.** A v3-specific obligation with no v2.1 equivalent; same disposition. |

**One genuine simplification came out of the SPEC LOCK amendment.** Qt and FFmpeg are now
under the *same* licence version, LGPLv3. Before, the product would have had to satisfy
LGPL v2.1 for FFmpeg and v3 for Qt simultaneously — two sets of obligations, two sets of
notices, two conversations with counsel. It is now one. That is a real reduction in
surface area, and it is not a substitute for the review.
