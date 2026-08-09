"""Custom widgets: the status readout and the empty state.

Both exist because a stock widget was doing the job badly. Everything else in the
interface is a plain Qt widget with a style sheet, which is deliberate — a custom widget
is a maintenance cost and a screen-reader risk, so there are exactly two.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from preflightqc.ui import design as d
from preflightqc.ui import severity_style

#: Which tone paints each readout segment. Order is fixed by `viewmodels.READOUT_ORDER`.
_SEGMENT_TONES: dict[str, str] = {
    "FAIL": "FAIL",
    "WARN": "WARN",
    "PASS": "PASS",
    "NOT_INSPECTED": "NOT_INSPECTED",
    "NOT_APPLICABLE": "NOT_APPLICABLE",
}


class StatusReadout(QWidget):
    """A segmented bar showing the batch outcome, worst first.

    Replaces five loose text counters that competed with the export buttons for the same
    strip of footer. The bar is never the only signal: the same counts are printed beside
    it with their markers and labels, so it degrades to plain text rather than to nothing.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._segments: tuple[tuple[str, int], ...] = ()
        self._total = 0
        self._pending = 0
        self.setMinimumHeight(d.READOUT_HEIGHT)
        self.setMaximumHeight(d.READOUT_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAccessibleName("Batch outcome")
        self._update_accessible_description()

    def set_segments(self, segments: tuple[tuple[str, int], ...], *, pending: int = 0) -> None:
        self._segments = segments
        self._total = sum(count for _, count in segments) + pending
        self._pending = pending
        self._update_accessible_description()
        self.update()

    def clear(self) -> None:
        self.set_segments(())

    def _update_accessible_description(self) -> None:
        if not self._segments or not self._total:
            self.setAccessibleDescription("No files checked yet")
            self.setToolTip("")
            return
        parts = [
            f"{count} {severity_style.for_status(name).label.lower()}"
            for name, count in self._segments
            if count
        ]
        if self._pending:
            parts.append(f"{self._pending} not yet checked")
        text = f"{self._total} files: " + ", ".join(parts)
        self.setAccessibleDescription(text)
        self.setToolTip(text)

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt override
        return QSize(240, d.READOUT_HEIGHT)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 - Qt override
        if not self._total:
            # An empty track is noise. Before the first run there is nothing to read out,
            # so the readout draws nothing at all.
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        track = QRectF(self.rect()).adjusted(0, 6, 0, -6)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(d.SURFACE_BASE))
        painter.drawRoundedRect(track, d.RADIUS_CHIP, d.RADIUS_CHIP)

        x = track.left()
        for name, count in self._segments:
            if not count:
                continue
            width = track.width() * (count / self._total)
            tone = severity_style.for_status(_SEGMENT_TONES.get(name, name))
            painter.setBrush(QColor(tone.foreground))
            painter.drawRect(QRectF(x, track.top(), width, track.height()))
            x += width

        # The unchecked remainder stays as bare track, so a run in progress reads as
        # "this much is still unknown" rather than as a shrunken result.
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QColor(d.BORDER_SUBTLE))
        painter.drawRoundedRect(track.adjusted(0.5, 0.5, -0.5, -0.5), d.RADIUS_CHIP, d.RADIUS_CHIP)
        painter.end()


class EmptyState(QFrame):
    """What the batch area shows before anything is loaded.

    The window used to open on two blank panes with a 12-px status-bar hint at the very
    bottom edge. A professional tool can be dense, but it cannot be silent on first run:
    the user has to learn the order of operations from somewhere, and the alternative to
    this panel is documentation nobody reads.
    """

    TITLE = "Drop video files here"
    SUBTITLE = "or use Add files and Add folder"
    STEPS: tuple[tuple[str, str], ...] = (
        ("1", "Add the files you are about to deliver"),
        ("2", "Choose the preset for where they are going"),
        ("3", "Run the check, review findings, export a report"),
    )
    PRIVACY = (
        "Everything runs on this machine. Source files are opened read-only and are "
        "never modified, moved or uploaded."
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("EmptyState")
        self.setAccessibleName("Getting started")
        self.setAccessibleDescription(
            f"{self.TITLE}. " + " ".join(f"Step {n}: {text}." for n, text in self.STEPS)
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(d.SPACE_XL, d.SPACE_XL, d.SPACE_XL, d.SPACE_XL)
        outer.setSpacing(d.SPACE_LG)
        outer.addStretch(1)

        title = QLabel(self.TITLE)
        title.setObjectName("EmptyTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        outer.addWidget(title)

        subtitle = QLabel(self.SUBTITLE)
        subtitle.setObjectName("EmptyBody")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        outer.addWidget(subtitle)

        outer.addSpacing(d.SPACE_MD)

        steps = QWidget()
        steps_layout = QVBoxLayout(steps)
        steps_layout.setContentsMargins(0, 0, 0, 0)
        steps_layout.setSpacing(d.SPACE_SM)
        for number, text in self.STEPS:
            row = QHBoxLayout()
            row.setSpacing(d.SPACE_MD)
            marker = QLabel(number)
            marker.setObjectName("EmptyStepNumber")
            marker.setFixedWidth(16)
            label = QLabel(text)
            label.setObjectName("EmptyStep")
            row.addWidget(marker)
            row.addWidget(label, 1)
            steps_layout.addLayout(row)
        holder = QHBoxLayout()
        holder.addStretch(1)
        holder.addWidget(steps)
        holder.addStretch(1)
        outer.addLayout(holder)

        outer.addSpacing(d.SPACE_MD)

        privacy = QLabel(self.PRIVACY)
        privacy.setObjectName("PrivacyNote")
        privacy.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        privacy.setWordWrap(True)
        privacy.setMaximumWidth(420)
        privacy_row = QHBoxLayout()
        privacy_row.addStretch(1)
        privacy_row.addWidget(privacy)
        privacy_row.addStretch(1)
        outer.addLayout(privacy_row)

        outer.addStretch(1)
