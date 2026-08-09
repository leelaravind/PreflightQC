# Page: `itisyou.app/products/preflightqc/legal` — PREPARED, NOT PUBLISHED

At publication, link the EULA text actually shipped in the release (the final
`licenses/EULA.txt`, banner removed) — never a divergent web copy.

---

# PreflightQC — Legal & Licences

**Publisher:** ITISYOU · **Product:** PreflightQC 1.0.0 (Windows x64)

## Licence agreement

PreflightQC is licensed, not sold, under the End User Licence Agreement shown by the
installer and shipped with the product as `licenses/EULA.txt`. The same text:
{{EULA_LINK}}.

Key points, stated plainly (the EULA text governs):

- One-time purchase; perpetual licence for the purchased version; no subscription.
- The open-source licences of bundled components take precedence over anything in the
  EULA that would conflict with them, and the EULA does not prohibit what those
  licences permit — including reverse engineering of the LGPL components.
- PreflightQC inspects files read-only and makes no guarantee any platform will
  accept an upload.

## Third-party components

PreflightQC bundles, unmodified: FFmpeg's ffprobe and libav* libraries (LGPL v3 —
PreflightQC does not own FFmpeg); MediaInfo (BSD-2-Clause) and ZenLib (zlib); Qt via
PySide6 (LGPL v3), shipped as separate replaceable libraries; CPython (PSF-2.0) and
its bundled libraries; Microsoft Visual C++ runtime components (Microsoft
Distributable Code). The complete notices and full licence texts ship inside the
product in `licenses/`, and the dependency manifest lists every file with its
checksum. Corresponding source for the LGPL components:
[source page](/products/preflightqc/source).

## Privacy

PreflightQC has no network capability: no account, no telemetry, no analytics, no
update checks — the installed application contains no HTTP client and no socket
implementation. Nothing about you, your files, or your usage is collected or
transmitted by the product. Purchases are handled by the merchant of record under
their privacy terms; this site's hosting has its own standard server logs.

## Trademarks

Instagram, Meta, TikTok, YouTube and LinkedIn are trademarks of their respective
owners. Qt is a trademark of The Qt Company Ltd. PreflightQC is not affiliated with,
endorsed by, or certified by any of them; their names are used descriptively only, to
identify the delivery specifications PreflightQC validates against.

## Refunds

See the [refund policy](/products/preflightqc/refunds). Statutory rights unaffected.
