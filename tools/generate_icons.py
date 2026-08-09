"""Generate the production icon derivatives from the approved logo.

The source of truth is ``assets/logo/logo.png`` — Product Owner-provided and approved
artwork. Every derivative is a pure geometric resize of that file: no crop, no recolour,
no recomposition, no stylistic reinterpretation. Qt's smooth (bilinear-filtered)
scaler is used at fixed settings, so for a pinned Qt version the outputs are
deterministic byte-for-byte.

Outputs:

    assets/logo/preflightqc.ico             multi-size Windows icon:
                                            16/24/32/48 as 32-bit BMP entries (the
                                            sizes Explorer renders from classic DIBs)
                                            and 64/128/256 as PNG entries
    assets/logo/logo-512.png                marketplace/listing derivative
    src/preflightqc/ui/assets/preflightqc.png
                                            256 px window/taskbar icon, shipped in
                                            the frozen package

The ICO container is assembled by hand because the repository deliberately adds no
imaging dependency: header + directory entries + per-image payloads, per the format
Microsoft documents for ICONDIR/ICONDIRENTRY.

    python tools/generate_icons.py
"""

from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "assets" / "logo" / "logo.png"
ICO_OUT = REPO_ROOT / "assets" / "logo" / "preflightqc.ico"
MARKETING_OUT = REPO_ROOT / "assets" / "logo" / "logo-512.png"
WINDOW_ICON_OUT = REPO_ROOT / "src" / "preflightqc" / "ui" / "assets" / "preflightqc.png"

BMP_SIZES = (16, 24, 32, 48)
PNG_SIZES = (64, 128, 256)


def _scaled(image: QImage, size: int) -> QImage:  # noqa: F821 - imported in main
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage

    result = image.scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    return result.convertToFormat(QImage.Format.Format_ARGB32)


def _png_bytes(image: QImage) -> bytes:  # noqa: F821
    from PySide6.QtCore import QBuffer, QIODevice

    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise RuntimeError("PNG encode failed")
    return bytes(buffer.data())


def _bmp_entry_bytes(image: QImage) -> bytes:  # noqa: F821
    """A 32-bit BGRA DIB as an ICO payload: BITMAPINFOHEADER with doubled height,
    bottom-up XOR rows, then the (all-transparent-bits-zero) 1-bpp AND mask."""
    width, height = image.width(), image.height()
    xor_rows = []
    for y in range(height):
        pointer = image.constScanLine(y)
        xor_rows.append(bytes(pointer[: width * 4]))
    xor_data = b"".join(reversed(xor_rows))  # bottom-up

    and_stride = ((width + 31) // 32) * 4
    and_data = b"\x00" * (and_stride * height)

    header = struct.pack(
        "<IiiHHIIiiII",
        40,                # biSize
        width,
        height * 2,        # XOR + AND
        1,                 # biPlanes
        32,                # biBitCount
        0,                 # BI_RGB
        len(xor_data) + len(and_data),
        0, 0, 0, 0,
    )
    return header + xor_data + and_data


def build_ico(source: QImage) -> bytes:  # noqa: F821
    entries: list[tuple[int, bytes]] = []
    for size in BMP_SIZES:
        entries.append((size, _bmp_entry_bytes(_scaled(source, size))))
    for size in PNG_SIZES:
        entries.append((size, _png_bytes(_scaled(source, size))))

    directory = struct.pack("<HHH", 0, 1, len(entries))
    offset = len(directory) + 16 * len(entries)
    body = b""
    for size, payload in entries:
        directory_size = size if size < 256 else 0
        directory += struct.pack(
            "<BBBBHHII",
            directory_size,
            directory_size,
            0,   # colour count (true colour)
            0,   # reserved
            1,   # planes
            32,  # bit count
            len(payload),
            offset + len(body),
        )
        body += payload
    return directory + body


def main() -> int:
    from PySide6.QtGui import QGuiApplication, QImage

    QGuiApplication.setApplicationName("preflightqc-icon-generator")
    _app = QGuiApplication.instance() or QGuiApplication([])

    if not SOURCE.is_file():
        print(f"error: approved logo not found at {SOURCE}", file=sys.stderr)
        return 2
    source = QImage(str(SOURCE))
    if source.isNull():
        print("error: the approved logo could not be decoded", file=sys.stderr)
        return 2
    if source.width() != source.height():
        print(
            f"error: expected square artwork, got {source.width()}x{source.height()}",
            file=sys.stderr,
        )
        return 2

    ICO_OUT.write_bytes(build_ico(source))
    WINDOW_ICON_OUT.parent.mkdir(parents=True, exist_ok=True)
    if not _scaled(source, 256).save(str(WINDOW_ICON_OUT), "PNG"):
        raise RuntimeError("window icon save failed")
    if not _scaled(source, 512).save(str(MARKETING_OUT), "PNG"):
        raise RuntimeError("marketing derivative save failed")

    for path in (SOURCE, ICO_OUT, WINDOW_ICON_OUT, MARKETING_OUT):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"  {digest}  {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
