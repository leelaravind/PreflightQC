"""Gate G-5 — the archived FFmpeg source must correspond to the binary we ship.

The failure this guards against is not "we forgot the source". It is the near miss: an
8.1.1 tarball sitting next to an 8.1.2 binary, which passes every eyeball check and
satisfies no LGPL obligation at all.

So the tests that matter here are the negative ones. A verifier that only ever says yes
is worse than no verifier, because it launders an unchecked claim into a green tick.
"""

from __future__ import annotations

import gzip
import io
import json
import tarfile
from pathlib import Path

import pytest
import verify_source
from verify_source import (
    BinaryIdentity,
    SourceIdentity,
    compare,
    parse_binary_identity,
    parse_source_identity,
    verify,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOCK_FILE = REPO_ROOT / "packaging" / "binaries.lock.json"

#: Verbatim output of the shipped ffprobe, trimmed to the lines the verifier reads.
REAL_VERSION_OUTPUT = """\
ffprobe version n8.1.2-34-g9b6c8969e0-20260809 Copyright (c) 2007-2026 the FFmpeg developers
built with gcc 15.2.0 (crosstool-NG 1.28.0.23_185f348)
configuration: --enable-version3 --disable-debug --enable-shared
libavutil      60. 26.102 / 60. 26.102
libavcodec     62. 28.102 / 62. 28.102
libavformat    62. 12.102 / 62. 12.102
libavdevice    62.  3.102 / 62.  3.102
libavfilter    11. 14.102 / 11. 14.102
libswscale      9.  5.102 /  9.  5.102
libswresample   6.  3.102 /  6.  3.102
"""

REAL_LIBRARIES: dict[str, tuple[int, int, int]] = {
    "libavutil": (60, 26, 102),
    "libavcodec": (62, 28, 102),
    "libavformat": (62, 12, 102),
    "libavdevice": (62, 3, 102),
    "libavfilter": (11, 14, 102),
    "libswscale": (9, 5, 102),
    "libswresample": (6, 3, 102),
}


def build_source_archive(
    path: Path,
    *,
    release: str = "8.1.2",
    libraries: dict[str, tuple[int, int, int]] | None = None,
    prefix: str = "ffmpeg-test",
) -> Path:
    """Write a miniature FFmpeg source tree in the shape the verifier reads."""
    libraries = REAL_LIBRARIES if libraries is None else libraries
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as archive:

        def add(name: str, text: str) -> None:
            payload = text.encode("utf-8")
            info = tarfile.TarInfo(f"{prefix}/{name}")
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))

        add("RELEASE", f"{release}\n")
        for library, (major, minor, micro) in libraries.items():
            symbol = library.upper()
            add(
                f"{library}/version.h",
                f"#define {symbol}_VERSION_MAJOR {major}\n"
                f"#define {symbol}_VERSION_MINOR {minor}\n"
                f"#define {symbol}_VERSION_MICRO {micro}\n"
                f"#define FF_API_SOMETHING ({symbol}_VERSION_MAJOR < 99)\n",
            )
    path.write_bytes(gzip.compress(raw.getvalue()))
    return path


class TestParsingTheBinarySelfReport:
    def test_the_real_version_string_is_decomposed(self) -> None:
        identity = parse_binary_identity(REAL_VERSION_OUTPUT)
        assert identity.version == "n8.1.2-34-g9b6c8969e0-20260809"
        assert identity.release == "8.1.2"
        assert identity.commits_ahead == 34
        assert identity.commit == "9b6c8969e0"

    def test_all_seven_library_versions_are_read(self) -> None:
        assert parse_binary_identity(REAL_VERSION_OUTPUT).libraries == REAL_LIBRARIES

    def test_a_build_made_exactly_on_a_release_tag_parses(self) -> None:
        identity = parse_binary_identity("ffprobe version n8.1.2 Copyright (c) 2007-2026\n")
        assert identity.release == "8.1.2"
        assert identity.commits_ahead is None
        assert identity.commit is None

    @pytest.mark.parametrize(
        "text",
        [
            "",
            "some other program version 1.0\n",
            "ffprobe version 2024-custom-build Copyright\n",
        ],
    )
    def test_an_unparseable_version_raises_rather_than_degrading(self, text: str) -> None:
        """Silently returning 'unknown' would let the gate pass on an unidentified build."""
        with pytest.raises(ValueError, match="version|ffprobe"):
            parse_binary_identity(text)


