# PREFLIGHTQC — UNSIGNED RELEASE POLICY V1 ("POLICY U")

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Status | **ADOPTED** for V1, on the product owner's instruction. Applies until a certificate is obtained. |
| Cost | **£0** — that is the point of it |
| Gate G-11 | **REMAINS OPEN.** This policy does not close, waive, or redefine it. G-11 is the upgrade path out of this policy. |
| Verification | `python packaging/sign.py verify --expect unsigned` — passes only when the artefacts match the declared unsigned state |
| Legal | This policy is release engineering, not legal advice. G-12 attorney review still applies to everything customer-facing. |

## 1. THE DECISION, PRECISELY

PreflightQC V1 may be released with an **unsigned** `PreflightQC.exe` and an **unsigned**
installer, provided every condition in §6 holds. The unsigned state is **declared,
disclosed and mechanically verified** — never hidden, never worked around, and never
described in any way that could be read as "signed" or "verified by Windows".

Two things this policy is *not*:

- **Not a pass of G-11.** `sign.py verify` (the default, signed expectation) still fails
  against these artefacts, and must keep failing. The release audit records that failure
  plus a Policy U pass — both, explicitly.
- **Not a security claim.** An unsigned binary offers the user no publisher
  authentication from the operating system. Nothing we publish may imply otherwise.

## 2. EVALUATION — WHAT SHIPPING UNSIGNED ACTUALLY COSTS

Recorded so the decision is made with the costs in view, not discovered from refunds.

| Consequence | Detail |
| --- | --- |
| **SmartScreen warning, every new release** | Downloaded unsigned executables carry Mark-of-the-Web; Defender SmartScreen shows *"Windows protected your PC"* with the publisher listed as *Unknown*. Proceeding requires **More info → Run anyway** — two clicks a nervous buyer may not make. |
| **Reputation resets on every release** | Unsigned SmartScreen reputation accrues **per file hash**. Each new installer version starts from zero, forever. With a signed build, reputation accrues to the certificate instead and persists across releases — this is the biggest structural cost of staying unsigned. |
| **Browser download friction** | Edge (and to a lesser degree Chrome) may flag an uncommonly-downloaded unsigned `.exe` at download time, before SmartScreen is even involved. |
| **Antivirus heuristics** | Some AV products weight "unsigned + low prevalence" heavily. False-positive reports must be handled per vendor, reactively. |
| **Managed environments** | AppLocker/WDAC policies that require signed code will block the product outright. Enterprise buyers are effectively out of scope while this policy is active. |
| **Merchant-of-Record optics** | The MoR delivers the download, but the warning is ours. Conversion loss and refund pressure land on the product, which is why disclosure *before purchase* is a hard condition (§6). |

## 3. £0 AND NEAR-£0 ALTERNATIVES — CONSIDERED AND DISPOSED OF

| Option | Cost | Verdict |
| --- | --- | --- |
| **Self-signed certificate** | £0 | **Rejected.** No trust chain, so every warning remains — and it *adds* a misleading artefact: a signature that fails validation invites the user to reason about a broken chain instead of a plainly absent one. It is also the closest thing to "pretending to be signed", which this policy exists to avoid. |
| **SignPath Foundation / OSS signing services** | £0 | **Ineligible.** Free signing programmes require an open-source project; PreflightQC is proprietary. |
| **Azure Trusted Signing** | ~US$9.99/month | **The recommended first upgrade** when any §7 trigger fires. Cloud HSM, meets the FIPS hardware requirement, no token shipping, and identity validation is lighter than EV. Not £0, so not this policy. |
| **Microsoft Store (MSIX)** | US$19 one-time (individual) | Store-signed and warning-free, but a different distribution model (Store terms, MSIX packaging, certification) and a fee. Out of scope for V1; worth revisiting alongside a Store listing decision. |
| **OV / EV Authenticode certificate** | ~£200–500+/year | The full G-11 path, already documented in `CODE-SIGNING-READINESS.md`. The business decision it needs is unchanged. |

