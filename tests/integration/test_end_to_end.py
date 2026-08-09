"""Phase 10 — end-to-end integration through the real pipeline.

These tests drive enumerate → inspect → normalise → validate → aggregate → report with
the shipped presets, substituting only the two external binaries. Everything else is the
code that ships.
"""

from __future__ import annotations

import hashlib
import socket
from datetime import UTC, datetime
from pathlib import Path

import pytest

from factories import ffprobe_payload, mediainfo_payload
from preflightqc.adapters import ffprobe as ffprobe_adapter
from preflightqc.adapters import mediainfo as mediainfo_adapter
from preflightqc.adapters.base import FailureKind, InspectorFailure, InspectorSuccess
from preflightqc.orchestration.runner import BatchRunner, InspectionSettings
from preflightqc.platform.binaries import InspectorInfo, InspectorKind, StartupReport
from preflightqc.reporting import claims, csv_writer, html_renderer
from preflightqc.reporting.export import ExportFormat, export
from preflightqc.reporting.model import build_report
from preflightqc.results.aggregate import FileStatus
from preflightqc.rules.loader import load_catalog
from preflightqc.scan.enumerate import EnumerationOptions, enumerate_inputs

PRESETS_DIR = Path(__file__).resolve().parent.parent.parent / "presets"
CATALOG = load_catalog([PRESETS_DIR])

STARTUP = StartupReport(
    inspectors=(
        InspectorInfo(InspectorKind.FFPROBE, Path("C:/bin/ffprobe.exe"), "7.1", True),
        InspectorInfo(InspectorKind.MEDIAINFO, Path("C:/bin/mediainfo.exe"), "26.05", True),
    )
)

#: A conformant Instagram Reels deliverable.
GOOD_VIDEO = {"width": 1080, "height": 1920, "avg_frame_rate": "30/1", "bit_rate": "8000000"}
#: The same file re-exported at 4K, which exceeds the documented 1920-pixel ceiling.
BAD_VIDEO = {"width": 2160, "height": 3840, "avg_frame_rate": "30/1", "bit_rate": "40000000"}


@pytest.fixture
def scenario(tmp_path: Path, monkeypatch):
    """A realistic mixed batch: a good file, a bad file, and a corrupt one."""
    good = tmp_path / "hero_cut_v3.mp4"
    bad = tmp_path / "hero_cut_4k.mp4"
    corrupt = tmp_path / "truncated.mp4"
    # Real files, deliberately small. File size is read from the filesystem as ground
    # truth, and faking stat to inflate it breaks path traversal for no benefit: the
    # bad file is meant to fail on dimensions and bitrate, not on size.
    for path in (good, bad, corrupt):
        path.write_bytes(b"\x00" * 4096)

    def ff(path: Path):
        if path == corrupt:
            return InspectorFailure(FailureKind.FILE_UNREADABLE, "Invalid data found")
        video = GOOD_VIDEO if path == good else BAD_VIDEO
        return InspectorSuccess(
            raw=ffprobe_payload(video=video, audio={}, duration="28.500000")
        )

    def mi(path: Path):
        if path == corrupt:
            return InspectorFailure(FailureKind.FILE_UNREADABLE, "Unable to load")
        # MediaInfo must describe the *same* file as ffprobe. If the two stubs disagree,
        # the field becomes CONFLICTED and severity is correctly capped at WARN — which
        # is right behaviour but would make this fixture test the conflict path instead
        # of the rule path it is aiming at.
        source = GOOD_VIDEO if path == good else BAD_VIDEO
        return InspectorSuccess(
            raw=mediainfo_payload(
                video={
                    "Width": str(source["width"]),
                    "Height": str(source["height"]),
                    "BitRate": source["bit_rate"],
                },
                audio={},
                duration="28.500",
            )
        )

    monkeypatch.setattr(ffprobe_adapter, "inspect", lambda b, p, **k: ff(p))
    monkeypatch.setattr(mediainfo_adapter, "inspect", lambda b, p, **k: mi(p))
    return tmp_path, good, bad, corrupt


