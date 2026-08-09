"""PreflightQC — offline technical QA for video exports.

PreflightQC inspects local video files, normalises their metadata, validates that
metadata against a selected preset's data-driven rule set, and reports the result.

It never modifies a source file, never uploads anything, and never requires a network.

Authority: docs/specification/PREFLIGHTQC-V1-SPEC.md
"""

from __future__ import annotations

__version__ = "0.1.0-dev"
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
