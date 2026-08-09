# Page: `itisyou.app/products/preflightqc/support` — PREPARED, NOT PUBLISHED

`{{SUPPORT_CONTACT}}` must be connected to a real mailbox/form at publication — a
support page with a dead contact is worse than none.

---

# PreflightQC — Support

**Contact:** {{SUPPORT_CONTACT}} · Please include your Windows version and, if the
problem concerns a specific file, the exported HTML report (it contains the technical
detail we need and nothing personal).

## System requirements

- Windows 10 x64 or Windows 11 x64 (no macOS, Linux, 32-bit, or ARM)
- ~250 MB disk space; 1280×800 or larger display recommended
- No administrator rights required — installs per-user
- Nothing else to install: ffprobe and MediaInfo are bundled

## Installing

1. Download `PreflightQC-1.0.0-setup.exe` from the product page or your purchase
   receipt.
2. **Verify the download** (recommended). In PowerShell:
   `Get-FileHash PreflightQC-1.0.0-setup.exe -Algorithm SHA256`
   or in Command Prompt:
   `certutil -hashfile PreflightQC-1.0.0-setup.exe SHA256`
   Compare the value against `RELEASE-HASHES.txt` on the product page. They must
   match exactly.
3. Run the installer. **Windows SmartScreen will warn** — the installer is not
   digitally signed in this version, and the warning names an unknown publisher. This
   is the expected behaviour we disclose before purchase. Choose **More info → Run
   anyway** to proceed. If your organisation's policy blocks unsigned software,
   PreflightQC cannot be installed on that machine in this version.
4. No elevation prompt appears; PreflightQC installs under your user profile.

## Frequently asked

**Does it need the internet?** No. PreflightQC is fully offline: no account, no
login, no activation, no telemetry, no update checks. The application contains no
networking code at all.

**Where is my data?** On your machine. Source videos are opened read-only and never
modified. Reports are written only where you choose to save them. Custom profiles and
settings live under `%LOCALAPPDATA%\PreflightQC`.

**Why did a file PASS but the platform still complained?** PreflightQC validates the
technical rules contained in the selected preset, each traced to a published
first-party source with a verification date. Platforms change requirements without
notice and apply rules that are not published. A PASS is a statement about the file
against those rules — not a guarantee of acceptance.

**Why UNKNOWN?** Either the platform publishes no requirement for that property, or
the property could not be read from your file. PreflightQC reports that honestly
rather than guessing.

**Custom profiles?** Advanced, file-based: place a profile JSON in
`%LOCALAPPDATA%\PreflightQC\profiles`. There is no in-app editor in this version.

**Uninstalling** removes the application only; your profiles and reports are yours
and are left in place.

## Refunds

Request within 7 calendar days of purchase; eligible refunds normally receive the
full purchase price, processed through the merchant of record you bought from. Full
policy: [refunds](/products/preflightqc/refunds).
