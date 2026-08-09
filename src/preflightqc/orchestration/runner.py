"""Batch orchestration: inspect, normalise, validate — concurrently and cancellably.

Three properties this module must hold, all from specification 13:

1. **Per-file isolation.** Every job runs inside a boundary that converts *any*
   exception into a NOT_INSPECTED result with a reason. One broken file never
   terminates a batch.
2. **Input-order presentation.** Results stream as they complete, but are presented in
   the order the user added them, so the list does not reshuffle while they read it.
3. **Bounded, prompt cancellation.** Queued work stops, in-flight inspectors are
   terminated, completed results are preserved, and the batch is marked partial.

Threads rather than processes: the work is subprocess- and I/O-bound, so the GIL is
released for essentially all of it, and threads keep cancellation and result delivery
simple.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from preflightqc.adapters import ffprobe, mediainfo
from preflightqc.adapters.base import FILE_LEVEL_FAILURES, FailureKind, InspectorFailure
from preflightqc.core.model import Diagnostics, InspectorRecord
from preflightqc.normalise.normaliser import normalise
from preflightqc.platform.binaries import InspectorKind, StartupReport
from preflightqc.results.aggregate import (
    BatchSummary,
    FileResult,
    InspectionFailure,
    build_file_result,
    build_not_inspected,
    summarise,
)
from preflightqc.rules.document import PresetDocument
from preflightqc.rules.engine import evaluate

DEFAULT_WORKERS = 4
DEFAULT_TIMEOUT_SECONDS = 60.0

#: Remediation hints, keyed by failure kind. Spec 23 asks for actionable messages, and
#: "permission denied" without a next step is not actionable.
_HINTS: dict[FailureKind, str] = {
    FailureKind.PERMISSION_DENIED: (
        "Check that your account can read this file, and that it is not open "
        "exclusively in another application."
    ),
    FailureKind.FILE_UNREADABLE: (
        "The file may have been moved, renamed or deleted since the batch started."
    ),
    FailureKind.TIMEOUT: (
        "The inspector did not finish in time. Very large files on slow or network "
        "storage may need a longer timeout in settings."
    ),
    FailureKind.MALFORMED_OUTPUT: (
        "The file could not be parsed as media. It may be corrupt or truncated."
    ),
    FailureKind.NOT_FOUND: (
        "The bundled inspector is missing. Reinstall PreflightQC."
    ),
    FailureKind.LAUNCH_FAILED: (
        "The bundled inspector could not be started. Antivirus software may be "
        "blocking it."
    ),
}


class JobState(Enum):
    QUEUED = "QUEUED"
    INSPECTING = "INSPECTING"
    VALIDATING = "VALIDATING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class InspectionSettings:
    workers: int = DEFAULT_WORKERS
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    #: Reading a frame for HDR side data engages the decoder. Off by default; see the
    #: ffprobe adapter's module docstring.
    read_hdr_frame: bool = False


@dataclass(frozen=True, slots=True)
class BatchProgress:
    total: int
    completed: int
    in_flight: int

    @property
    def remaining(self) -> int:
        return max(0, self.total - self.completed)


class CancellationToken:
    """A cooperative cancellation flag, checked between pipeline stages."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def __call__(self) -> bool:
        return self._event.is_set()


@dataclass(slots=True)
class _CacheEntry:
    key: tuple[str, int, int]
    ffprobe_raw: object | None
    mediainfo_raw: object | None
    records: tuple[InspectorRecord, ...]
    failure: InspectionFailure | None


class InspectionCache:
    """Session-scoped cache keyed on (path, size, mtime).

    This is what lets a user switch preset and re-run without paying for inspection
    again -- the expensive part is the subprocess, and nothing about it depends on which
    rules will be applied.
    """

    def __init__(self) -> None:
        self._entries: dict[tuple[str, int, int], _CacheEntry] = {}
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    @staticmethod
    def key_for(path: Path) -> tuple[str, int, int] | None:
        try:
            stat = path.stat()
        except OSError:
            return None
        return (str(path).lower(), stat.st_size, stat.st_mtime_ns)

    def get(self, key: tuple[str, int, int]) -> _CacheEntry | None:
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None:
                self.hits += 1
            else:
                self.misses += 1
            return entry

    def put(self, entry: _CacheEntry) -> None:
        with self._lock:
            self._entries[entry.key] = entry

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


