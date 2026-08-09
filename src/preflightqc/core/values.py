"""Three-valued metadata fields.

This module is the mechanical guarantee behind specification 7.1 -- "never treat
unavailable metadata as failure".

Every metadata field is one of four states:

    KNOWN         a determined value, and where it came from
    NOT_PRESENT   the property is genuinely absent from the file
    UNDETERMINED  the inspectors could not determine it
    CONFLICTED    both inspectors reported it and disagreed

There is no fifth state and no default. A missing bitrate is NOT_PRESENT, never 0.
Because no fabricated zero exists anywhere in the model, a rule cannot accidentally
compare against one and produce a FAIL.

Reading a value requires explicitly handling absence: `MetaField.value` raises on any
non-KNOWN state. Callers use `is_known`, `or_none()`, or `unwrap_or()`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar

T = TypeVar("T")


class FieldState(Enum):
    """The four states a metadata field may occupy."""

    KNOWN = "KNOWN"
    NOT_PRESENT = "NOT_PRESENT"
    UNDETERMINED = "UNDETERMINED"
    CONFLICTED = "CONFLICTED"


class FieldNotKnownError(RuntimeError):
    """Raised when a caller reads `.value` on a field that has no determined value.

    This is deliberately loud. Silently substituting a default here is precisely the
    defect the three-valued model exists to prevent.
    """


@dataclass(frozen=True, slots=True)
class Provenance:
    """Where a value came from.

    `inspector` is the tool name ("ffprobe", "mediainfo", or "computed").
    `field_path` is the raw source path, e.g. "streams[0].pix_fmt".
    `derived_from` is non-empty when the value was computed rather than read, which
    reports must disclose (spec 9.6.4).
    """

    inspector: str
    field_path: str
    tool_version: str | None = None
    derived_from: tuple[str, ...] = ()

    @property
    def is_derived(self) -> bool:
        return bool(self.derived_from)

    def describe(self) -> str:
        base = f"{self.inspector}:{self.field_path}"
        return f"{base} (derived from {', '.join(self.derived_from)})" if self.derived_from else base


#: Provenance for values PreflightQC computed itself rather than read from an inspector.
def computed(field_path: str, *, derived_from: tuple[str, ...]) -> Provenance:
    return Provenance(inspector="computed", field_path=field_path, derived_from=derived_from)


@dataclass(frozen=True, slots=True)
class MetaField(Generic[T]):
    """A single metadata field in one of the four states.

    Construct through the classmethods, never directly, so that an invalid combination
    of state and payload cannot be expressed.
    """

    state: FieldState
    _value: T | None = None
    provenance: Provenance | None = None
    reason: str | None = None
    #: Populated only for CONFLICTED: the competing (value, provenance) observations.
    conflict: tuple[tuple[T, Provenance], ...] = field(default_factory=tuple)
    #: Retained for UNDETERMINED when an inspector reported something unmappable, so a
    #: report can show what was actually seen without the engine trusting it.
    raw: str | None = None

    # -- constructors ----------------------------------------------------------

    @classmethod
    def known(cls, value: T, provenance: Provenance) -> MetaField[T]:
        return cls(state=FieldState.KNOWN, _value=value, provenance=provenance)

    @classmethod
    def not_present(cls, provenance: Provenance | None = None) -> MetaField[T]:
        return cls(state=FieldState.NOT_PRESENT, provenance=provenance)

    @classmethod
    def undetermined(
        cls,
        reason: str,
        provenance: Provenance | None = None,
        raw: str | None = None,
    ) -> MetaField[T]:
        return cls(state=FieldState.UNDETERMINED, provenance=provenance, reason=reason, raw=raw)

    @classmethod
    def conflicted(cls, *observations: tuple[T, Provenance]) -> MetaField[T]:
        if len(observations) < 2:
            raise ValueError("a conflicted field needs at least two observations")
        return cls(state=FieldState.CONFLICTED, conflict=tuple(observations))

    # -- inspection ------------------------------------------------------------

    @property
    def is_known(self) -> bool:
        return self.state is FieldState.KNOWN

    @property
    def is_not_present(self) -> bool:
        return self.state is FieldState.NOT_PRESENT

    @property
    def is_undetermined(self) -> bool:
        return self.state is FieldState.UNDETERMINED

    @property
    def is_conflicted(self) -> bool:
        return self.state is FieldState.CONFLICTED

    @property
    def is_absent(self) -> bool:
        """True when there is no single usable value: NOT_PRESENT or UNDETERMINED.

        These two are reported differently to the user but are handled identically by
        the rule engine: both yield an UNKNOWN finding, never a FAIL.
        """
        return self.state in (FieldState.NOT_PRESENT, FieldState.UNDETERMINED)

    @property
    def value(self) -> T:
        """The determined value.

        Raises FieldNotKnownError on any non-KNOWN state. There is intentionally no
        default: callers must decide what absence means in their context.
        """
        if self.state is not FieldState.KNOWN:
            raise FieldNotKnownError(
                f"field is {self.state.value}, not KNOWN"
                + (f" ({self.reason})" if self.reason else "")
            )
        # A KNOWN field always carries a value; the Optional is a construction artefact.
        return self._value  # type: ignore[return-value]

    def or_none(self) -> T | None:
        """The value if KNOWN, else None. Never raises."""
        return self._value if self.state is FieldState.KNOWN else None

    def unwrap_or(self, fallback: T) -> T:
        """The value if KNOWN, else the caller-supplied fallback.

        Only for presentation. Never use this to feed a rule comparison.
        """
        return self._value if self.state is FieldState.KNOWN else fallback  # type: ignore[return-value]

    def conflict_values(self) -> tuple[T, ...]:
        return tuple(value for value, _ in self.conflict)

    # -- display ---------------------------------------------------------------

    def describe(self) -> str:
        """A short human-readable rendering, used by findings and reports.

        Absent states render as explicit words, never as blank or zero.
        """
        match self.state:
            case FieldState.KNOWN:
                return str(self._value)
            case FieldState.NOT_PRESENT:
                return "not present in file"
            case FieldState.UNDETERMINED:
                base = "could not be determined"
                return f"{base} ({self.reason})" if self.reason else base
            case FieldState.CONFLICTED:
                parts = [f"{v} [{p.inspector}]" for v, p in self.conflict]
                return "inspectors disagree: " + " vs ".join(parts)
        raise AssertionError(f"unhandled field state: {self.state}")  # pragma: no cover

    def __str__(self) -> str:
        return self.describe()


def absent_reason(field_obj: MetaField[object]) -> str:
    """Explain, for an UNKNOWN finding, why a field could not be evaluated."""
    if field_obj.is_not_present:
        return "the property is not present in the file"
    if field_obj.is_undetermined:
        return field_obj.reason or "the inspectors could not determine this property"
    raise ValueError("field is not absent")