class TestParsingTheSourceArchive:
    def test_release_and_library_versions_are_read(self, tmp_path: Path) -> None:
        archive = build_source_archive(tmp_path / "src.tar.gz")
        source = parse_source_identity(archive)
        assert source.release == "8.1.2"
        assert source.libraries == REAL_LIBRARIES

    def test_a_major_defined_in_version_major_h_is_still_found(self, tmp_path: Path) -> None:
        """libavcodec and friends moved VERSION_MAJOR into a separate header."""
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode="w") as archive:

            def add(name: str, text: str) -> None:
                payload = text.encode("utf-8")
                info = tarfile.TarInfo(f"ffmpeg/{name}")
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))

            add("RELEASE", "8.1.2\n")
            add("libavcodec/version_major.h", "#define LIBAVCODEC_VERSION_MAJOR 62\n")
            add(
                "libavcodec/version.h",
                "#define LIBAVCODEC_VERSION_MINOR 28\n#define LIBAVCODEC_VERSION_MICRO 102\n",
            )
        path = tmp_path / "split.tar.gz"
        path.write_bytes(gzip.compress(raw.getvalue()))
        assert parse_source_identity(path).libraries["libavcodec"] == (62, 28, 102)

    def test_an_archive_without_a_release_file_raises(self, tmp_path: Path) -> None:
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode="w") as archive:
            info = tarfile.TarInfo("ffmpeg/README.md")
            info.size = 0
            archive.addfile(info, io.BytesIO(b""))
        path = tmp_path / "empty.tar.gz"
        path.write_bytes(gzip.compress(raw.getvalue()))
        with pytest.raises(ValueError, match="RELEASE"):
            parse_source_identity(path)


class TestMismatchesAreCaught:
    """The whole point. Each of these would otherwise ship as 'source provided'."""

    def test_matching_source_and_binary_produce_no_problems(self) -> None:
        binary = parse_binary_identity(REAL_VERSION_OUTPUT)
        source = SourceIdentity(release="8.1.2", libraries=dict(REAL_LIBRARIES))
        assert compare(binary, source) == []

    def test_a_one_patch_release_difference_is_caught(self) -> None:
        binary = parse_binary_identity(REAL_VERSION_OUTPUT)
        source = SourceIdentity(release="8.1.1", libraries=dict(REAL_LIBRARIES))
        problems = compare(binary, source)
        assert any("release mismatch" in str(p) for p in problems)

    def test_a_single_library_micro_difference_is_caught(self) -> None:
        """Micro 100 vs 102 distinguishes a Libav-era build from an FFmpeg one."""
        libraries = dict(REAL_LIBRARIES)
        libraries["libavcodec"] = (62, 28, 100)
        problems = compare(
            parse_binary_identity(REAL_VERSION_OUTPUT),
            SourceIdentity(release="8.1.2", libraries=libraries),
        )
        assert any("libavcodec mismatch" in str(p) for p in problems)

    def test_a_source_tree_missing_a_library_is_caught(self) -> None:
        libraries = dict(REAL_LIBRARIES)
        del libraries["libswresample"]
        problems = compare(
            parse_binary_identity(REAL_VERSION_OUTPUT),
            SourceIdentity(release="8.1.2", libraries=libraries),
        )
        assert any("libswresample" in str(p) for p in problems)

    def test_a_binary_reporting_no_libraries_is_caught(self) -> None:
        binary = BinaryIdentity(
            version="n8.1.2", release="8.1.2", commits_ahead=None, commit=None, libraries={}
        )
        problems = compare(binary, SourceIdentity(release="8.1.2", libraries=dict(REAL_LIBRARIES)))
        assert any("no library versions" in str(p) for p in problems)


class TestTheFullVerification:
    def test_a_missing_archive_fails_loudly(self, tmp_path: Path) -> None:
        problems = verify(archive=tmp_path / "absent.tar.gz", version_output=REAL_VERSION_OUTPUT)
        assert len(problems) == 1
        assert "missing" in str(problems[0])

    def test_a_wrong_hash_in_the_lock_file_fails(self, tmp_path: Path) -> None:
        archive = build_source_archive(tmp_path / "src.tar.gz")
        lock = {
            "components": [
                {
                    "name": "ffprobe",
                    "corresponding_source": {
                        "archive_sha256": "0" * 64,
                        "commit": "9b6c8969e05b4f0b29f0f85cd501be6b3e582e6b",
                        "commits_ahead_of_tag": 34,
                        "hosting_url": "https://example.invalid/src.tar.gz",
                    },
                }
            ]
        }
        problems = verify(archive=archive, version_output=REAL_VERSION_OUTPUT, lock=lock)
        assert any("SHA-256 does not match" in str(p) for p in problems)

    def test_a_lock_file_pointing_at_a_different_commit_fails(self, tmp_path: Path) -> None:
        archive = build_source_archive(tmp_path / "src.tar.gz")
        lock = {
            "components": [
                {
                    "name": "ffprobe",
                    "corresponding_source": {
                        "archive_sha256": verify_source.sha256(archive),
                        "commit": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
                        "commits_ahead_of_tag": 34,
                        "hosting_url": "https://example.invalid/src.tar.gz",
                    },
                }
            ]
        }
        problems = verify(archive=archive, version_output=REAL_VERSION_OUTPUT, lock=lock)
        assert any("corresponding source at deadbeef" in str(p) for p in problems)

    def test_a_missing_hosting_url_fails(self, tmp_path: Path) -> None:
        """An archive nobody can reach is not an offer of source."""
        archive = build_source_archive(tmp_path / "src.tar.gz")
        lock = {
            "components": [
                {
                    "name": "ffprobe",
                    "corresponding_source": {
                        "archive_sha256": verify_source.sha256(archive),
                        "commit": "9b6c8969e05b4f0b29f0f85cd501be6b3e582e6b",
                        "commits_ahead_of_tag": 34,
                        "hosting_url": "",
                    },
                }
            ]
        }
        problems = verify(archive=archive, version_output=REAL_VERSION_OUTPUT, lock=lock)
        assert any("hosting_url" in str(p) for p in problems)


