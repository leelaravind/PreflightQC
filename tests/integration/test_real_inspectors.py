"""GATE-1 — the real binaries, against real media, through the shipping pipeline.

Everything else in the suite simulates the inspectors. This module does not: it runs the
bundled ffprobe and MediaInfo over files produced by a real encoder, which is the only
way to know that PreflightQC's assumptions about what those tools report are true.

The whole module skips when the binaries are absent, so the suite still runs on a machine
that has not passed GATE-1 — but a skip is never a pass, and the GATE-1 report says so.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from preflightqc.core.values import FieldState
from preflightqc.orchestration.runner import BatchRunner, CancellationToken, InspectionSettings
from preflightqc.platform import binaries
from preflightqc.platform.binaries import InspectorKind
from preflightqc.results.aggregate import FileStatus
from preflightqc.rules.loader import load_catalog

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLES = REPO_ROOT / "spikes" / "samples"
PRESETS = REPO_ROOT / "presets"

STARTUP = binaries.check_all()
_ff = STARTUP.get(InspectorKind.FFPROBE)
_mi = STARTUP.get(InspectorKind.MEDIAINFO)

pytestmark = [
    pytest.mark.requires_inspectors,
    pytest.mark.skipif(
        not (_ff and _ff.available and _mi and _mi.available and SAMPLES.is_dir()
             and any(SAMPLES.iterdir())),
        reason="real inspector binaries and sample media are required (GATE-1)",
    ),
]


@pytest.fixture(scope="module")
def catalog():
    return load_catalog([PRESETS])


@pytest.fixture(scope="module")
def runner():
    return BatchRunner(startup=STARTUP, settings=InspectionSettings(workers=4))


def sample(name: str) -> Path:
    path = SAMPLES / name
    if not path.is_file():
        pytest.skip(f"sample missing: {name}")
    return path


def media_for(runner: BatchRunner, catalog, name: str):
    preset = catalog.by_id("ig_reels")
    outcome = runner.run([sample(name)], preset)
    return outcome.results[0]


# ---------------------------------------------------------------------------
# The build itself
# ---------------------------------------------------------------------------


class TestBuildIsAcceptable:
    def test_ffprobe_is_not_gpl_or_nonfree(self) -> None:
        assert _ff is not None and _ff.configuration
        assert "--enable-gpl" not in _ff.configuration
        assert "--enable-nonfree" not in _ff.configuration

    def test_ffprobe_has_no_prohibited_component(self) -> None:
        assert _ff is not None
        assert _ff.licence_violations == ()
        assert _ff.licence_ok

    def test_ffprobe_is_a_shared_build(self) -> None:
        assert _ff is not None and _ff.configuration
        assert "--enable-shared" in _ff.configuration

    def test_the_licence_version_is_detected_and_accepted(self) -> None:
        assert _ff is not None
        assert _ff.licence in ("LGPL-2.1-or-later", "LGPL-3.0-or-later")

    def test_mediainfo_is_a_bsd_era_release(self) -> None:
        assert _mi is not None and _mi.version is not None
        major = int(_mi.version.split(".")[0])
        # 0.7.62 and earlier are GPL/LGPL. Modern releases use calendar versions (26.x).
        assert major >= 1, f"MediaInfo {_mi.version} predates the BSD-2-Clause relicence"

    def test_no_encoder_is_installed_beside_the_inspectors(self) -> None:
        """Spec 10.2 — V1 ships no FFmpeg encoder."""
        assert _ff is not None and _ff.path is not None
        bin_dir = _ff.path.parent
        for forbidden in ("ffmpeg.exe", "ffplay.exe", "libcurl.dll", "LIBCURL.DLL"):
            assert not (bin_dir / forbidden).exists(), f"{forbidden} must not ship"


# ---------------------------------------------------------------------------
# Real metadata extraction
# ---------------------------------------------------------------------------


class TestRealMetadataExtraction:
    def test_a_conformant_file_yields_the_core_fields(self, runner, catalog) -> None:
        result = media_for(runner, catalog, "01_h264_1080x1920_30_aac.mp4")
        assert result.media is not None
        media = result.media
        video, audio = media.primary_video, media.primary_audio
        assert video is not None and audio is not None

        assert media.file.size_bytes.value > 0
        assert media.file.duration_seconds.value == pytest.approx(4.0, abs=0.5)
        assert "mp4" in media.container.formats.value
        assert media.container.video_stream_count.value == 1
        assert media.container.audio_stream_count.value == 1

        assert video.codec.value == "h264"
        assert video.width.value == 1080
        assert video.height.value == 1920
        assert float(video.frame_rate.value) == pytest.approx(30.0, abs=0.01)
        assert video.chroma_subsampling.value == "4:2:0"
        assert video.bit_depth.value == 8
        assert video.pixel_format.value == "yuv420p"

        assert audio.codec.value == "aac"
        assert audio.sample_rate.value == 48000
        assert audio.channels.value == 2

    def test_displayed_aspect_ratio_is_computed_from_real_geometry(self, runner, catalog) -> None:
        result = media_for(runner, catalog, "01_h264_1080x1920_30_aac.mp4")
        video = result.media.primary_video
        assert float(video.display_aspect_ratio.value) == pytest.approx(1080 / 1920, abs=0.001)

    def test_anamorphic_sar_changes_the_displayed_ratio(self, runner, catalog) -> None:
        """A real 1440x1080 file with SAR 4:3 displays as 16:9, not 4:3."""
        result = media_for(runner, catalog, "04_anamorphic_sar43.mp4")
        video = result.media.primary_video
        assert video.width.value == 1440
        assert video.height.value == 1080
        assert float(video.sample_aspect_ratio.value) == pytest.approx(4 / 3, abs=0.01)
        assert float(video.display_aspect_ratio.value) == pytest.approx(16 / 9, abs=0.01)

    def test_a_file_with_no_audio_reports_absence_not_zero(self, runner, catalog) -> None:
        result = media_for(runner, catalog, "02_h264_no_audio.mp4")
        assert not result.media.has_audio
        assert result.media.primary_audio is None
        assert result.status is not FileStatus.FAIL

    def test_mono_44k_audio_is_read_correctly(self, runner, catalog) -> None:
        result = media_for(runner, catalog, "10_mono_44k.mp4")
        audio = result.media.primary_audio
        assert audio.channels.value == 1
        assert audio.sample_rate.value == 44100

    def test_a_webm_vp9_file_is_recognised(self, runner, catalog) -> None:
        result = media_for(runner, catalog, "05_vp9.webm")
        media = result.media
        assert media.primary_video.codec.value == "vp9"
        assert "webm" in media.container.formats.value

    def test_a_mov_container_is_recognised(self, runner, catalog) -> None:
        result = media_for(runner, catalog, "06_h264.mov")
        assert "mov" in result.media.container.formats.value

    def test_hdr_signalling_is_read_where_the_container_carries_it(self, runner, catalog) -> None:
        """10-bit BT.2020 is read. Primaries/transfer are UNDETERMINED for this file.

        That is not a defect: ffprobe genuinely reports no color_primaries or
        color_transfer for this VP9-in-WebM encode. Reporting UNDETERMINED rather than
        inventing a plausible value is exactly the required behaviour.
        """
        result = media_for(runner, catalog, "08_hdr_pq_10bit.webm")
        video = result.media.primary_video
        assert video.bit_depth.value == 10
        assert video.pixel_format.value == "yuv420p10le"
        for field in (video.colour_primaries, video.transfer_characteristics):
            assert field.state in (FieldState.KNOWN, FieldState.UNDETERMINED)
            if field.is_absent:
                assert field.reason

    def test_every_populated_field_carries_real_provenance(self, runner, catalog) -> None:
        result = media_for(runner, catalog, "01_h264_1080x1920_30_aac.mp4")
        video = result.media.primary_video
        for field in (video.codec, video.width, video.frame_rate, video.chroma_subsampling):
            assert field.provenance is not None
            assert field.provenance.inspector in {"ffprobe", "mediainfo", "computed", "filesystem"}


class TestDocumentedGapsAreHonest:
    """Register gaps G-1, G-2 must stay UNDETERMINED against real files, not be guessed."""

    def test_edit_lists_remain_undetermined(self, runner, catalog) -> None:
        result = media_for(runner, catalog, "01_h264_1080x1920_30_aac.mp4")
        assert result.media.container.edit_lists_present.is_undetermined

    def test_closed_gop_remains_undetermined(self, runner, catalog) -> None:
        result = media_for(runner, catalog, "01_h264_1080x1920_30_aac.mp4")
        assert result.media.primary_video.gop_closed.is_undetermined

    def test_fast_start_is_actually_readable(self, runner, catalog) -> None:
        """MediaInfo's IsStreamable was the reason MediaInfo is in the design at all."""
        result = media_for(runner, catalog, "01_h264_1080x1920_30_aac.mp4")
        assert result.media.container.faststart.is_known


