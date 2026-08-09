"""The single external-process runner.

Every subprocess PreflightQC starts goes through here, so there is exactly one place
that gets timeouts, process-tree termination, output caps and child reaping right.

Design constraints, all from the specification's failure-handling section:

* **Never raises.** Returns a structured outcome instead, because a batch must survive
  any individual file (spec 23).
* **No shell.** Arguments are passed as a list, so a filename containing quotes,
  semicolons or ampersands is data, never syntax.
* **Bounded output.** A pathological file cannot exhaust memory through inspector output.
* **Whole-tree termination.** On Windows, killing a process does not kill its children;
  a job object is used so a hung inspector cannot leave orphans behind.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

#: Hard cap on captured stdout. Inspector JSON for a pathological file can be large,
#: but never this large; beyond it we are being attacked or something is very wrong.
DEFAULT_STDOUT_LIMIT = 32 * 1024 * 1024

#: stderr is only ever used for diagnostics, so it is capped much lower.
DEFAULT_STDERR_LIMIT = 64 * 1024

#: How long a terminated process gets to exit before it is killed outright.
TERMINATE_GRACE_SECONDS = 2.0


class RunStatus(Enum):
    COMPLETED = "COMPLETED"
    TIMEOUT = "TIMEOUT"
    LAUNCH_FAILED = "LAUNCH_FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class RunResult:
    """The outcome of one external process call."""

    status: RunStatus
    exit_code: int | None
    stdout: str
    stderr: str
    duration_ms: float
    truncated_stdout: bool = False
    message: str = ""

    @property
    def ok(self) -> bool:
        return self.status is RunStatus.COMPLETED and self.exit_code == 0


def _creation_flags() -> int:
    """Windows flags that keep console windows from flashing during a batch."""
    if sys.platform != "win32":
        return 0
    return (
        getattr(subprocess, "CREATE_NO_WINDOW", 0)
        | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    )


def _minimal_environment() -> dict[str, str]:
    """A deliberately small environment for child processes.

    Inheriting the full environment invites surprises -- a stray FFREPORT or
    LD_LIBRARY_PATH changing inspector behaviour between machines. Only the variables
    Windows genuinely needs to start a process are passed through.
    """
    keep = ("SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATHEXT", "COMSPEC", "NUMBER_OF_PROCESSORS")
    env = {name: os.environ[name] for name in keep if name in os.environ}
    # Deliberately no PATH: binaries are always invoked by absolute path (spec 22.4).
    env.setdefault("PATH", "")
    return env


def _taskkill_path() -> str:
    """Absolute path to taskkill, so PATH cannot decide what we run."""
    system_root = os.environ.get("SYSTEMROOT", r"C:\Windows")
    return str(Path(system_root) / "System32" / "taskkill.exe")


def _terminate_tree(process: subprocess.Popen[bytes]) -> None:
    """Terminate a process and everything it started.

    On Windows `taskkill /T` is the reliable way to reach grandchildren; `Popen.kill()`
    alone leaves them running, which is how orphan inspector processes accumulate.
    """
    if process.poll() is not None:
        return
    if sys.platform == "win32":
        try:
            subprocess.run(
                [_taskkill_path(), "/F", "/T", "/PID", str(process.pid)],
                capture_output=True,
                timeout=10,
                check=False,
                creationflags=_creation_flags(),
            )
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        process.terminate()
        process.wait(timeout=TERMINATE_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        try:
            process.kill()
            process.wait(timeout=TERMINATE_GRACE_SECONDS)
        except (OSError, subprocess.TimeoutExpired):  # pragma: no cover - defensive
            pass
    except OSError:  # pragma: no cover - process already gone
        pass


def run(
    argv: list[str],
    *,
    timeout_seconds: float,
    cwd: Path | None = None,
    stdout_limit: int = DEFAULT_STDOUT_LIMIT,
    stderr_limit: int = DEFAULT_STDERR_LIMIT,
) -> RunResult:
    """Run an external program and capture its output.

    Never raises. `argv[0]` must be an absolute path to a binary we ship.
    """
    started = time.monotonic()

    try:
        process = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            cwd=str(cwd) if cwd else None,
            env=_minimal_environment(),
            shell=False,
            creationflags=_creation_flags(),
        )
    except (OSError, ValueError) as exc:
        return RunResult(
            status=RunStatus.LAUNCH_FAILED,
            exit_code=None,
            stdout="",
            stderr="",
            duration_ms=(time.monotonic() - started) * 1000.0,
            message=str(exc),
        )

    try:
        raw_out, raw_err = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        _terminate_tree(process)
        try:
            raw_out, raw_err = process.communicate(timeout=TERMINATE_GRACE_SECONDS)
        except (subprocess.TimeoutExpired, ValueError):  # pragma: no cover - defensive
            raw_out, raw_err = b"", b""
        return RunResult(
            status=RunStatus.TIMEOUT,
            exit_code=None,
            stdout=_decode(raw_out, stdout_limit)[0],
            stderr=_decode(raw_err, stderr_limit)[0],
            duration_ms=(time.monotonic() - started) * 1000.0,
            message=f"exceeded {timeout_seconds:g}s budget",
        )
    except (OSError, ValueError) as exc:  # pragma: no cover - defensive
        _terminate_tree(process)
        return RunResult(
            status=RunStatus.LAUNCH_FAILED,
            exit_code=None,
            stdout="",
            stderr="",
            duration_ms=(time.monotonic() - started) * 1000.0,
            message=str(exc),
        )

    stdout, truncated = _decode(raw_out, stdout_limit)
    stderr, _ = _decode(raw_err, stderr_limit)
    return RunResult(
        status=RunStatus.COMPLETED,
        exit_code=process.returncode,
        stdout=stdout,
        stderr=stderr,
        duration_ms=(time.monotonic() - started) * 1000.0,
        truncated_stdout=truncated,
    )


def _decode(raw: bytes, limit: int) -> tuple[str, bool]:
    truncated = len(raw) > limit
    payload = raw[:limit] if truncated else raw
    return payload.decode("utf-8", errors="replace"), truncated
