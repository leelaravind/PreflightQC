"""The inspector adapter contract.

Both adapters implement the same shape (ARCHITECTURE-V1.md section 4.1):

    inspect(path, timeout) -> InspectorOutcome

An adapter **never raises** to its caller and **never** returns partially-parsed data
without saying so. Every way an inspection can go wrong has a name in `FailureKind`,
because "the file failed" and "we could not inspect the file" are different facts and
the specification requires them to be reported differently (spec 7.4).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FailureKind(Enum):
    """Every way an inspection can fail. Spec 23 maps each to a user-visible behaviour."""

    NOT_FOUND = "NOT_FOUND"
    """The inspector binary is not where it should be."""

    LAUNCH_FAILED = "LAUNCH_FAILED"
    """The binary exists but could not be started."""

    TIMEOUT = "TIMEOUT"
    """The inspector exceeded its per-call budget and its process tree was killed."""

    CRASHED = "CRASHED"
    """The inspector terminated abnormally."""

    BAD_EXIT = "BAD_EXIT"
    """The inspector exited non-zero with a reportable error."""

    MALFORMED_OUTPUT = "MALFORMED_OUTPUT"
    """Output could not be parsed as the expected structured format."""

    FILE_UNREADABLE = "FILE_UNREADABLE"
    """The file could not be read (missing, deleted mid-scan, I/O error)."""

    PERMISSION_DENIED = "PERMISSION_DENIED"
    """The file exists but access was refused."""

    CANCELLED = "CANCELLED"
    """The batch was cancelled while this inspection was in flight."""


#: Failure kinds that describe the *file* rather than the inspector. These are the ones
#: worth surfacing to the user with a remediation hint.
FILE_LEVEL_FAILURES = frozenset(
    {FailureKind.FILE_UNREADABLE, FailureKind.PERMISSION_DENIED}
)


@dataclass(frozen=True, slots=True)
class InspectorSuccess:
    """A successful inspection."""

    raw: dict[str, Any]
    tool_version: str | None = None
    duration_ms: float = 0.0

    ok: bool = True


@dataclass(frozen=True, slots=True)
class InspectorFailure:
    """A failed inspection, with enough detail to explain it to a user."""

    kind: FailureKind
    message: str
    exit_code: int | None = None
    stderr_excerpt: str | None = None
    duration_ms: float = 0.0

    ok: bool = False

    def describe(self) -> str:
        detail = f"{self.kind.value}: {self.message}"
        if self.exit_code is not None:
            detail += f" (exit {self.exit_code})"
        return detail


InspectorOutcome = InspectorSuccess | InspectorFailure


@dataclass(frozen=True, slots=True)
class RawStream:
    """One stream as reported by an inspector, before normalisation."""

    index: int
    kind: str  # "video" | "audio" | "subtitle" | "data" | "other"
    fields: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RawInspection:
    """An inspector's output reduced to a common intermediate shape.

    Both adapters produce this, so the normaliser has one input format rather than two.
    Values stay as the inspector reported them -- canonicalisation happens downstream.
    """

    inspector: str
    tool_version: str | None
    container: dict[str, Any]
    streams: tuple[RawStream, ...]

    def streams_of(self, kind: str) -> tuple[RawStream, ...]:
        return tuple(s for s in self.streams if s.kind == kind)
