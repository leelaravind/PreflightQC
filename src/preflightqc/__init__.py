"""PreflightQC — offline technical QA for video exports.

PreflightQC inspects local video files, normalises their metadata, validates that
metadata against a selected preset's data-driven rule set, and reports the result.

It never modifies a source file, never uploads anything, and never requires a network.

Authority: docs/specification/PREFLIGHTQC-V1-SPEC.md
"""

from __future__ import annotations

__version__ = "0.1.0-dev"
__product_name__ = "PreflightQC"

__all__ = ["__product_name__", "__version__"]