class TestNoSpuriousConflicts:
    def test_a_clean_file_produces_no_inspector_disagreement(self, runner, catalog) -> None:
        """Spelling differences must not read as disagreement (spec 10.4)."""
        for name in (
            "01_h264_1080x1920_30_aac.mp4",
            "03_h264_1920x1080_25.mp4",
            "05_vp9.webm",
            "06_h264.mov",
            "10_mono_44k.mp4",
        ):
            result = media_for(runner, catalog, name)
            assert result.media.diagnostics.conflicts == (), (
                f"{name}: spurious conflicts {result.media.diagnostics.conflicts}"
            )


# ---------------------------------------------------------------------------
# Failure handling, with real broken files
# ---------------------------------------------------------------------------


class TestRealFailureHandling:
    @pytest.mark.parametrize(
        "name",
        ["90_truncated.mp4", "91_header_only.mp4", "92_not_media.mp4",
         "93_zero_bytes.mp4", "94_corrupt_moov.mp4"],
    )
    def test_a_broken_file_is_never_failed_for_being_broken(
        self, runner, catalog, name: str
    ) -> None:
        """Spec 23 — never FAIL *for corruption alone*.

        The precise guarantee is not "a corrupt file never fails". It is that a failure
        must rest on a property that was actually read. Spec 23 requires us to "validate
        what is known and emit UNKNOWN for the rest", so a corrupt file whose fast-start
        flag MediaInfo *positively* reports as absent may legitimately fail that rule.

        What must never happen is a FAIL resting on an UNDETERMINED or NOT_PRESENT
        value — that would mean the engine invented the evidence against the file.
        """
        from preflightqc.core.model import PROPERTY_PATHS

        result = media_for(runner, catalog, name)
        assert result.status in set(FileStatus)

        if result.media is None:
            assert result.status is FileStatus.NOT_INSPECTED
            return
        for finding in result.findings:
            if finding.severity.value != "FAIL":
                continue
            field = PROPERTY_PATHS[finding.property_path].resolve(result.media)
            assert field.is_known, (
                f"{name}: {finding.rule_id} FAILED on a {field.state.value} property — "
                "the engine must not fail a file on evidence it does not have"
            )

    def test_a_broken_file_that_is_inspected_yields_unknowns_not_invented_values(
        self, runner, catalog
    ) -> None:
        result = media_for(runner, catalog, "93_zero_bytes.mp4")
        if result.media is None:
            assert result.status is FileStatus.NOT_INSPECTED
            return
        video = result.media.primary_video
        if video is not None:
            for field in (video.codec, video.width, video.height):
                assert not field.is_known or field.value, "no fabricated value"

    def test_one_broken_file_does_not_stop_a_real_batch(self, runner, catalog) -> None:
        """The defining property, with real binaries and real corrupt input."""
        names = [
            "01_h264_1080x1920_30_aac.mp4",
            "93_zero_bytes.mp4",
            "03_h264_1920x1080_25.mp4",
            "92_not_media.mp4",
            "05_vp9.webm",
        ]
        paths = [sample(n) for n in names]
        outcome = runner.run(paths, catalog.by_id("ig_reels"))

        assert len(outcome.results) == len(paths)
        assert [r.path for r in outcome.results] == paths
        good = [r for r in outcome.results if r.media is not None]
        assert len(good) >= 3, "the healthy files must still have been inspected"

    def test_a_missing_file_is_reported_not_fatal(self, runner, catalog, tmp_path) -> None:
        outcome = runner.run([tmp_path / "does_not_exist.mp4"], catalog.by_id("ig_reels"))
        assert outcome.results[0].status is FileStatus.NOT_INSPECTED
        assert outcome.results[0].failure is not None

    def test_an_aggressive_timeout_is_enforced_against_the_real_binary(
        self, runner, catalog
    ) -> None:
        """A timeout must terminate the real inspector, not hang the batch."""
        impatient = BatchRunner(
            startup=STARTUP, settings=InspectionSettings(workers=1, timeout_seconds=0.001)
        )
        outcome = impatient.run(
            [sample("01_h264_1080x1920_30_aac.mp4")], catalog.by_id("ig_reels")
        )
        assert len(outcome.results) == 1
        # Either it beat the deadline or it was cleanly timed out; never a hang or crash.
        assert outcome.results[0].status in set(FileStatus)

    def test_cancellation_stops_a_real_batch(self, runner, catalog) -> None:
        token = CancellationToken()
        token.cancel()
        paths = [sample("01_h264_1080x1920_30_aac.mp4"), sample("03_h264_1920x1080_25.mp4")]
        outcome = runner.run(paths, catalog.by_id("ig_reels"), token=token)
        assert outcome.cancelled
        assert outcome.summary.is_partial
        assert len(outcome.results) == len(paths)


