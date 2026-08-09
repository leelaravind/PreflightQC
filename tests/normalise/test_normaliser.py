"""Phase 2 — normalisation from raw inspector output (P2-A1..A9)."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

from factories import build_media, default_media, ffprobe_payload, mediainfo_payload
from preflightqc.core.model import PROPERTY_PATHS


class TestHappyPath:
    def test_a_conformant_file_normalises_completely(self) -> None:
        media = default_media()
        video = media.primary_video
        audio = media.primary_audio
        assert video is not None and audio is not None

        assert video.codec.value == "h264"
        assert video.width.value == 1080
        assert video.height.value == 1920
        assert video.frame_rate.value == Fraction(30)
        assert video.chroma_subsampling.value == "4:2:0"
        assert video.bit_depth.value == 8
        assert audio.codec.value == "aac"
        assert audio.sample_rate.value == 48000
        assert audio.channels.value == 2

    def test_container_family_is_a_set(self) -> None:
        media = default_media()
        assert "mp4" in media.container.formats.value

    def test_every_populated_field_carries_provenance(self) -> None:
        """P2-A8."""
        media = default_media()
        video = media.primary_video
        assert video is not None
        for field in (video.codec, video.width, video.frame_rate):
            assert field.provenance is not None
            assert field.provenance.inspector in {"ffprobe", "mediainfo", "computed", "filesystem"}
            assert field.provenance.field_path


class TestAbsence:
    def test_absent_bitrate_is_not_present_never_zero(self) -> None:
        """P2-A2 — the headline guarantee."""
        ff = ffprobe_payload(video={"bit_rate": None}, bit_rate=None)
        media = build_media(ffprobe=ff)
        video = media.primary_video
        assert video is not None
        assert not video.bitrate.is_known
        assert video.bitrate.or_none() != 0

    def test_unknown_field_order_becomes_undetermined_not_missing(self) -> None:
        """P2-A3 — register gap G-3."""
        ff = ffprobe_payload(video={"field_order": "unknown"})
        media = build_media(ffprobe=ff)
        video = media.primary_video
        assert video is not None
        assert video.scan_type.is_undetermined
        assert "heuristic" in (video.scan_type.reason or "")

    def test_unmapped_pixel_format_retains_the_raw_value(self) -> None:
        """P2-A9 — no silent default to 4:2:0."""
        ff = ffprobe_payload(video={"pix_fmt": "yuv420p16xx"})
        media = build_media(ffprobe=ff)
        video = media.primary_video
        assert video is not None
        assert video.chroma_subsampling.is_undetermined
        assert video.chroma_subsampling.raw == "yuv420p16xx"

    def test_missing_colour_description_is_undetermined_with_a_clear_reason(self) -> None:
        ff = ffprobe_payload(
            video={"color_primaries": "unknown", "color_transfer": "unknown", "color_space": "unknown"}
        )
        media = build_media(ffprobe=ff)
        video = media.primary_video
        assert video is not None
        assert video.colour_primaries.is_undetermined
        assert "colour description" in (video.colour_primaries.reason or "")

    def test_a_file_with_no_audio_has_no_audio_streams(self) -> None:
        media = build_media(ffprobe=ffprobe_payload(video={}))
        assert not media.has_audio
        assert media.primary_audio is None

    def test_documented_gaps_are_undetermined_not_guessed(self) -> None:
        """Register gaps G-1 (edit lists) and G-2 (closed GOP)."""
        media = default_media()
        video = media.primary_video
        assert video is not None
        assert media.container.edit_lists_present.is_undetermined
        assert video.gop_closed.is_undetermined
        assert "not determined by PreflightQC V1" in (
            media.container.edit_lists_present.reason or ""
        )


class TestDerivedGeometry:
    def test_display_aspect_ratio_is_computed_and_flagged_derived(self) -> None:
        """P2-A5."""
        media = default_media()
        video = media.primary_video
        assert video is not None
        assert video.display_aspect_ratio.value == Fraction(9, 16)
        provenance = video.display_aspect_ratio.provenance
        assert provenance is not None and provenance.is_derived

    def test_anamorphic_sar_changes_the_display_ratio(self) -> None:
        ff = ffprobe_payload(video={"width": 1440, "height": 1080, "sample_aspect_ratio": "4:3"})
        media = build_media(ffprobe=ff)
        video = media.primary_video
        assert video is not None
        assert video.display_aspect_ratio.value == Fraction(16, 9)

    def test_rotation_metadata_swaps_displayed_dimensions(self) -> None:
        """P2-A6."""
        ff = ffprobe_payload(
            video={
                "width": 1920,
                "height": 1080,
                "side_data_list": [{"side_data_type": "Display Matrix", "rotation": -90}],
            }
        )
        media = build_media(ffprobe=ff)
        video = media.primary_video
        assert video is not None
        assert video.rotation_degrees.value == 90
        assert video.display_width.value == 1080
        assert video.display_height.value == 1920

    def test_absent_rotation_metadata_means_no_rotation(self) -> None:
        media = default_media()
        video = media.primary_video
        assert video is not None
        assert video.rotation_degrees.value == 0


class TestConflicts:
    def test_substantive_disagreement_is_preserved(self) -> None:
        """P2-A7 — both values kept, neither silently chosen."""
        ff = ffprobe_payload(video={"width": 1080})
        mi = mediainfo_payload(video={"Width": "1440"})
        media = build_media(ffprobe=ff, mediainfo=mi)
        video = media.primary_video
        assert video is not None
        assert video.width.is_conflicted
        assert set(video.width.conflict_values()) == {1080, 1440}
        assert any(c.property_path == "video.width" for c in media.diagnostics.conflicts)

    def test_trivial_numeric_rounding_is_not_treated_as_disagreement(self) -> None:
        """Rounding noise must not cap a legitimate FAIL rule at WARN."""
        ff = ffprobe_payload(duration="30.000000")
        mi = mediainfo_payload(duration="30.001")
        media = build_media(ffprobe=ff, mediainfo=mi)
        assert media.file.duration_seconds.is_known

    def test_categorical_disagreement_is_a_conflict(self) -> None:
        ff = ffprobe_payload(video={"field_order": "progressive"})
        mi = mediainfo_payload(video={"ScanType": "Interlaced"})
        media = build_media(ffprobe=ff, mediainfo=mi)
        video = media.primary_video
        assert video is not None
        assert video.scan_type.is_conflicted


class TestPrecedence:
    def test_mediainfo_wins_scan_type(self) -> None:
        ff = ffprobe_payload(video={"field_order": "unknown"})
        mi = mediainfo_payload(video={"ScanType": "Progressive"})
        media = build_media(ffprobe=ff, mediainfo=mi)
        video = media.primary_video
        assert video is not None
        assert video.scan_type.value == "progressive"
        assert video.scan_type.provenance is not None
        assert video.scan_type.provenance.inspector == "mediainfo"

    def test_faststart_comes_only_from_mediainfo(self) -> None:
        media = build_media(ffprobe=ffprobe_payload(video={}), mediainfo=mediainfo_payload(video={}))
        assert media.container.faststart.value is True

    def test_faststart_is_undetermined_without_mediainfo(self) -> None:
        """When MediaInfo is unavailable the answer is honestly unknown, not assumed."""
        media = build_media(ffprobe=ffprobe_payload(video={}))
        assert media.container.faststart.is_undetermined


class TestDegradedInspection:
    def test_ffprobe_alone_still_produces_a_usable_model(self) -> None:
        """Spec 23 — a MediaInfo crash degrades detail, it does not stop validation."""
        media = build_media(ffprobe=ffprobe_payload(video={}, audio={}))
        video = media.primary_video
        assert video is not None
        assert video.codec.value == "h264"
        assert video.frame_rate_mode.is_undetermined

    def test_mediainfo_alone_still_produces_a_usable_model(self) -> None:
        media = build_media(mediainfo=mediainfo_payload(video={}, audio={}))
        video = media.primary_video
        assert video is not None
        assert video.codec.value == "h264"

    def test_neither_inspector_yields_an_all_absent_model_not_a_crash(self) -> None:
        media = build_media(size_bytes=1234)
        assert media.video == ()
        assert media.audio == ()
        assert media.file.size_bytes.value == 1234


class TestMultipleStreams:
    def test_multiple_video_streams_are_enumerated_with_a_note(self) -> None:
        """Spec 23 — stream 0 is primary and the user is told."""
        extra = {
            "index": 2,
            "codec_type": "video",
            "codec_name": "h264",
            "width": 640,
            "height": 480,
            "pix_fmt": "yuv420p",
            "avg_frame_rate": "25/1",
        }
        ff = ffprobe_payload(video={}, audio={}, extra_streams=[extra])
        media = build_media(ffprobe=ff)
        assert len(media.video) == 2
        assert media.primary_video is media.video[0]
        assert any("video streams" in note for note in media.diagnostics.notes)

    def test_attached_cover_art_is_not_counted_as_a_video_stream(self) -> None:
        """A music file with artwork must not look like a two-stream video."""
        art = {
            "index": 2,
            "codec_type": "video",
            "codec_name": "mjpeg",
            "disposition": {"attached_pic": 1},
        }
        ff = ffprobe_payload(video={}, audio={}, extra_streams=[art])
        media = build_media(ffprobe=ff)
        assert len(media.video) == 1
        assert not any("video streams" in note for note in media.diagnostics.notes)


def test_every_registered_property_path_resolves_against_a_real_model() -> None:
    """P2-A1 — the registry and the model cannot drift apart."""
    media = default_media()
    for path, descriptor in PROPERTY_PATHS.items():
        field = descriptor.resolve(media)
        assert field is not None, path
        assert descriptor.label, path


def test_every_registered_path_resolves_even_with_no_streams() -> None:
    """A stream-less file must yield UNDETERMINED, never an exception."""
    media = build_media(size_bytes=10)
    for path, descriptor in PROPERTY_PATHS.items():
        field = descriptor.resolve(media)
        assert field is not None, path


def test_filesystem_size_is_ground_truth() -> None:
    media = build_media(ffprobe=ffprobe_payload(size="999"), size_bytes=123456)
    assert media.file.size_bytes.value == 123456
    provenance = media.file.size_bytes.provenance
    assert provenance is not None and provenance.inspector == "filesystem"


def test_bitrate_records_where_it_came_from() -> None:
    """Reports must not imply a measured value that was actually derived."""
    ff = ffprobe_payload(video={"bit_rate": None}, bit_rate="3000000")
    media = build_media(ffprobe=ff)
    video = media.primary_video
    assert video is not None
    assert video.bitrate.value == 3_000_000
    assert video.bitrate_source.value == "container"


def test_path_and_name_are_carried_through() -> None:
    media = build_media(path=Path("D:/deliverables/hero_cut_v3.mp4"), ffprobe=ffprobe_payload(video={}))
    assert media.file.name == "hero_cut_v3.mp4"
