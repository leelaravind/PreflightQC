"""Inspector binary resolution and the startup self-check.

One rule governs this module: **PATH is never consulted** (spec 22.4).

Falling back to a PATH binary would mean PreflightQC could silently run an unknown
build -- possibly a GPL one, possibly a different version producing different metadata --
and report results as though they came from the build we tested and licensed. A missing
binary is an actionable error, never a silent substitution.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from preflightqc.platform import process
from preflightqc.platform.paths import bundled_binaries_dir


class InspectorKind(Enum):
    FFPROBE = "ffprobe"
    MEDIAINFO = "mediainfo"


#: Candidate filenames per inspector, in preference order.
_CANDIDATES: dict[InspectorKind, tuple[str, ...]] = {
    InspectorKind.FFPROBE: ("ffprobe.exe", "ffprobe"),
    InspectorKind.MEDIAINFO: ("mediainfo.exe", "MediaInfo.exe", "mediainfo"),
}

#: Configure switches that must never be present.
#:
#: These two are the whole ballgame: `--enable-gpl` would impose copyleft on
#: PreflightQC's own source, and `--enable-nonfree` produces a binary FFmpeg's own
#: LICENSE.md calls "unredistributable".
PROHIBITED_SWITCHES: tuple[str, ...] = ("--enable-gpl", "--enable-nonfree")

#: Components that must not be *enabled* in a shipped ffprobe build.
#: Mirrors docs/licensing/LICENSING-GATE-V1.md section 7.
#:
#: This is exactly FFmpeg's own `EXTERNAL_LIBRARY_GPL_LIST` plus its nonfree and
#: GPLv3 lists. Enabling any of them would force `--enable-gpl` (or make the binary
#: unredistributable), which is the thing we actually care about.
#:
#: Deliberately NOT listed: `gmp`, `libaribb24`, `liblensfun`. FFmpeg's LICENSE.md puts
#: these under "LGPL version 3" and they are permitted via `--enable-version3`, which
#: the LGPLv3 spec-lock amendment accepts. They upgrade the licence; they do not make
#: it copyleft.
#:
#: Also NOT listed: `libzvbi`. See LIBZVBI_MIN_VERSION below.
#:
#: Names are normalised (hyphens to underscores) before comparison because FFmpeg's
#: configure switches use hyphens (`--enable-libfdk-aac`) while its internal lists use
#: underscores (`libfdk_aac`).
PROHIBITED_COMPONENTS: tuple[str, ...] = (
    # EXTERNAL_LIBRARY_GPL_LIST — each forces --enable-gpl
    "avisynth",
    "frei0r",
    "libcdio",
    "libdavs2",
    "libdvdnav",
    "libdvdread",
    "librubberband",
    "libvidstab",
    "libx264",
    "libx265",
    "libxavs",
    "libxavs2",
    "libxvid",
    # EXTERNAL_LIBRARY_GPLV3_LIST — forces --enable-gpl --enable-version3
    "libsmbclient",
    # EXTERNAL_LIBRARY_NONFREE_LIST — renders the binary unredistributable
    "decklink",
    "libfdk_aac",
    "libmpeghdec",
    # HWACCEL_LIBRARY_NONFREE_LIST
    "libnpp",
    "cuda_nvcc",
    "cuda_sdk",
)

#: `--enable-version3` upgrades FFmpeg from LGPL v2.1 to LGPL v3.
#:
#: Permitted since the LGPLv3 spec-lock amendment: the mainstream BtbN
#: `win64-lgpl-shared` build carries it, and building a custom FFmpeg purely to avoid
#: it would make PreflightQC a "modifier" with its own source-correspondence duties --
#: a worse licensing position, not a better one.
#:
#: It is still *reported*, because it determines which licence text and notice wording
#: the product must ship. A build that does NOT carry it is LGPL v2.1 and would need
#: different notices, so the fact is recorded either way.
VERSION3_SWITCH = "--enable-version3"

#: libzvbi is LGPL-2.1-or-later from version 0.2.28 onward; it was GPL-2+ before that.
#:
#: FFmpeg's configure encodes this directly (9.0, line 7510):
#:
#:     enabled libzvbi && require_pkg_config libzvbi zvbi-0.2 ... &&
#:       { test_cpp_condition libzvbi.h "VBI_VERSION_MAJOR > 0 || ... MICRO >= 28" ||
#:         enabled gpl || die "ERROR: libzvbi requires version 0.2.28 or --enable-gpl."; }
#:
#: So a build that enables libzvbi *without* --enable-gpl has, by FFmpeg's own check,
#: linked the LGPL version. libzvbi is therefore not prohibited; the absence of
#: --enable-gpl is what proves it safe, and that is already checked above.
LIBZVBI_MIN_LGPL_VERSION = "0.2.28"

_FLAG = re.compile(r"--(enable|disable)-([A-Za-z0-9_-]+)")


def _normalise(name: str) -> str:
    return name.replace("-", "_").lower()


def enabled_components(text: str) -> frozenset[str]:
    """The set of components a configuration string switches ON.

    Parsing matters: `--disable-libx264` *contains* `libx264`, so a substring scan flags
    a compliant build. A scanner that cries wolf on every good build trains people to
    ignore it, which is worse than having no scanner at all.
    """
    return frozenset(
        _normalise(match.group(2))
        for match in _FLAG.finditer(text)
        if match.group(1) == "enable"
    )


def audit_configuration(text: str) -> tuple[str, ...]:
    """Real licensing violations in an ffprobe configuration string.

    Returns only findings that would actually block release: the two prohibited
    switches, and any prohibited component genuinely enabled. `--enable-version3` is
    permitted and is reported separately by `licence_version()`, not as a violation.
    """
    violations = [switch for switch in PROHIBITED_SWITCHES if switch in text]
    prohibited = {_normalise(name) for name in PROHIBITED_COMPONENTS}
    violations.extend(
        sorted(f"--enable-{name}" for name in enabled_components(text) & prohibited)
    )
    return tuple(violations)


def licence_version(text: str) -> str:
    """The LGPL version this build is actually under.

    Not a violation either way -- but the product must ship the matching licence text
    and notice wording, so getting this right is the difference between an accurate
    notice and a false one.
    """
    return "LGPL-3.0-or-later" if VERSION3_SWITCH in text else "LGPL-2.1-or-later"


@dataclass(frozen=True, slots=True)
class InspectorInfo:
    """What the self-check learned about one inspector."""

    kind: InspectorKind
    path: Path | None
    version: str | None
    available: bool
    message: str = ""
    #: Prohibited build components found in the reported configuration, if any.
    licence_violations: tuple[str, ...] = ()
    #: The licence the build is actually under, e.g. "LGPL-3.0-or-later". Recorded so
    #: the shipped notices can state the real version rather than an assumed one.
    licence: str | None = None
    #: The verbatim configuration string, for the dependency manifest and the report.
    configuration: str | None = None

    @property
    def licence_ok(self) -> bool:
        return not self.licence_violations

    def describe(self) -> str:
        if not self.available:
            return f"{self.kind.value}: unavailable — {self.message}"
        return f"{self.kind.value} {self.version or 'unknown version'}"


def locate(kind: InspectorKind, *, search_dir: Path | None = None) -> Path | None:
    """Find a bundled inspector by absolute path. Never consults PATH."""
    directory = search_dir or bundled_binaries_dir()
    for name in _CANDIDATES[kind]:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    return None


_FFPROBE_VERSION = re.compile(r"ffprobe version (\S+)")
_FFPROBE_CONFIG = re.compile(r"^configuration:(.*)$", re.M)
_MEDIAINFO_LIB_VERSION = re.compile(r"MediaInfoLib\s*-\s*v?([0-9][0-9.]*)")
_MEDIAINFO_CLI_VERSION = re.compile(r"MediaInfo Command line[,\s]+v?([0-9][0-9.]*)")


def _probe_ffprobe(path: Path, timeout: float) -> InspectorInfo:
    result = process.run([str(path), "-hide_banner", "-version"], timeout_seconds=timeout)
    if not result.ok:
        return InspectorInfo(
            kind=InspectorKind.FFPROBE,
            path=path,
            version=None,
            available=False,
            message=result.message or f"exit {result.exit_code}",
        )
    text = f"{result.stdout}\n{result.stderr}"
    match = _FFPROBE_VERSION.search(text)
    config = _FFPROBE_CONFIG.search(text)
    return InspectorInfo(
        kind=InspectorKind.FFPROBE,
        path=path,
        version=match.group(1) if match else None,
        available=True,
        licence_violations=audit_configuration(text),
        licence=licence_version(text),
        configuration=config.group(1).strip() if config else None,
    )


def _probe_mediainfo(path: Path, timeout: float) -> InspectorInfo:
    result = process.run([str(path), "--Version"], timeout_seconds=timeout)
    # MediaInfo's --Version exits non-zero on some builds while still printing the
    # version, so the output is trusted over the exit code here.
    text = f"{result.stdout}\n{result.stderr}".strip()
    if result.status is not process.RunStatus.COMPLETED or not text:
        return InspectorInfo(
            kind=InspectorKind.MEDIAINFO,
            path=path,
            version=None,
            available=False,
            message=result.message or f"exit {result.exit_code}",
        )
    match = _MEDIAINFO_LIB_VERSION.search(text) or _MEDIAINFO_CLI_VERSION.search(text)
    version = match.group(1) if match else None
    return InspectorInfo(
        kind=InspectorKind.MEDIAINFO,
        path=path,
        version=version,
        available=True,
        licence="BSD-2-Clause",
    )


def self_check(
    kind: InspectorKind, *, search_dir: Path | None = None, timeout: float = 20.0
) -> InspectorInfo:
    """Verify one inspector launches, and capture its version for the report."""
    path = locate(kind, search_dir=search_dir)
    if path is None:
        directory = search_dir or bundled_binaries_dir()
        return InspectorInfo(
            kind=kind,
            path=None,
            version=None,
            available=False,
            message=(
                f"not found in {directory}. PreflightQC only runs the inspector bundled "
                "with it, and never one found on the system PATH."
            ),
        )
    if kind is InspectorKind.FFPROBE:
        return _probe_ffprobe(path, timeout)
    return _probe_mediainfo(path, timeout)


@dataclass(frozen=True, slots=True)
class StartupReport:
    """The result of checking every inspector at application start."""

    inspectors: tuple[InspectorInfo, ...]

    @property
    def usable(self) -> bool:
        """At least one inspector must work for validation to mean anything."""
        return any(info.available for info in self.inspectors)

    @property
    def fully_available(self) -> bool:
        return all(info.available for info in self.inspectors)

    @property
    def licence_violations(self) -> tuple[str, ...]:
        return tuple(v for info in self.inspectors for v in info.licence_violations)

    def get(self, kind: InspectorKind) -> InspectorInfo | None:
        return next((i for i in self.inspectors if i.kind is kind), None)

    def versions(self) -> dict[str, str]:
        return {i.kind.value: (i.version or "unknown") for i in self.inspectors if i.available}

    def problems(self) -> tuple[str, ...]:
        messages = [i.describe() for i in self.inspectors if not i.available]
        if self.licence_violations:
            messages.append(
                "The bundled ffprobe reports prohibited build components: "
                + ", ".join(sorted(set(self.licence_violations)))
                + ". PreflightQC must ship an unmodified LGPL build with no GPL or "
                "nonfree component."
            )
        return tuple(messages)


def check_all(*, search_dir: Path | None = None, timeout: float = 20.0) -> StartupReport:
    """Run the startup self-check for every inspector."""
    return StartupReport(
        inspectors=tuple(
            self_check(kind, search_dir=search_dir, timeout=timeout) for kind in InspectorKind
        )
    )