# ---------------------------------------------------------------------------
# Source integrity — the promise a QC tool must keep
# ---------------------------------------------------------------------------


class TestSourceIntegrity:
    def test_real_inspection_does_not_alter_a_single_byte(self, runner, catalog) -> None:
        """Spec AC-13, verified against the real binaries over the whole corpus."""
        files = sorted(p for p in SAMPLES.iterdir() if p.is_file())
        before = {
            p: (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size, p.stat().st_mtime_ns)
            for p in files
        }

        for preset_id in ("ig_reels", "youtube_standard", "linkedin_ctv"):
            runner.run(files, catalog.by_id(preset_id))

        after = {
            p: (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size, p.stat().st_mtime_ns)
            for p in files
        }
        assert before == after


# ---------------------------------------------------------------------------
# Every shipped preset, against real media
# ---------------------------------------------------------------------------


class TestAllPresetsAgainstRealMedia:
    def test_every_preset_completes_a_real_batch(self, runner, catalog) -> None:
        files = sorted(p for p in SAMPLES.iterdir() if p.is_file())
        for preset in catalog.presets:
            outcome = runner.run(files, preset)
            assert len(outcome.results) == len(files), preset.preset_id

    def test_no_preset_fails_a_file_on_undeterminable_metadata(self, runner, catalog) -> None:
        """Claim C2, end to end with real binaries.

        Every FAIL must cite a rule whose property was actually KNOWN. A failure resting
        on an absent value would mean the engine invented the evidence for it.
        """
        broken = [sample(n) for n in ("93_zero_bytes.mp4", "92_not_media.mp4", "91_header_only.mp4")]
        for preset in catalog.presets:
            outcome = runner.run(broken, preset)
            for result in outcome.results:
                for finding in result.findings:
                    if finding.severity.value == "FAIL":
                        assert result.media is not None
                        field = __import__(
                            "preflightqc.core.model", fromlist=["PROPERTY_PATHS"]
                        ).PROPERTY_PATHS[finding.property_path].resolve(result.media)
                        assert field.is_known, (
                            f"{preset.preset_id}:{finding.rule_id} FAILED on a "
                            f"{field.state.value} property"
                        )
