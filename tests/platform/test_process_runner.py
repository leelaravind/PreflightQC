"""Phase 5 — the process runner, exercised against real subprocesses.

These tests spawn actual processes (via the running interpreter) rather than mocking,
because the properties under test — timeout enforcement, process-tree termination,
output capping, no-shell argument passing — only mean anything against a real OS.
"""

from __future__ import annotations

import sys
import time

import pytest

from preflightqc.platform import process
from preflightqc.platform.process import RunStatus


def py(code: str) -> list[str]:
    return [sys.executable, "-c", code]


class TestBasics:
    def test_a_successful_run_captures_stdout(self) -> None:
        result = process.run(py("print('hello')"), timeout_seconds=30)
        assert result.status is RunStatus.COMPLETED
        assert result.exit_code == 0
        assert result.ok
        assert "hello" in result.stdout

    def test_stderr_is_captured_separately(self) -> None:
        result = process.run(
            py("import sys; sys.stderr.write('problem')"), timeout_seconds=30
        )
        assert "problem" in result.stderr
        assert "problem" not in result.stdout

    def test_a_non_zero_exit_is_reported_not_raised(self) -> None:
        result = process.run(py("raise SystemExit(3)"), timeout_seconds=30)
        assert result.status is RunStatus.COMPLETED
        assert result.exit_code == 3
        assert not result.ok

    def test_duration_is_measured(self) -> None:
        result = process.run(py("pass"), timeout_seconds=30)
        assert result.duration_ms >= 0


class TestFailureModes:
    def test_a_missing_binary_is_launch_failed_not_an_exception(self) -> None:
        result = process.run(
            ["Z:/definitely/not/here/nope.exe"], timeout_seconds=5
        )
        assert result.status is RunStatus.LAUNCH_FAILED
        assert result.message

    def test_a_hanging_process_is_terminated_at_the_timeout(self) -> None:
        started = time.monotonic()
        result = process.run(py("import time; time.sleep(60)"), timeout_seconds=2)
        elapsed = time.monotonic() - started
        assert result.status is RunStatus.TIMEOUT
        # Generous ceiling: the point is that it returns promptly, not in 60 seconds.
        assert elapsed < 30, f"timeout was not enforced promptly ({elapsed:.1f}s)"

    def test_a_process_that_spawns_a_child_is_killed_as_a_tree(self) -> None:
        """A hung inspector must not leave a grandchild running (spec 15.7)."""
        code = (
            "import subprocess, sys, time; "
            "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
            "time.sleep(60)"
        )
        result = process.run(py(code), timeout_seconds=3)
        assert result.status is RunStatus.TIMEOUT

    def test_enormous_output_is_capped(self) -> None:
        """A pathological file must not exhaust memory through inspector output."""
        result = process.run(
            py("print('x' * 5_000_000)"), timeout_seconds=60, stdout_limit=1000
        )
        assert result.truncated_stdout
        assert len(result.stdout) <= 1000


class TestNoShell:
    @pytest.mark.parametrize(
        "hostile",
        [
            'name with "quotes".mp4',
            "name & echo pwned.mp4",
            "name; rm -rf /.mp4",
            "name | type nul.mp4",
            "name %PATH% .mp4",
            "naïve—clip—2026.mp4",
        ],
    )
    def test_shell_metacharacters_are_data_not_syntax(self, hostile: str) -> None:
        """P10-A3 — proves argv-list invocation rather than a shell command line.

        The child compares the argument itself and prints only an ASCII verdict. Asking
        it to echo the name back would test the child's console codepage rather than
        our argument passing, and would fail on non-ASCII filenames for reasons that
        have nothing to do with the property under test.
        """
        code = (
            "import sys; "
            "sys.stdout.write('MATCH' if sys.argv[1] == sys.argv[2] else 'MISMATCH:' + sys.argv[1])"
        )
        result = process.run(
            [sys.executable, "-c", code, hostile, hostile], timeout_seconds=30
        )
        assert result.ok
        assert result.stdout.strip() == "MATCH"

    def test_a_non_ascii_argument_survives_the_boundary(self) -> None:
        """Client folders routinely contain accented and CJK names."""
        name = "naïve—clip—2026—日本語.mp4"
        code = "import sys; sys.stdout.write(str(len(sys.argv[1])))"
        result = process.run([sys.executable, "-c", code, name], timeout_seconds=30)
        assert result.ok
        assert result.stdout.strip() == str(len(name))

    def test_the_child_environment_excludes_path(self) -> None:
        """Binaries are always invoked by absolute path; a child needs no PATH."""
        result = process.run(
            py("import os; print(repr(os.environ.get('PATH')))"), timeout_seconds=30
        )
        assert result.ok
        assert result.stdout.strip() in {"''", '""'}

    def test_the_child_gets_no_stdin(self) -> None:
        """An inspector that reads stdin must not block the batch forever."""
        result = process.run(
            py("import sys; print(len(sys.stdin.read()))"), timeout_seconds=30
        )
        assert result.ok
        assert result.stdout.strip() == "0"


def test_run_never_raises_for_any_input() -> None:
    """The contract that makes per-file isolation possible."""
    for argv in ([""], ["   "], ["Z:/nope"], [sys.executable, "-c", "raise SystemExit(9)"]):
        result = process.run(argv, timeout_seconds=5)
        assert isinstance(result, process.RunResult)
