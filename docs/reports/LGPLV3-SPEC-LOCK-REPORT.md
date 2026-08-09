# PREFLIGHTQC — LGPLv3 SPEC LOCK AMENDMENT REPORT

> **AMENDMENT NOTE (2026-08-09, added after this report was written).** Gate G-12 was
> amended by SPEC LOCK v1.1.0 from mandatory attorney review to **owner licensing &
> compliance risk acceptance** — see `docs/decisions/ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md`.
> Statements below describing attorney review as an absolute release prerequisite record
> the gate as it stood when this report was written and are preserved unchanged.
> **No attorney review has occurred, and no legal clearance is claimed.**

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Authorised by | `Temp/PREFLIGHTQC-LGPLV3-SPEC-LOCK-AND-GATE1.md` — "APPROVE OPTION B" |
| Procedure | SPEC LOCK, per `PREFLIGHTQC-V1-SPEC.md` §29.2 |
| Scope | FFmpeg licence version, and the prohibited-component list |
| Result | **Amendment applied. Dependency gate re-verified: PASS.** |
| Legal status | **No clearance claimed. G-12 / G-13 remain open hard release gates.** |

---

## 1. WHAT CHANGED AND WHY

The repository originally required FFmpeg to be **LGPL v2.1**. That requirement was
written before any binary existed, on the assumption that "an LGPL build" meant v2.1.

Verification of the real mainstream Windows build disproved the assumption. The BtbN
`win64-lgpl-shared` build is **LGPL v3**.

### 1.1 The evidence

| Source | Finding |
| --- | --- |
| `ffprobe -version` on the installed binary | configuration contains `--enable-version3` |
| The build's own `LICENSE.txt` | is the **LGPL version 3** text, not v2.1 |
| FFmpeg `LICENSE.md` (from the 9.0 source tarball) | *"The following libraries are under LGPL version 3: gmp, libaribb24, liblensfun. When combining them with FFmpeg, use the configure option `--enable-version3` to upgrade FFmpeg to the LGPL v3."* |

The build enables `gmp` and `libaribb24`, which is exactly why `--enable-version3` is
present. This is not an unusual or misconfigured build; it is what the ecosystem ships.

### 1.2 The decision

`--enable-version3` is **permitted**. `gmp`, `libaribb24` and `liblensfun` are permitted
**as part of a verified LGPLv3 build**. They upgrade the licence *version*; they do not
introduce copyleft over PreflightQC's own source.

Custom-building an LGPLv2.1 FFmpeg was explicitly rejected by the authorising instruction,
and independently it would be the worse option: it would make PreflightQC a "modifier"
under the licensing gate §2.5, taking on source-correspondence duties for a build we
produced ourselves.

**What did not change.** `--enable-gpl` and `--enable-nonfree` remain absolutely
prohibited, as does every library in FFmpeg's `EXTERNAL_LIBRARY_GPL_LIST`, its nonfree
lists, and `libsmbclient`. The verified build disables all of them.

---

## 2. THE libzvbi CORRECTION

The source pack recorded **libzvbi as GPL-2+**, which would have forced `--enable-gpl`.
That classification is **stale**.

### 2.1 Authoritative evidence

FFmpeg 9.0 `configure`, line 7510 — verbatim:

```
enabled libzvbi && require_pkg_config libzvbi zvbi-0.2 libzvbi.h vbi_decoder_new &&
  { test_cpp_condition libzvbi.h "VBI_VERSION_MAJOR > 0 || VBI_VERSION_MINOR > 2 ||
      VBI_VERSION_MINOR == 2 && VBI_VERSION_MICRO >= 28" ||
    enabled gpl || die "ERROR: libzvbi requires version 0.2.28 or --enable-gpl."; }
```

`--enable-gpl` is demanded **only** for libzvbi *below* 0.2.28. libzvbi relicensed from
GPL-2+ to **LGPL-2.1-or-later** at 0.2.28, and FFmpeg encodes precisely that boundary.

Corroborating: libzvbi appears in **neither** `EXTERNAL_LIBRARY_GPL_LIST` (configure lines
2029–2043) **nor** the GPL-v2 list in FFmpeg's `LICENSE.md`.

### 2.2 Why this is evidence-led, not convenience-led

The instruction was explicit: *"Do not remove a prohibition merely to make the gate pass."*

Two things make this correction safe:

1. **The evidence is upstream and primary** — FFmpeg's own build system, not our reading
   of a blog.
2. **The safety property it was protecting is enforced elsewhere, absolutely.** libzvbi
   was prohibited because it was believed to force GPL. The `--enable-gpl` check remains
   unconditional, so a build that *did* link a GPL libzvbi would still be rejected — by
   the check that actually matters. Removing the name changes nothing about that.

---

## 3. DOCUMENTS AMENDED

