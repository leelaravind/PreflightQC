# PreflightQC brand asset provenance

| Field | Value |
| --- | --- |
| Source of truth | `assets/logo/logo.png` — **Product Owner-provided and approved project artwork** (approved in the Final Binding instruction, 2026-08-10) |
| SHA-256 (approved original) | `54372b3e0e9e7a973b709115f0d54be242934b63e7abdbb09cfc178a880cfda3` |
| Redesign policy | The logo must not be redesigned or stylistically reinterpreted. Every derivative in this folder and in the application is a pure geometric resize of the original — no crop, recolour, or recomposition. |
| Generator | `tools/generate_icons.py` — Qt smooth scaling at fixed settings; deterministic for the pinned Qt version |

## Derivatives

| File | Purpose | SHA-256 |
| --- | --- | --- |
| `preflightqc.ico` | Windows multi-size icon (16/24/32/48 BMP + 64/128/256 PNG entries): executable icon (PyInstaller spec) and installer icon (Inno Setup) | `dbda9406c9d8a9a8a29c745cb0317b3e0e6295044eeb0ae5af48540d681f3fc2` |
| `../../src/preflightqc/ui/assets/preflightqc.png` | 256 px application window/taskbar icon, shipped inside the frozen package and shown in the About dialog | `b2074635a827ebb1856927a712158eebfa71bb8d0485f8c4bcd9b9e397fc7f75` |
| `logo-512.png` | Marketplace/listing artwork derivative | `80cc324e095b9edb630e4cbabfc1f25618f653901130d8e4e671963a79a9153f` |

Regenerate (overwrites all derivatives from the approved original):

```
python tools/generate_icons.py
```

Any change to `logo.png` requires Product Owner approval first, then regeneration and
an update to the hashes above.