class TestFullCycle:
    def test_a_mixed_batch_produces_the_expected_statuses(self, scenario) -> None:
        """The core promise: three files, three different honest outcomes."""
        folder, good, bad, corrupt = scenario
        preset = CATALOG.by_id("ig_reels")

        found = enumerate_inputs([folder], options=EnumerationOptions(recurse=True))
        assert len(found.files) == 3

        outcome = BatchRunner(startup=STARTUP).run(found.files, preset)
        by_name = {r.display_name: r for r in outcome.results}

        assert by_name["hero_cut_v3.mp4"].status in (FileStatus.PASS, FileStatus.WARN)
        assert by_name["hero_cut_4k.mp4"].status is FileStatus.FAIL
        assert by_name["truncated.mp4"].status is FileStatus.NOT_INSPECTED

        # The corrupt file must not inflate the failure count the user acts on.
        assert outcome.summary.failed == 1
        assert outcome.summary.not_inspected == 1

    def test_the_failing_file_names_the_rule_and_its_source(self, scenario) -> None:
        folder, good, bad, corrupt = scenario
        preset = CATALOG.by_id("ig_reels")
        outcome = BatchRunner(startup=STARTUP).run([bad], preset)
        failures = [f for f in outcome.results[0].findings if f.severity.value == "FAIL"]
        assert failures
        width_failure = next(f for f in failures if "width" in f.rule_id)
        assert "2160" in width_failure.detected
        assert "1920" in width_failure.expected
        assert width_failure.source.url.startswith("https://developers.facebook.com")
        assert width_failure.source.access_date == "2026-08-09"

    def test_the_full_cycle_exports_both_formats(self, scenario, tmp_path: Path) -> None:
        folder, good, bad, corrupt = scenario
        preset = CATALOG.by_id("ig_reels")
        found = enumerate_inputs([folder], options=EnumerationOptions(recurse=True))
        outcome = BatchRunner(startup=STARTUP).run(found.files, preset)

        report = build_report(
            results=outcome.results,
            summary=outcome.summary,
            preset=preset,
            product_version="0.1.0-dev",
            scan_started=datetime(2026, 8, 9, 12, 0, tzinfo=UTC),
            scan_finished=datetime(2026, 8, 9, 12, 1, tzinfo=UTC),
            inspector_versions=STARTUP.versions(),
        )
        out = tmp_path / "out"
        out.mkdir()
        for fmt, name in ((ExportFormat.CSV, "r.csv"), (ExportFormat.HTML, "r.html")):
            result = export(report, out / name, fmt)
            assert result.ok, result.error

        html = (out / "r.html").read_text(encoding="utf-8")
        assert claims.APPROVED_CLAIM in html
        assert claims.contains_forbidden_claim(html) == ()
        assert html_renderer.find_external_references(html) == ()

        csv_bytes = (out / "r.csv").read_bytes()
        assert csv_bytes.startswith(b"\xef\xbb\xbf")
        csv_text = csv_bytes.decode("utf-8-sig")
        assert "hero_cut_4k.mp4" in csv_text
        assert "truncated.mp4" in csv_text

    @pytest.mark.parametrize("preset_id", [p.preset_id for p in CATALOG.presets])
    def test_every_shipped_preset_runs_end_to_end(self, scenario, preset_id: str) -> None:
        """A preset that cannot complete a batch is not shippable."""
        folder, good, bad, corrupt = scenario
        preset = CATALOG.by_id(preset_id)
        outcome = BatchRunner(startup=STARTUP).run([good, bad, corrupt], preset)
        assert len(outcome.results) == 3
        assert all(r.status in set(FileStatus) for r in outcome.results)


class TestSafety:
    def test_no_network_connection_is_attempted(self, scenario, monkeypatch) -> None:
        """Spec AC-12 — the whole cycle must work with the network blocked."""
        folder, good, bad, corrupt = scenario

        def forbidden(*args, **kwargs):
            raise AssertionError("PreflightQC must not touch the network")

        monkeypatch.setattr(socket, "create_connection", forbidden)
        monkeypatch.setattr(socket.socket, "connect", forbidden)
        monkeypatch.setattr(socket.socket, "connect_ex", forbidden)

        preset = CATALOG.by_id("ig_reels")
        found = enumerate_inputs([folder], options=EnumerationOptions(recurse=True))
        outcome = BatchRunner(startup=STARTUP).run(found.files, preset)
        report = build_report(
            results=outcome.results,
            summary=outcome.summary,
            preset=preset,
            product_version="0.1.0-dev",
            scan_started=datetime(2026, 8, 9, 12, 0, tzinfo=UTC),
            scan_finished=datetime(2026, 8, 9, 12, 1, tzinfo=UTC),
            inspector_versions={},
        )
        assert html_renderer.render(report)
        assert csv_writer.render_findings(report)

    def test_no_source_file_is_modified(self, scenario) -> None:
        """Spec AC-13 — the promise a QC tool absolutely must keep."""
        folder, good, bad, corrupt = scenario
        files = [good, bad, corrupt]
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

        preset = CATALOG.by_id("ig_reels")
        BatchRunner(startup=STARTUP).run(files, preset)

        after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        assert before == after

    def test_no_source_file_is_opened_for_writing(self, scenario, monkeypatch) -> None:
        folder, good, bad, corrupt = scenario
        sources = {str(good), str(bad), str(corrupt)}
        real_open = Path.open

        def guarded(self, mode="r", *args, **kwargs):
            if str(self) in sources and any(flag in mode for flag in ("w", "a", "+", "x")):
                raise AssertionError(f"source file opened for writing: {self}")
            return real_open(self, mode, *args, **kwargs)

        monkeypatch.setattr(Path, "open", guarded)
        BatchRunner(startup=STARTUP).run([good, bad, corrupt], CATALOG.by_id("ig_reels"))