| Document | Change | Reason |
| --- | --- | --- |
| `docs/licensing/LICENSING-GATE-V1.md` | New **§2.0 amendment** recording evidence and decision; §2 heading v2.1 → v3; §2.2 version3 row struck; §2.4 checklist notices → LGPLv3; §6 notice list → LGPLv3; §7 prohibited list rewritten to FFmpeg's own GPL/nonfree/GPLv3 lists; new **§7.1** documenting the libzvbi correction; G-4 now records the licence version | The licence the product declares must match the binary it ships |
| `docs/specification/PREFLIGHTQC-V1-SPEC.md` | §10.2 permits v2.1 **or** v3 with detection; §26 release package requires LGPL-3.0 text; G-4 and G-8 reworded | Spec is the authority the gate is subordinate to |
| `docs/architecture/ADR-001-TECH-STACK.md` | ffprobe row → LGPL-3.0+; §4.1 notes Qt and FFmpeg now share a licence version | The "compliance machinery already exists" argument is now stronger, not weaker |
| `docs/architecture/ARCHITECTURE-V1.md` | Dependency-boundary and packaging diagrams → LGPL 3.0 | Diagrams state a licence; it must be the right one |
| `docs/sources/SOURCE-REGISTER.md` | FFmpeg row annotated: default is v2.1, but the shipped BtbN binary is v3 | The register records what research found; the correction is appended, not overwritten |
| `packaging/generate_manifest.py` | FFmpeg notice → LGPLv3; new version3 explanatory note; gmp / libaribb24 / libzvbi added as declared components; G-5 check no longer keyed on `LGPL-2.1` | Generated notices must be true |
| `packaging/layout_check.py` | LGPL-3.0 text required first | The package must carry the licence it operates under |
| `packaging/binaries.lock.json` | ffprobe **VERIFIED**, full configuration and per-file hashes recorded; amendment noted | The manifest must reflect the verified reality |
| `src/preflightqc/ui/about.py` | About-box notice → LGPLv3 + version3 statement | The FFmpeg checklist requires an in-product notice; it must name the right version |
| `src/preflightqc/platform/binaries.py` | Prohibited list rewritten; `--enable-version3` no longer a violation; `licence_version()` added; configuration captured | See §4 |
| `spikes/probe_matrix.py` | Now **delegates** to the shipped audit instead of duplicating it | See §4.2 |

**Nothing was blanket-replaced.** References to LGPL 2.1 that remain correct — the licence
text still shipped because LGPLv3 incorporates it, libzvbi's own LGPL-2.1-or-later status,
MediaInfo's pre-0.7.63 history — are untouched.

---

## 4. DEFECTS FOUND AND FIXED

The amendment exposed defects in our own tooling. All are fixed with tests.

### 4.1 The build scanner could not tell `--enable-` from `--disable-`

Substring matching meant `--disable-libx264` was reported as a libx264 violation. Against
the real build it produced **twelve** findings, **ten of them false**. `audit_configuration()`
now parses the flags and reports only components genuinely switched on.

A scanner that cries wolf on every compliant build teaches people to ignore it, which is
worse than having no scanner.

### 4.2 The spike harness had its own divergent copy of the policy

`spikes/probe_matrix.py` carried a duplicate prohibited-list and the same substring bug.
After the amendment it **rejected a build the application accepted** — the two disagreed.
It now imports `audit_configuration` and `licence_version` from the shipped module, so
they cannot drift again.

### 4.3 MediaInfo's version parsed as "MediaInfoLib"

The regex captured the library name instead of the version. Now reports **26.05**. This
matters: the version is the evidence for BSD-era licensing, and it is printed on reports.

---

## 5. RE-VERIFICATION

All six required checks, against the actually installed binaries:

| # | Check | Result |
| --- | --- | --- |
| 1 | Scanner run against installed ffprobe | **PASS** — `n8.1.2-34-g9b6c8969e0-20260809` |
| 2 | No GPL/nonfree configuration | **PASS** — `--enable-gpl` absent, `--enable-nonfree` absent, prohibited components enabled: **none** |
| 3 | Licence classification = accepted LGPLv3 | **PASS** — detected `LGPL-3.0-or-later`, violations: none |
| 4 | MediaInfo remains approved | **PASS** — 26.05, BSD-2-Clause, no GUI, no libcurl installed |
| 5 | Licence / manifest tests | **PASS** |
| 6 | Full regression | **PASS — 1037 passed, 3 skipped, 0 failed** |

Plus: `mypy` clean over 52 source files, `ruff check` clean, all 6 documentation
invariants hold.

**DEPENDENCY GATE: PASS.**

---

## 6. WHAT THIS AMENDMENT DOES NOT DO

- **It claims no legal clearance.** LGPL v3 carries terms v2.1 does not — installation
  information for "User Products", and explicit patent provisions. Their effect on a
  commercial desktop product is an attorney question.
- **G-12 (attorney review) remains open**, untouched and not started.
- **G-13 (GUI framework licence posture) remains open.** It is now the *same* licence
  family as FFmpeg, so it is one legal conversation rather than two — which is a genuine
  simplification, not a resolution.
- **It does not declare the product releasable.** It clears an engineering gate.

---

## 7. SPEC DEVIATIONS

**NONE.** The amendment was explicitly authorised, follows the SPEC LOCK procedure
(§29.2), is recorded with primary-source evidence, and re-verified every affected gate.

The only judgement call worth naming: the licensing gate now ships **both** LGPL-3.0 and
LGPL-2.1 texts rather than replacing one with the other. LGPLv3 incorporates v2.1 by
reference and libzvbi is LGPL-2.1-or-later, so dropping v2.1 would have created a new gap
while closing another.
