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


#: Words that flip a forbidden phrase into the disclaimer we are required to make.
#:
#: The EULA has to say the software is *"not affiliated with, endorsed by, or certified
#: by any platform"* — the required disclaimer contains the forbidden phrase. A scanner
#: that cannot tell an assertion from its negation would flag that sentence, and the
#: obvious way to make it pass would be to delete the disclaimer. So negation is
#: recognised, narrowly and within the same sentence.
_NEGATIONS: tuple[str, ...] = ("not", "never", "no", "nor", "cannot", "isn't", "aren't")

#: How far back to look for a negation. Long enough for "is not affiliated with,
#: endorsed by, or certified by", short enough not to reach the previous clause.
_NEGATION_WINDOW = 80


def _is_negated(lowered: str, position: int) -> bool:
    sentence_start = max(
        lowered.rfind(". ", 0, position),
        lowered.rfind(".\n", 0, position),
        lowered.rfind("\n\n", 0, position),
    )
    start = max(position - _NEGATION_WINDOW, sentence_start + 1, 0)
    # Whitespace is normalised because these documents are hard-wrapped: "is not\n
    # affiliated" must read the same as "is not affiliated".
    window = " ".join(lowered[start:position].split())
    return any(f" {word} " in f" {window} " for word in _NEGATIONS)


def contains_forbidden_claim(text: str) -> tuple[str, ...]:
    """Return any forbidden phrases asserted in the text. Empty means clean.

    An occurrence that is negated in the same sentence is not a claim — it is the
    disclaimer the specification requires.
    """
    lowered = text.lower()
    found: list[str] = []
    for phrase in FORBIDDEN_CLAIMS:
        position = lowered.find(phrase)
        while position != -1:
            if not _is_negated(lowered, position):
                found.append(phrase)
                break
            position = lowered.find(phrase, position + 1)
    return tuple(found)
