# PREFLIGHTQC — CODE-SIGNING READINESS (GATE G-11)

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Gate | **G-11** — application, first-party binaries and installer Authenticode-signed |
| Status | **OPEN.** No certificate exists. `packaging/sign.py verify` reports `UNSIGNED` and exits non-zero. |
| Infrastructure | **Ready.** Everything except the certificate itself is written and tested. |
| This document | The run-book for whoever obtains the certificate. It does **not** sign anything. |
| Unsigned path | V1 may release **unsigned** under **Policy U** — `docs/licensing/UNSIGNED-RELEASE-POLICY-V1.md` (adopted 2026-08-09). That policy declares, discloses and mechanically verifies the unsigned state (`sign.py verify --expect unsigned`); it does **not** close this gate. G-11 stays OPEN as the upgrade path, with §7 of that policy listing the exit triggers. |

Nothing in this repository contains a certificate, a thumbprint, a password or a token,
and nothing should. `packaging/sign.py` takes the signing identity from the command line
or the environment for that reason.

---

## 1. WHAT MUST BE SIGNED, AND WHAT MUST NOT

| Artefact | Sign? | Why |
| --- | --- | --- |
| `PreflightQC.exe` | **Yes** | First-party. The binary Windows executes. |
| `PreflightQC-<version>-setup.exe` | **Yes** | First-party, and the file SmartScreen judges. |
| `bin\ffprobe.exe` and the seven `libav*` DLLs | **No, by default** | Third-party, shipped **unmodified**. |
| `bin\MediaInfo.exe` | **No, by default** | Same. |
| `_internal\PySide6\*.dll` | **No** | Third-party Qt, shipped unmodified. |

### 1.1 Why the third-party binaries are left alone

Re-signing them is *permitted* by the licensing gate provided they are otherwise
unmodified — but every signature we add is one more thing to explain to a recipient
checking that the FFmpeg binary we shipped is the one BtbN published. The archived
corresponding source, the published checksum and the byte-identical file are a clean,
verifiable chain. Leaving the files exactly as published keeps it clean.

`packaging/sign.py --include-third-party` exists for the case where a distribution channel
insists. If it is ever used, the manifest hashes in `licenses/DEPENDENCY-MANIFEST.json`
must be regenerated afterwards, because signing changes the file.

---

## 2. SIGNING ORDER

Order matters in one place, and getting it wrong produces an installer whose contents fail
verification.

```
1.  packaging/build.py --skip-installer      # produce dist/PreflightQC
2.  sign PreflightQC.exe                     # BEFORE the installer is built
3.  packaging/build.py                       # build the installer around the signed exe
4.  sign PreflightQC-<version>-setup.exe
5.  packaging/sign.py verify                 # both must verify
6.  packaging/generate_manifest.py           # regenerate: signing changed PreflightQC.exe
7.  packaging/scan_prohibited.py             # re-run the gate against the final tree
```

> **Step 2 before step 3.** Inno Setup embeds a copy of every file. Signing the executable
> after the installer is built leaves the installer carrying the unsigned original, and
> the file the user ends up with is the unsigned one.
>
> **Step 6 after signing.** An Authenticode signature is appended to the PE, so the file's
> SHA-256 changes. A manifest generated before signing describes a file that is no longer
> in the package — which is exactly the drift the generated manifest exists to prevent.

---

## 3. COMMANDS

Sign (the release engineer needs the certificate in the Windows certificate store):

```
set PREFLIGHTQC_SIGNING_THUMBPRINT=<sha1 thumbprint>
python packaging/sign.py sign
```

Verify (anyone, on any build):

```
python packaging/sign.py verify
```

The underlying calls, for the record:

```
signtool sign /sha1 <thumbprint> /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 <file>
signtool verify /pa /v <file>
```

`packaging/sign.py` locates `signtool.exe` itself, preferring an x64 build — this machine
has an arm64 `signtool` earlier in the Windows Kits tree, and picking it produces a
confusing failure rather than an obvious one.

---

## 4. TIMESTAMPING IS NOT OPTIONAL

Every signature must carry an RFC 3161 timestamp (`/tr` plus `/td SHA256`).

Without one, the signature stops validating the day the certificate expires — **including
on copies already installed on customer machines**. A three-year certificate would
silently turn every installed copy into an unsigned binary on its expiry date.

Default in `sign.py`: `http://timestamp.digicert.com`. Any RFC 3161 authority is
acceptable; the `--timestamp-url` flag exists so the choice is not baked in.

---

## 5. CERTIFICATE — THE DECISION THAT HAS TO BE MADE

| Option | Effect on SmartScreen | Notes |
| --- | --- | --- |
| **OV (organisation validated)** | Builds reputation over time; **early downloads will warn** | Cheaper. The warning fades as installs accumulate. |
| **EV (extended validation)** | Immediate SmartScreen reputation | More expensive, and requires a hardware token or a cloud HSM, which changes the signing workflow |

Since June 2023 all publicly-trusted code-signing keys must be generated and stored on
hardware meeting FIPS 140-2 Level 2 or equivalent. Either option therefore involves a
token or an HSM — this is not a file you download and copy into CI.

**This is a business decision.** The engineering consequence is only that step 2 and step 4
above may need the token present, and that a CI machine cannot sign unattended without a
cloud HSM.

---

## 6. WHAT SIGNING UNBLOCKS

| Blocked item | Why it needs the signature |
| --- | --- |
| **P13-A2** SmartScreen behaviour | Cannot be meaningfully observed against an unsigned installer |
| **P13-A8** signature verification | The criterion *is* the signature |
| **GATE-6** clean-machine validation | Needs A2 and A8 |
| A listing on any Merchant of Record | An unsigned Windows installer produces a warning most buyers will not click through |

**Get the certificate before booking the clean-machine validation** — unless the release
runs under Policy U, whose A2-U/A8-U run-book variants are designed to be executed
against the unsigned build and validate the declared state instead. Running the *signed*
run-book against an unsigned build still burns the session.

---

## 7. WHAT IS ALREADY DONE

| Item | State |
| --- | --- |
| `packaging/sign.py`, sign and verify | **Written**, with signtool discovery and architecture preference |
| Artefact list | **Defined** — first-party by default, third-party opt-in |
| Timestamping | **Defaulted**, and documented as mandatory |
| Verification in the audit | **Wired.** `sign.py verify` runs and currently fails, which is the correct report before a certificate exists |
| Repository hygiene | **No credential, thumbprint or certificate is committed**, and `.gitignore` excludes `*.pfx`, `*.p12` and `*.snk` |
| Manifest regeneration after signing | **Documented** as step 6, because signing changes the hash |

**G-11 remains OPEN until a certificate is obtained, both artefacts are signed and
timestamped, and `packaging/sign.py verify` exits zero.**
