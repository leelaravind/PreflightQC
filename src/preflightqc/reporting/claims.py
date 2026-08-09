"""Report claim language.

Specification 4.1 forbids PreflightQC from ever implying platform acceptance. That is
not a style preference: a tool that says "guaranteed accepted" is making a promise it
has no way to keep, and the first rejected upload destroys the user's trust in every
other verdict it gave.

The approved wording is kept here as a constant, and the forbidden phrases are kept
beside it so an automated content check can prove neither drifted into a report.
"""

from __future__ import annotations

#: The only claim PreflightQC makes about a validated file. Spec 4.2.
APPROVED_CLAIM = (
    "Validated against the technical rules contained in the selected PreflightQC preset."
)

#: What PreflightQC does not do to your files, stated in every report.
NON_DESTRUCTIVE_STATEMENT = (
    "PreflightQC inspects files only. No source video file was opened for writing, "
    "modified, moved or renamed."
)

#: The honest limits of the tool, stated where the user will read them.
ACCURACY_STATEMENT = (
    "PreflightQC reads file metadata; it does not watch the video. Platform "
    "specifications change without notice, so every rule carries the date its source "
    "was last verified. Where a platform documents nothing, PreflightQC reports "
    "UNKNOWN rather than guessing."
)

#: Phrases that must never appear in any report, UI string or document.
FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "guaranteed accepted",
    "guaranteed to be accepted",
    "guaranteed to upload",
    "guaranteed upload",
    "approved by instagram",
    "approved by meta",
    "approved by tiktok",
    "approved by youtube",
    "approved by linkedin",
    "certified by",
    "will be accepted",
    "guarantees acceptance",
)


def contains_forbidden_claim(text: str) -> tuple[str, ...]:
    """Return any forbidden phrases found in the text. Empty means clean."""
    lowered = text.lower()
    return tuple(phrase for phrase in FORBIDDEN_CLAIMS if phrase in lowered)
