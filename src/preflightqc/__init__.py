"""PreflightQC — offline technical QA for video exports.

PreflightQC inspects local video files, normalises their metadata, validates that
metadata against a selected preset's data-driven rule set, and reports the result.

It never modifies a source file, never uploads anything, and never requires a network.

Authority: docs/specification/PREFLIGHTQC-V1-SPEC.md
"""

from __future__ import annotations

#: The single authoritative product version. Everything customer-facing derives from
#: this: the window title, About dialog, exported reports, CLI banner, package
#: metadata (pyproject `dynamic`), and the installer version passed by
#: packaging/build.py. Frozen at 1.0.0 on 2026-08-09 by Product Owner decision
#: (release identity: PreflightQC 1.0.0, ITISYOU, Windows x64, Policy U unsigned).
__version__ = "1.0.0"
__product_name__ = "PreflightQC"
__publisher__ = "ITISYOU"

#: Customer-facing locations, shown in the About dialog and the exported report.
#:
#: These are *strings*. Nothing in the product fetches them, resolves them or checks
#: whether they exist — displaying a URL must never become a reason to open a socket
#: (spec §18). The corresponding-source location in particular is a licensing
#: obligation, and it has to be readable offline to be worth anything.
PRODUCT_URL = "https://itisyou.app/products/preflightqc"
SUPPORT_URL = "https://itisyou.app/products/preflightqc/support"
LEGAL_URL = "https://itisyou.app/products/preflightqc/legal"
SOURCE_URL = "https://itisyou.app/products/preflightqc/source"

__all__ = [
    "LEGAL_URL",
    "PRODUCT_URL",
    "SOURCE_URL",
    "SUPPORT_URL",
    "__product_name__",
    "__publisher__",
    "__version__",
]
