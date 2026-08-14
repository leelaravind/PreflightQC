# PyInstaller specification for PreflightQC.
#
# ONE-DIRECTORY BUILD, NEVER ONE-FILE.
#
# This is a licensing requirement, not a preference. A one-file build extracts to a temp
# directory at runtime, which frustrates the LGPL shared-library-replacement posture that
# ADR-001 section 4.1 relies on: a user must be able to identify and substitute the Qt and
# libav* libraries. One-dir keeps them as separate, unobfuscated, replaceable files.
#
# Invoke through packaging/build.py, not directly: this spec freezes the application, but
# presets/, licenses/ and bin/ are staged afterwards (see below).
#
#   python packaging/build.py

import sys
from pathlib import Path

SPEC_DIR = Path(SPECPATH).resolve()
REPO_ROOT = SPEC_DIR.parent

if str(SPEC_DIR) not in sys.path:
    sys.path.insert(0, str(SPEC_DIR))

block_cipher = None

# PACKAGE-INTERNAL DATA ONLY — the list lives in packaging/frozen_datas.py, one
# manifest imported here AND by tests/packaging/test_frozen_data_resources.py, which
# fails if any non-Python file under src/preflightqc is not declared. That test exists
# because the second 1.0.0 candidate shipped without preflightqc/rules/schema/
# preset.schema.json — the loader reads it relative to __file__, so the app installed
# on a clean Windows 11 machine and died on first launch (Phase 13, 2026-08-14). The
# full root-cause note is in frozen_datas.py itself.
#
# presets/, licenses/ and bin/ are staged by packaging/build.py into the package ROOT,
# not declared here. PyInstaller 6 places declared `datas` under `_internal/`, but
# ADR-001 section 5 requires them beside the executable — which is where
# platform.paths.application_root() resolves them, and where a licence folder has to be
# for "accompanying the distribution" to mean anything.
#
# Declaring them here as well would ship two copies of the licence folder: two things to
# keep in step, and an ambiguity about which one the dependency manifest describes.
from frozen_datas import pyinstaller_datas

datas = pyinstaller_datas(REPO_ROOT)

# The exclusion policy lives in packaging/frozen_excludes.py — one list, imported here
# AND by tests/packaging/test_frozen_import_closure.py, which blocks every excluded
# module in a fresh interpreter and imports the real launch closure. That test exists
# because the first 1.0.0 candidate excluded urllib.request, which jsonschema imports at
# module scope: the package built, passed every gate, installed on a clean Windows 11
# machine, and died on first launch (Phase 13, 2026-08-12). The full root-cause note,
# and the argument for why the remaining excludes (no ssl/_ssl above all: no TLS stack
# ships) are safe, is in frozen_excludes.py itself.
from frozen_excludes import EXCLUDES as excludes

a = Analysis(
    [str(REPO_ROOT / "src" / "preflightqc" / "ui" / "app.py")],
    pathex=[str(REPO_ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=["preflightqc.ui.main_window", "preflightqc.ui.about"],
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,          # one-dir: binaries stay outside the executable
    name="PreflightQC",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                      # UPX would obfuscate shipped library names
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # The Product Owner-approved logo, as a multi-size Windows icon
    # (assets/logo/PROVENANCE.md). Regenerate with tools/generate_icons.py.
    icon=str(REPO_ROOT / "assets" / "logo" / "preflightqc.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,                      # see above: names must stay identifiable
    upx_exclude=[],
    name="PreflightQC",
)