class TestScaleAndRobustness:
    def test_a_large_batch_completes_without_orphans(self, tmp_path: Path, monkeypatch) -> None:
        """P10-A4 — soak, at a size a real agency batch reaches."""
        files = []
        for i in range(250):
            path = tmp_path / f"clip_{i:04d}.mp4"
            path.write_bytes(b"\x00" * 512)
            files.append(path)

        monkeypatch.setattr(
            ffprobe_adapter,
            "inspect",
            lambda b, p, **k: InspectorSuccess(raw=ffprobe_payload(video={}, audio={})),
        )
        monkeypatch.setattr(
            mediainfo_adapter,
            "inspect",
            lambda b, p, **k: InspectorSuccess(raw=mediainfo_payload(video={}, audio={})),
        )

        outcome = BatchRunner(
            startup=STARTUP, settings=InspectionSettings(workers=8)
        ).run(files, CATALOG.by_id("ig_reels"))
        assert len(outcome.results) == 250
        assert [r.path for r in outcome.results] == files

    @pytest.mark.parametrize(
        "name",
        [
            "clip with spaces.mp4",
            "clip'quote.mp4",
            "clip&ampersand.mp4",
            "clip;semicolon.mp4",
            "clip%percent.mp4",
            "naïve_日本語_clip.mp4",
        ],
    )
    def test_hostile_filenames_are_handled(self, tmp_path: Path, monkeypatch, name: str) -> None:
        """P10-A3 — a filename is data, never syntax."""
        path = tmp_path / name
        path.write_bytes(b"\x00" * 512)
        monkeypatch.setattr(
            ffprobe_adapter,
            "inspect",
            lambda b, p, **k: InspectorSuccess(raw=ffprobe_payload(video={}, audio={})),
        )
        monkeypatch.setattr(
            mediainfo_adapter,
            "inspect",
            lambda b, p, **k: InspectorSuccess(raw=mediainfo_payload(video={}, audio={})),
        )
        outcome = BatchRunner(startup=STARTUP).run([path], CATALOG.by_id("ig_reels"))
        assert outcome.results[0].display_name == name

    def test_a_deeply_nested_folder_enumerates(self, tmp_path: Path) -> None:
        deep = tmp_path
        for level in range(12):
            deep = deep / f"level_{level}"
        deep.mkdir(parents=True)
        (deep / "buried.mp4").write_bytes(b"\x00" * 128)

        found = enumerate_inputs([tmp_path], options=EnumerationOptions(recurse=True))
        assert [p.name for p in found.files] == ["buried.mp4"]

    def test_recurse_off_stays_at_one_level(self, tmp_path: Path) -> None:
        (tmp_path / "top.mp4").write_bytes(b"\x00")
        nested = tmp_path / "sub"
        nested.mkdir()
        (nested / "deep.mp4").write_bytes(b"\x00")

        found = enumerate_inputs([tmp_path], options=EnumerationOptions(recurse=False))
        assert [p.name for p in found.files] == ["top.mp4"]

    def test_duplicates_are_enqueued_once(self, tmp_path: Path) -> None:
        path = tmp_path / "clip.mp4"
        path.write_bytes(b"\x00")
        found = enumerate_inputs([path, path, tmp_path])
        assert len(found.files) == 1
        assert found.skipped_duplicates >= 1

    def test_a_nonexistent_path_is_reported_not_raised(self, tmp_path: Path) -> None:
        found = enumerate_inputs([tmp_path / "nope"])
        assert found.files == []
        assert found.unreadable