@dataclass(slots=True)
class BatchOutcome:
    results: tuple[FileResult, ...]
    summary: BatchSummary
    cancelled: bool

    @property
    def partial(self) -> bool:
        return self.summary.is_partial


def _failure_for(outcome: InspectorFailure) -> InspectionFailure:
    return InspectionFailure(
        kind=outcome.kind.value,
        message=outcome.message,
        hint=_HINTS.get(outcome.kind),
    )


class BatchRunner:
    """Runs one batch of files against one preset."""

    def __init__(
        self,
        *,
        startup: StartupReport,
        settings: InspectionSettings | None = None,
        cache: InspectionCache | None = None,
    ) -> None:
        self._startup = startup
        self._settings = settings or InspectionSettings()
        self._cache = cache if cache is not None else InspectionCache()

    @property
    def cache(self) -> InspectionCache:
        return self._cache

    # -- inspection ---------------------------------------------------------

    def _inspect(self, path: Path, token: CancellationToken) -> _CacheEntry:
        """Run both inspectors, honouring the cache. Never raises."""
        key = InspectionCache.key_for(path)
        if key is None:
            return _CacheEntry(
                key=(str(path).lower(), -1, -1),
                ffprobe_raw=None,
                mediainfo_raw=None,
                records=(),
                failure=InspectionFailure(
                    kind=FailureKind.FILE_UNREADABLE.value,
                    message="the file is no longer available",
                    hint=_HINTS[FailureKind.FILE_UNREADABLE],
                ),
            )

        cached = self._cache.get(key)
        if cached is not None:
            return cached

        records: list[InspectorRecord] = []
        ff_raw = None
        mi_raw = None
        first_file_level_failure: InspectorFailure | None = None

        for kind, adapter in (
            (InspectorKind.FFPROBE, ffprobe),
            (InspectorKind.MEDIAINFO, mediainfo),
        ):
            if token.cancelled:
                break
            info = self._startup.get(kind)
            if info is None or not info.available or info.path is None:
                records.append(
                    InspectorRecord(
                        name=kind.value,
                        version=None,
                        ok=False,
                        failure_kind=FailureKind.NOT_FOUND.value,
                        message=info.message if info else "not configured",
                    )
                )
                continue

            extra = (
                {"read_hdr_frame": self._settings.read_hdr_frame}
                if kind is InspectorKind.FFPROBE
                else {}
            )
            outcome = adapter.inspect(
                info.path,
                path,
                timeout_seconds=self._settings.timeout_seconds,
                **extra,
            )
            if outcome.ok:
                parsed = adapter.parse_outcome(outcome, tool_version=info.version)
                if kind is InspectorKind.FFPROBE:
                    ff_raw = parsed
                else:
                    mi_raw = parsed
                records.append(
                    InspectorRecord(
                        name=kind.value,
                        version=info.version,
                        ok=True,
                        duration_ms=outcome.duration_ms,
                    )
                )
            else:
                assert isinstance(outcome, InspectorFailure)
                records.append(
                    InspectorRecord(
                        name=kind.value,
                        version=info.version,
                        ok=False,
                        failure_kind=outcome.kind.value,
                        message=outcome.message,
                        duration_ms=outcome.duration_ms,
                    )
                )
                # A file-level failure (unreadable, permission denied) is about the
                # file, so it is the reason worth reporting if nothing succeeds.
                if outcome.kind in FILE_LEVEL_FAILURES and first_file_level_failure is None:
                    first_file_level_failure = outcome

        failure: InspectionFailure | None = None
        if ff_raw is None and mi_raw is None:
            if first_file_level_failure is not None:
                failure = _failure_for(first_file_level_failure)
            else:
                worst = next((r for r in records if not r.ok), None)
                kind_name = worst.failure_kind if worst and worst.failure_kind else "UNKNOWN"
                # `failure_kind` is stored as the enum's *value*; look the member back up
                # by value so the remediation hint is actually found.
                try:
                    hint = _HINTS.get(FailureKind(kind_name))
                except ValueError:
                    hint = None
                failure = InspectionFailure(
                    kind=kind_name,
                    message=(
                        worst.message
                        if worst and worst.message
                        else "no inspector could read this file"
                    ),
                    hint=hint,
                )

        entry = _CacheEntry(
            key=key,
            ffprobe_raw=ff_raw,
            mediainfo_raw=mi_raw,
            records=tuple(records),
            failure=failure,
        )
        self._cache.put(entry)
        return entry

    # -- one job ------------------------------------------------------------

    def _run_job(
        self, path: Path, preset: PresetDocument, token: CancellationToken
    ) -> FileResult:
        """Inspect, normalise and validate one file.

        The outer try/except is the isolation boundary required by spec 13.3: whatever
        goes wrong in here, the batch keeps going and this file gets an honest reason.
        """
        try:
            if token.cancelled:
                return build_not_inspected(
                    path=path,
                    failure=InspectionFailure(
                        kind=FailureKind.CANCELLED.value, message="the batch was cancelled"
                    ),
                    preset_id=preset.preset_id,
                    ruleset_version=preset.ruleset_version,
                )

            entry = self._inspect(path, token)
            if entry.failure is not None:
                return build_not_inspected(
                    path=path,
                    failure=entry.failure,
                    preset_id=preset.preset_id,
                    ruleset_version=preset.ruleset_version,
                    diagnostics=Diagnostics(inspectors=entry.records),
                )

            try:
                stat = path.stat()
                size, mtime = stat.st_size, stat.st_mtime_ns
            except OSError:
                size, mtime = None, 0

            media = normalise(
                path,
                ffprobe=entry.ffprobe_raw,  # type: ignore[arg-type]
                mediainfo=entry.mediainfo_raw,  # type: ignore[arg-type]
                size_bytes=size,
                modified_ns=mtime,
                inspector_records=entry.records,
            )
            findings = evaluate(media, preset)
            return build_file_result(
                path=path,
                media=media,
                findings=findings,
                preset_id=preset.preset_id,
                ruleset_version=preset.ruleset_version,
            )
        except Exception as exc:
            return build_not_inspected(
                path=path,
                failure=InspectionFailure(
                    kind="INTERNAL_ERROR",
                    message=f"{type(exc).__name__}: {exc}",
                    hint="This is a defect in PreflightQC. The rest of the batch continued.",
                ),
                preset_id=preset.preset_id,
                ruleset_version=preset.ruleset_version,
            )

    # -- the batch ----------------------------------------------------------

    def run(
        self,
        paths: Sequence[Path],
        preset: PresetDocument,
        *,
        token: CancellationToken | None = None,
        on_result: Callable[[int, FileResult], None] | None = None,
        on_progress: Callable[[BatchProgress], None] | None = None,
    ) -> BatchOutcome:
        """Run a batch. Returns once every job has settled or been cancelled."""
        token = token or CancellationToken()
        ordered = list(paths)
        total = len(ordered)
        results: list[FileResult | None] = [None] * total

        if total == 0:
            return BatchOutcome(
                results=(),
                summary=summarise(
                    (),
                    preset_id=preset.preset_id,
                    preset_display_name=preset.display_name,
                    ruleset_version=preset.ruleset_version,
                    total_files=0,
                    cancelled=token.cancelled,
                ),
                cancelled=token.cancelled,
            )

        completed = 0
        lock = threading.Lock()
        workers = max(1, min(self._settings.workers, total))

        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="pfqc") as pool:
            futures: dict[Future[FileResult], int] = {
                pool.submit(self._run_job, path, preset, token): index
                for index, path in enumerate(ordered)
            }
            for future in futures:
                index = futures[future]

                def _done(fut: Future[FileResult], index: int = index) -> None:
                    nonlocal completed
                    result = fut.result()
                    with lock:
                        results[index] = result
                        completed += 1
                        snapshot = BatchProgress(
                            total=total,
                            completed=completed,
                            in_flight=min(workers, total - completed),
                        )
                    if on_result is not None:
                        on_result(index, result)
                    if on_progress is not None:
                        on_progress(snapshot)

                future.add_done_callback(_done)

        # Presentation order is input order, never completion order (spec 13.8).
        finished = tuple(r for r in results if r is not None)
        cancelled = token.cancelled
        return BatchOutcome(
            results=finished,
            summary=summarise(
                finished,
                preset_id=preset.preset_id,
                preset_display_name=preset.display_name,
                ruleset_version=preset.ruleset_version,
                total_files=total,
                completed=not cancelled,
                cancelled=cancelled,
            ),
            cancelled=cancelled,
        )
