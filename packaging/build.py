"""Build the PreflightQC Windows package (Phase 11).

Ordering here is deliberate: **every licensing gate that can be checked before the build
is checked before the build.** Discovering at the packaging step that the bundled ffprobe
is a GPL build wastes a build; discovering it after the installer is signed wastes a
release. So the order is verify → freeze → stage → verify again.

    python packaging/build.py                    # full build
    python packaging/build.py --skip-installer   # PyInstaller + gates only
    python packaging/build.py --clean            # discard dist/ and build/ first

The installer step needs Inno Setup's ISCC on PATH or in its default location; it is
skipped with a clear message rather than silently omitted if absent. Signing is a separate
step (``packaging/sign.py``) because it needs a certificate this repository does not and
must not contain.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGING = REPO_ROOT / "packaging"
DIST = REPO_ROOT / "dist"
PACKAGE = DIST / "PreflightQC"
LOCK_FILE = PACKAGING / "binaries.lock.json"

#: Where ISCC lives. A portable extraction under LOCALAPPDATA is checked too, so a build
#: machine does not have to have Inno Setup installed system-wide to produce an installer.
ISCC_CANDIDATES: tuple[Path, ...] = (
    Path(os.environ.get("PREFLIGHTQC_ISCC", "")) if os.environ.get("PREFLIGHTQC_ISCC") else Path(),
    Path(os.environ.get("LOCALAPPDATA", "")) / "PreflightQC-build-tools" / "innosetup" / "ISCC.exe",
    Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
    / "Inno Setup 6"
    / "ISCC.exe",
    Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Inno Setup 6" / "ISCC.exe",
)

#: Qt libraries PyInstaller collects that PreflightQC does not use.
#:
#: The spec's excludes list removes the *Python* modules, but PyInstaller still ships the
#: native libraries because Qt's own DLLs depend on each other. The result was a package
#: that shipped **Qt6Network.dll** while the product promises it cannot make a network
#: request (spec §18, AC-12). "We excluded the Python binding" is not the same claim.
#:
#: Removal order matters: Qt6Network is only reachable through the QML/Quick/Pdf cluster,
#: so the cluster goes and Network goes with it. This is verified rather than assumed —
#: `verify_no_dangling_imports` re-derives the import closure from the PE headers of what
#: actually remains and fails the build if anything still needs a removed library.
PRUNED_QT_LIBRARIES: tuple[str, ...] = (
    "Qt6Network.dll",
    "Qt6Qml.dll",
    "Qt6QmlMeta.dll",
    "Qt6QmlModels.dll",
    "Qt6QmlWorkerScript.dll",
    "Qt6Quick.dll",
    "Qt6OpenGL.dll",
    "Qt6Pdf.dll",
    "Qt6VirtualKeyboard.dll",
)

#: Qt plugin directories that exist only to serve the pruned libraries.
PRUNED_QT_PLUGIN_DIRS: tuple[str, ...] = (
    "qml",
    "plugins/platforminputcontexts",
)

#: Qt plugins are leaves: they are loaded by name at runtime and nothing links to them.
#: So a plugin left needing a removed library can be dropped safely, and dropping it is
#: better than reinstating the library. Anything outside this directory that has a
#: dangling import is a real breakage and must fail the build instead.
QT_PLUGIN_ROOT = "_internal/PySide6/plugins"


@dataclass
class Step:
    name: str
    ok: bool
    detail: str = ""


def run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    printable = " ".join(Path(c).name if Path(c).is_absolute() else c for c in command)
    print(f"    $ {printable}")
    return subprocess.run(
        command, cwd=cwd or REPO_ROOT, capture_output=True, text=True, check=False
    )


def _python() -> str:
    return sys.executable


def verify_inputs() -> list[Step]:
    """Gates that must hold before a single byte is frozen."""
    steps: list[Step] = []

    result = run([_python(), str(PACKAGING / "fetch_binaries.py"), "--verify-only"])
    steps.append(
        Step(
            "inspector binaries match binaries.lock.json",
            result.returncode == 0,
            result.stdout.strip() or result.stderr.strip(),
        )
    )

    result = run([_python(), str(PACKAGING / "verify_source.py")])
    steps.append(
        Step(
            "G-5 corresponding source matches the shipped binary",
            result.returncode == 0,
            result.stdout.strip() or result.stderr.strip(),
        )
    )
    return steps


def freeze() -> Step:
    result = run(
        [
            _python(),
            "-m",
            "PyInstaller",
            str(PACKAGING / "preflightqc.spec"),
            "--noconfirm",
            "--distpath",
            str(DIST),
            "--workpath",
            str(REPO_ROOT / "build"),
        ]
    )
    if result.returncode != 0:
        tail = "\n".join(result.stderr.strip().splitlines()[-25:])
        return Step("PyInstaller one-dir build", False, tail)
    return Step("PyInstaller one-dir build", True, f"{PACKAGE}")


def stage_payload() -> Step:
    """Put presets, licences and inspectors where the application resolves them.

    PyInstaller 6 places bundled data under ``_internal/``. ADR-001 §5 requires them at
    the package root, next to the executable, because that is where
    ``platform.paths.application_root()`` looks — and, for ``licenses/``, because a
    licence folder buried inside an implementation directory is not "accompanying the
    distribution" in any useful sense.
    """
    if not PACKAGE.is_dir():
        return Step("stage payload", False, f"no package at {PACKAGE}")

    for name in ("presets", "licenses"):
        source = REPO_ROOT / name if name == "presets" else REPO_ROOT / "third-party" / "licenses"
        target = PACKAGE / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        # PyInstaller may also have placed a copy under _internal/. Two copies of the
        # licence folder means two things to keep in step, and the manifest would have to
        # choose one. Remove the buried duplicate.
        buried = PACKAGE / "_internal" / name
        if buried.is_dir():
            shutil.rmtree(buried)

    bin_target = PACKAGE / "bin"
    bin_target.mkdir(exist_ok=True)
    for binary in sorted((REPO_ROOT / "third-party" / "bin").glob("*")):
        if binary.is_file():
            shutil.copy2(binary, bin_target / binary.name)

    # The EULA is first-party, so it lives in packaging/ and is shipped verbatim. The
    # installer shows this exact file on its licence page, so there is one text, not a
    # shipped copy and a reviewed copy that can drift apart.
    shutil.copyfile(PACKAGING / "EULA.txt", PACKAGE / "licenses" / "EULA.txt")

    lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    ffprobe = next(c for c in lock["components"] if c["name"] == "ffprobe")
    source_spec = ffprobe["corresponding_source"]
    (PACKAGE / "licenses" / "ffmpeg-build-configuration.txt").write_text(
        "\n".join(
            [
                "FFmpeg build configuration for the libraries bundled with PreflightQC",
                "=" * 72,
                "",
                "Required by the FFmpeg LGPL compliance checklist: the exact configure line",
                "of the build shipped with this product.",
                "",
                f"Version    : {ffprobe['version']}",
                f"Build      : {ffprobe['build_identifier']}",
                f"Licence    : {ffprobe['declared_license']}",
                f"Obtained   : {ffprobe['download_url']}",
                "",
                "Configure line",
                "-" * 72,
                str(ffprobe["configuration"]),
                "",
                "Corresponding source",
                "-" * 72,
                f"Upstream   : {source_spec['upstream_repository']}",
                f"Commit     : {source_spec['commit']}",
                f"Release tag: {source_spec['release_tag']} (+{source_spec['commits_ahead_of_tag']} commits)",
                f"Archive    : {Path(str(source_spec['archive'])).name}",
                f"SHA-256    : {source_spec['archive_sha256']}",
                f"Available  : {source_spec['hosting_url']}",
                "",
                "The build recipe that produced this binary is archived alongside the source:",
                f"  {lock['components'][0]['build_recipe_source']['upstream_repository']}",
                f"  commit {lock['components'][0]['build_recipe_source']['commit']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return Step("stage presets, licences and inspectors at the package root", True)


def prune_unused_qt() -> Step:
    """Remove Qt libraries the product does not use, Qt6Network above all."""
    pyside = PACKAGE / "_internal" / "PySide6"
    if not pyside.is_dir():
        return Step("prune unused Qt libraries", False, f"no PySide6 directory in {PACKAGE}")

    removed: list[str] = []
    reclaimed = 0
    for name in PRUNED_QT_LIBRARIES:
        target = pyside / name
        if target.is_file():
            reclaimed += target.stat().st_size
            target.unlink()
            removed.append(name)

    for relative in PRUNED_QT_PLUGIN_DIRS:
        directory = pyside / Path(relative)
        if directory.is_dir():
            reclaimed += sum(p.stat().st_size for p in directory.rglob("*") if p.is_file())
            shutil.rmtree(directory)
            removed.append(f"{relative}/")

    orphans, orphan_bytes = _prune_orphaned_plugins()
    removed.extend(orphans)
    reclaimed += orphan_bytes

    return Step(
        "prune unused Qt libraries (removes Qt6Network)",
        True,
        f"removed {len(removed)}: {', '.join(removed)} ({reclaimed / 1_048_576:.1f} MB)",
    )


def _qt_imports(path: Path) -> set[str] | None:
    try:
        import pefile
    except ImportError:
        return None
    try:
        pe = pefile.PE(str(path), fast_load=True)
        pe.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
        )
        imported = {
            entry.dll.decode("ascii", "replace").lower()
            for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])
        }
        pe.close()
    except Exception:
        return None
    return {dll for dll in imported if dll.startswith(("qt6", "shiboken"))}


def _prune_orphaned_plugins() -> tuple[list[str], int]:
    """Drop Qt plugins whose libraries were just removed, repeating until stable.

    Iteration matters: a plugin can depend on another plugin's library, so one pass can
    leave a second-order orphan behind. Looping until nothing changes is cheap and means
    the prune list does not have to be re-derived by hand on every PySide6 upgrade.
    """
    plugin_root = PACKAGE / Path(QT_PLUGIN_ROOT)
    removed: list[str] = []
    reclaimed = 0
    if not plugin_root.is_dir():
        return removed, reclaimed

    while True:
        present = {p.name.lower() for p in PACKAGE.rglob("*") if p.is_file()}
        casualties = [
            path
            for path in sorted(plugin_root.rglob("*.dll"))
            if (imports := _qt_imports(path)) is not None and imports - present
        ]
        if not casualties:
            return removed, reclaimed
        for path in casualties:
            reclaimed += path.stat().st_size
            removed.append(path.relative_to(PACKAGE / "_internal" / "PySide6").as_posix())
            path.unlink()


def verify_no_dangling_imports() -> Step:
    """Prove nothing left in the package imports a library that is no longer there.

    Pruning by name is a guess; this is the check that turns it into a fact. Every
    shipped PE is parsed and its import table compared against what the package actually
    contains, so a removal that broke the load chain fails the build here rather than on
    a user's machine.
    """
    try:
        import pefile
    except ImportError:
        return Step(
            "verify no dangling DLL imports",
            False,
            "pefile is not installed; it ships with PyInstaller and is required to "
            "prove the pruned package still loads",
        )

    present = {p.name.lower() for p in PACKAGE.rglob("*") if p.is_file()}
    dangling: list[str] = []
    scanned = 0

    for path in sorted(PACKAGE.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".dll", ".pyd", ".exe"}:
            continue
        try:
            pe = pefile.PE(str(path), fast_load=True)
            pe.parse_data_directories(
                directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
            )
            imported = {
                entry.dll.decode("ascii", "replace").lower()
                for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])
            }
            pe.close()
        except Exception as error:
            dangling.append(f"{path.name}: could not read imports ({error})")
            continue
        scanned += 1
        # Only Qt/shiboken imports are our responsibility; the rest resolve from Windows.
        for dll in sorted(imported):
            if dll.startswith(("qt6", "shiboken")) and dll not in present:
                dangling.append(f"{path.relative_to(PACKAGE)} imports missing {dll}")

    if dangling:
        return Step("verify no dangling DLL imports", False, "\n".join(dangling))
    return Step("verify no dangling DLL imports", True, f"{scanned} binaries scanned")


def verify_frozen_self_check() -> Step:
    """Run the built executable's own self-check (P11-A9, P13-A4).

    This is the first moment the *packaged* application runs. It proves the frozen
    binary starts, finds its inspectors by absolute path under ``bin/``, and reports
    their versions — on a machine where PATH also contains an ffprobe, which is exactly
    the substitution spec AC-17 forbids.
    """
    executable = PACKAGE / "PreflightQC.exe"
    if not executable.is_file():
        return Step("packaged application self-check", False, f"no executable at {executable}")

    result = subprocess.run(
        [str(executable), "--self-check"],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
        cwd=str(REPO_ROOT),
    )
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        return Step("packaged application self-check", False, output)

    # The self-check must have actually performed the launch data reads (preset schema
    # + catalogue, report template) — a self-check that silently stopped reporting them
    # would certify nothing, which is how both Phase 13 failures reached a clean
    # machine. Require the affirmative lines, not merely a zero exit.
    for required_line in (
        "import closure   : OK",
        "preset catalogue : OK",
        "report template  : OK",
    ):
        if required_line not in output:
            return Step(
                "packaged application self-check",
                False,
                f"self-check output lacks '{required_line}' — the packaged app did not "
                f"verify its launch resources:\n{output}",
            )

    expected = str(PACKAGE / "bin").lower()
    if expected not in output.lower():
        return Step(
            "packaged application self-check",
            False,
            f"the packaged app did not resolve inspectors from {expected}:\n{output}",
        )
    versions = [line.strip() for line in output.splitlines() if line.strip().startswith("version")]
    return Step("packaged application self-check", True, "; ".join(versions))


def post_build_gates(product_version: str) -> list[Step]:
    steps: list[Step] = []

    result = run(
        [
            _python(),
            str(PACKAGING / "generate_manifest.py"),
            "--package",
            str(PACKAGE),
            "--product-version",
            product_version,
        ]
    )
    steps.append(
        Step(
            "G-1/G-2 dependency manifest and notices generated from the package",
            result.returncode == 0,
            (result.stdout + result.stderr).strip(),
        )
    )

    result = run([_python(), str(PACKAGING / "scan_prohibited.py"), "--package", str(PACKAGE)])
    steps.append(
        Step(
            "G-3/G-4/G-7 prohibited-component scan",
            result.returncode == 0,
            (result.stdout + result.stderr).strip(),
        )
    )

    result = run([_python(), str(PACKAGING / "layout_check.py"), "--package", str(PACKAGE)])
    steps.append(
        Step(
            "P11-A3 package layout matches ADR-001 §5",
            result.returncode == 0,
            (result.stdout + result.stderr).strip(),
        )
    )

    # Deliberately blocking, not advisory. A rule whose first-party source nobody has read
    # in six months should not ship in a product whose entire claim is that every finding
    # traces to a source somebody read.
    result = run(
        [
            _python(),
            str(PACKAGING / "staleness_report.py"),
            "--out",
            str(PACKAGE / "licenses" / "PRESET-STALENESS.txt"),
        ]
    )
    summary = next(
        (
            line.strip()
            for line in result.stdout.splitlines()
            if line.startswith(("No stale rules", "STALE RULES", "TRACEABILITY"))
        ),
        "",
    )
    steps.append(
        Step(
            "preset source staleness and traceability",
            result.returncode == 0,
            (result.stdout + result.stderr).strip() if result.returncode else summary,
        )
    )
    return steps


def find_iscc() -> Path | None:
    found = shutil.which("ISCC") or shutil.which("iscc")
    if found:
        return Path(found)
    return next((path for path in ISCC_CANDIDATES if path.is_file()), None)


def build_installer(product_version: str) -> Step:
    iscc = find_iscc()
    if iscc is None:
        return Step(
            "Inno Setup installer",
            False,
            "ISCC.exe not found. Install Inno Setup 6 or pass --skip-installer. "
            "The package itself is complete and testable without it.",
        )
    output = DIST / "installer"
    output.mkdir(parents=True, exist_ok=True)
    result = run(
        [
            str(iscc),
            f"/DMyAppVersion={product_version}",
            f"/DPackageDir={PACKAGE}",
            f"/O{output}",
            str(PACKAGING / "installer.iss"),
        ]
    )
    if result.returncode != 0:
        tail = "\n".join((result.stdout + result.stderr).strip().splitlines()[-20:])
        return Step("Inno Setup installer", False, tail)
    produced = sorted(output.glob("*.exe"))
    return Step(
        "Inno Setup installer",
        bool(produced),
        ", ".join(f"{p.name} ({p.stat().st_size / 1_048_576:.1f} MB)" for p in produced),
    )


def package_size() -> tuple[int, int]:
    files = [p for p in PACKAGE.rglob("*") if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PreflightQC Windows package")
    parser.add_argument("--product-version", default=None)
    parser.add_argument("--skip-installer", action="store_true")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    version = args.product_version
    if version is None:
        sys.path.insert(0, str(REPO_ROOT / "src"))
        from preflightqc import __version__ as version

    if args.clean:
        for directory in (DIST, REPO_ROOT / "build"):
            if directory.is_dir():
                shutil.rmtree(directory)
                print(f"    removed {directory}")

    started = time.monotonic()
    steps: list[Step] = []

    print("\n=== Pre-build gates ===")
    steps.extend(verify_inputs())
    if any(not step.ok for step in steps):
        report(steps, version, started)
        print("\nPre-build gates failed. Nothing was built.", file=sys.stderr)
        return 1

    print("\n=== Freeze ===")
    steps.append(freeze())
    if not steps[-1].ok:
        report(steps, version, started)
        return 1

    print("\n=== Stage ===")
    steps.append(stage_payload())
    if not steps[-1].ok:
        report(steps, version, started)
        return 1
    steps.append(prune_unused_qt())
    steps.append(verify_no_dangling_imports())
    if not steps[-1].ok:
        report(steps, version, started)
        return 1

    print("\n=== Post-build gates ===")
    steps.extend(post_build_gates(version))
    steps.append(verify_frozen_self_check())

    if not args.skip_installer:
        print("\n=== Installer ===")
        steps.append(build_installer(version))

    report(steps, version, started)
    failed = [step for step in steps if not step.ok]
    return 1 if failed else 0


def report(steps: list[Step], version: str, started: float) -> None:
    print("\n" + "=" * 72)
    print(f"PreflightQC {version} — build report")
    print("=" * 72)
    for step in steps:
        mark = "PASS" if step.ok else "FAIL"
        print(f"  [{mark}] {step.name}")
        if step.detail and not step.ok:
            for line in step.detail.splitlines():
                print(f"         {line}")
    if PACKAGE.is_dir():
        count, total = package_size()
        print(f"\n  Package : {PACKAGE}")
        print(f"  Files   : {count}")
        print(f"  Size    : {total / 1_048_576:.1f} MB")
    print(f"  Elapsed : {time.monotonic() - started:.1f}s")


if __name__ == "__main__":
    raise SystemExit(main())