class TestTheShippedLockFile:
    """Invariants on the real binaries.lock.json, independent of any downloaded archive."""

    @pytest.fixture(scope="class")
    def ffprobe_entry(self) -> dict[str, object]:
        lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
        entry = next(c for c in lock["components"] if c["name"] == "ffprobe")
        assert isinstance(entry, dict)
        return entry

    def test_the_recorded_source_matches_the_recorded_binary_version(
        self, ffprobe_entry: dict[str, object]
    ) -> None:
        source = ffprobe_entry["corresponding_source"]
        assert isinstance(source, dict)
        identity = parse_binary_identity(f"ffprobe version {ffprobe_entry['version']}\n")
        assert source["release_tag"] == f"n{identity.release}"
        assert source["commits_ahead_of_tag"] == identity.commits_ahead
        assert identity.commit is not None
        assert str(source["commit"]).startswith(identity.commit)

    def test_the_recorded_library_versions_match_the_source_archive_expectation(
        self, ffprobe_entry: dict[str, object]
    ) -> None:
        recorded = ffprobe_entry["library_versions"]
        assert isinstance(recorded, dict)
        assert {
            name: tuple(int(part) for part in str(value).split("."))
            for name, value in recorded.items()
        } == REAL_LIBRARIES

    def test_the_download_url_is_immutable_not_the_rolling_latest_tag(
        self, ffprobe_entry: dict[str, object]
    ) -> None:
        """BtbN replaces the `latest` assets on every rebuild.

        Pinning to `latest` would make the build unreproducible the next day and would
        silently change which binary the checksum is meant to protect.
        """
        url = str(ffprobe_entry["download_url"])
        assert "/releases/download/latest/" not in url
        assert "autobuild-" in url
        assert str(ffprobe_entry["version"]).split("-20")[0] in url

    def test_the_published_checksum_is_recorded_for_the_pinned_download(
        self, ffprobe_entry: dict[str, object]
    ) -> None:
        published = str(ffprobe_entry["published_sha256"])
        assert len(published) == 64
        assert published != str(ffprobe_entry["as_supplied_sha256"]), (
            "the pinned immutable asset is a different zip from the rolling repack; "
            "identical hashes here would mean the pin was never actually changed"
        )

    def test_every_source_archive_records_a_reproducible_command(
        self, ffprobe_entry: dict[str, object]
    ) -> None:
        for key in ("corresponding_source", "build_recipe_source"):
            spec = ffprobe_entry[key]
            assert isinstance(spec, dict)
            assert spec["commit"] in str(spec["archive_command"])
            assert str(spec["archive_prefix"]) in str(spec["archive_command"])
            assert len(str(spec["archive_sha256"])) == 64

    def test_placeholder_hosting_is_flagged_not_silently_accepted(
        self, ffprobe_entry: dict[str, object]
    ) -> None:
        """Until a real release domain exists, the lock file must say so out loud."""
        source = ffprobe_entry["corresponding_source"]
        assert isinstance(source, dict)
        if "example" in str(source["hosting_url"]):
            assert "PLACEHOLDER" in str(source["hosting_status"])


def _real_archive() -> Path | None:
    lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    entry = next(c for c in lock["components"] if c["name"] == "ffprobe")
    archive = REPO_ROOT / str(entry["corresponding_source"]["archive"])
    return archive if archive.is_file() else None


REAL_FFPROBE = REPO_ROOT / "third-party" / "bin" / "ffprobe.exe"


@pytest.mark.requires_inspectors
@pytest.mark.skipif(
    _real_archive() is None or not REAL_FFPROBE.is_file(),
    reason="needs the downloaded corresponding-source archive and the real ffprobe",
)
class TestAgainstTheRealArtefacts:
    """The end-to-end G-5 check, run over the actual 17 MB archive and the actual binary.

    Everything above works on fixtures. This is the one that would catch us shipping the
    wrong tarball.
    """

    def test_the_archived_source_corresponds_to_the_shipped_binary(self) -> None:
        archive = _real_archive()
        assert archive is not None
        lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
        problems = verify(
            archive=archive,
            version_output=verify_source.read_version_output(REAL_FFPROBE),
            lock=lock,
        )
        assert problems == [], "\n".join(str(p) for p in problems)

    def test_the_archive_contains_the_ffmpeg_licence_texts(self) -> None:
        """A source drop without COPYING.LGPLv3 does not evidence the licence we claim."""
        archive = _real_archive()
        assert archive is not None
        with tarfile.open(archive, "r:*") as handle:
            names = {Path(member.name).name for member in handle.getmembers() if member.isfile()}
        assert {"COPYING.LGPLv3", "COPYING.LGPLv2.1", "LICENSE.md", "configure"} <= names