## 4. CLAIMS DISCIPLINE — WHAT MAY AND MAY NOT BE SAID

**Required disclosure**, verbatim or equivalent, wherever the product is offered for
sale and on the support page:

> The PreflightQC installer is **not digitally signed** in this version. When you first
> run it, Windows SmartScreen will show a "Windows protected your PC" warning naming an
> unknown publisher. This is the expected behaviour for an unsigned installer — it is
> stated here so you know before buying, not after. To proceed, Windows requires
> choosing "More info", then "Run anyway". Verify your download first against the
> SHA-256 checksum published on the product page.

**Never:**

- describe the download as "signed", "verified", "certified", "trusted by Windows", or
  "safe" on the strength of anything in this policy;
- instruct users to disable SmartScreen, Defender, or any security feature — the
  disclosure describes the standard per-file flow Windows itself offers, nothing more;
- present the checksum as a substitute for code signing (see §5 for what it actually
  provides);
- let a listing or screenshot imply an absence of warnings.

## 5. INTEGRITY WITHOUT AUTHENTICODE — WHAT £0 ACTUALLY BUYS

For each release, the release owner publishes `RELEASE-HASHES.txt` on the product page
(`https://itisyou.app/products/preflightqc`) containing the SHA-256 of the installer and
of the portable archive if one is offered, with the exact filenames and the release
version. The MoR listing links to it.

Users verify with built-in tools, documented on the support page:

```
certutil -hashfile PreflightQC-<version>-setup.exe SHA256      (cmd)
Get-FileHash PreflightQC-<version>-setup.exe -Algorithm SHA256  (PowerShell)
```

**Honest scope of this measure.** A published hash protects against download corruption
and against tampering of a mirror or CDN copy, *provided* the page serving the hash is
intact; its trust anchor is TLS on `itisyou.app`, not a publisher identity. It does not
authenticate the publisher to the operating system and it does not help a user who does
not check it. That is what Authenticode is for, and why §7 exists.

## 6. CONDITIONS — ALL REQUIRED BEFORE ANY UNSIGNED RELEASE

| # | Condition | Checked by |
| --- | --- | --- |
| U-1 | `python packaging/sign.py verify --expect unsigned` exits 0 against the final artefacts (present and carrying **no** signature) | Mechanical |
| U-2 | The §4 disclosure appears in the marketplace listing and on the support page | Human, at listing time |
| U-3 | `RELEASE-HASHES.txt` published on the product page; hashes match the shipped artefacts byte-for-byte | Human, at publish time |
| U-4 | The clean-machine run-book is executed with the **Policy U variants** of A2 and A8 (`RELEASE-VALIDATION-V1.md`), and the observed SmartScreen behaviour is recorded verbatim with screenshots | Human, Phase 13 |
| U-5 | The default `sign.py verify` failure is recorded in the release audit alongside the Policy U pass — the audit must show both | Mechanical + audit |
| U-6 | No customer-facing text anywhere claims or implies the product is signed | Claim discipline, §4; spot-checked by test |

`FINAL BUILD APPROVED` authorisation, G-12 attorney review, and every other open gate
are unchanged by this policy.

## 7. EXIT TRIGGERS — WHEN £0 STOPS BEING THE RIGHT PRICE

Adopt Azure Trusted Signing (or better) when **any** of these occurs:

1. The MoR or distribution channel requires a signed installer.
2. Refunds or support contacts citing the SmartScreen warning exceed a level the owner
   is willing to tolerate.
3. An enterprise or managed-desktop customer materialises.
4. An AV false positive occurs that signing would plausibly have avoided.
5. Release cadence makes the per-release reputation reset (§2) a recurring cost rather
   than a one-off.

On exit: obtain the certificate, follow `CODE-SIGNING-READINESS.md` §2 signing order,
close G-11 genuinely, run A2/A8 in their signed form, and retire the §4 disclosure —
in that order.
