"""Phase 2 — canonicalisation tables (P2-A9).

The governing property under test: **an unmapped input is never coerced.** A silent
default here would manufacture the evidence for a FAIL that the file never carried.
"""

from __future__ import annotations

import pytest

from preflightqc.core import vocabulary as vocab


class TestContainers:
    def test_ffprobe_format_family_maps_to_a_set(self) -> None:
        """ffprobe reports a family, so membership is intersection, not equality."""
        tokens = vocab.canonical_containers("mov,mp4,m4a,3gp,3g2,mj2")
        assert "mp4" in tokens
        assert "mov" in tokens
        assert "3gp" in tokens

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("matroska,webm", {"mkv", "webm"}), ("avi", {"avi"}), ("asf", {"asf"})],
    )
    def test_common_containers_canonicalise(self, raw: str, expected: set[str]) -> None:
        assert expected.issubset(vocab.canonical_containers(raw))

    def test_unmapped_container_yields_an_empty_set_not_a_guess(self) -> None:
        assert vocab.canonical_containers("totally_made_up_format") == frozenset()


class TestCodecs:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("h264", "h264"), ("avc1", "h264"), ("H.264", "h264"), ("hevc", "hevc"), ("hvc1", "hevc"),
         ("vp9", "vp9"), ("av01", "av1"), ("apch", "prores")],
    )
    def test_video_codec_aliases_converge(self, raw: str, expected: str) -> None:
        assert vocab.canonical_video_codec(raw) == expected

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("aac", "aac"), ("mp4a-40-2", "aac"), ("opus", "opus"), ("pcm_s24le", "pcm")],
    )
    def test_audio_codec_aliases_converge(self, raw: str, expected: str) -> None:
        assert vocab.canonical_audio_codec(raw) == expected

    def test_unmapped_codec_returns_none(self) -> None:
        assert vocab.canonical_video_codec("nonexistent_codec") is None
        assert vocab.canonical_audio_codec("nonexistent_codec") is None


class TestPixelFormats:
    @pytest.mark.parametrize(
        ("raw", "chroma", "depth"),
        [
            ("yuv420p", "4:2:0", 8),
            ("yuv420p10le", "4:2:0", 10),
            ("yuv422p10le", "4:2:2", 10),
            ("yuv444p", "4:4:4", 8),
            ("p010le", "4:2:0", 10),
        ],
    )
    def test_pixel_format_yields_chroma_and_depth(self, raw: str, chroma: str, depth: int) -> None:
        facts = vocab.pixel_format_facts(raw)
        assert facts is not None
        assert facts.chroma_subsampling == chroma
        assert facts.bit_depth == depth

    def test_unmapped_pixel_format_does_not_default_to_420(self) -> None:
        """The defect this prevents: assuming 4:2:0 and then FAILing a chroma rule."""
        assert vocab.pixel_format_facts("yuv420p16xx") is None


class TestScanType:
    @pytest.mark.parametrize("raw", ["progressive", "Progressive", "prog"])
    def test_progressive_variants(self, raw: str) -> None:
        assert vocab.canonical_scan_type(raw) == "progressive"

    @pytest.mark.parametrize("raw", ["tt", "bb", "interlaced", "MBAFF", "Top Field First"])
    def test_interlaced_variants(self, raw: str) -> None:
        assert vocab.canonical_scan_type(raw) == "interlaced"

    @pytest.mark.parametrize("raw", ["unknown", "unspecified", "", "n/a"])
    def test_explicit_unknown_tokens_map_to_none(self, raw: str) -> None:
        """ffprobe frequently reports 'unknown' here (register gap G-3)."""
        assert vocab.canonical_scan_type(raw) is None


class TestColour:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("smpte2084", "pq"), ("arib-std-b67", "hlg"), ("bt709", "bt709")],
    )
    def test_transfer_characteristics(self, raw: str, expected: str) -> None:
        assert vocab.canonical_transfer(raw) == expected

    def test_hdr_transfers_are_exactly_pq_and_hlg(self) -> None:
        """These guard the conditional HDR rules; widening the set would fire them on SDR."""
        assert frozenset({"pq", "hlg"}) == vocab.HDR_TRANSFERS

    @pytest.mark.parametrize("raw", ["unknown", "unspecified", "reserved", "", "n/a"])
    def test_absent_colour_description_is_recognised(self, raw: str) -> None:
        assert vocab.is_colour_absent(raw)

    def test_colour_range_normalises_both_vocabularies(self) -> None:
        assert vocab.canonical_colour_range("tv") == "limited"
        assert vocab.canonical_colour_range("Limited") == "limited"
        assert vocab.canonical_colour_range("pc") == "full"


class TestFrameRateMode:
    @pytest.mark.parametrize(("raw", "expected"), [("CFR", "CFR"), ("VFR", "VFR"), ("Constant", "CFR")])
    def test_modes_canonicalise(self, raw: str, expected: str) -> None:
        assert vocab.canonical_frame_rate_mode(raw) == expected

    def test_unmapped_mode_returns_none(self) -> None:
        assert vocab.canonical_frame_rate_mode("sometimes") is None
