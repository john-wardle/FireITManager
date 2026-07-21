"""Graphics scene for the FireIT Manager camp workspace."""

from __future__ import annotations

from math import floor

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QGraphicsScene, QGraphicsTextItem

from fireitmanager.canvas.constants import (
    GRID_MAJOR_COLOR,
    GRID_MINOR_COLOR,
    MAJOR_GRID_SIZE,
    MINOR_GRID_SIZE,
    SCENE_RECT,
)


class CanvasScene(QGraphicsScene):
    """Scene with a grid background and an empty-state card."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setSceneRect(SCENE_RECT)
        self._build_empty_state()

    def _build_empty_state(self) -> None:
        """Create the centered card shown before data is loaded."""
        card = self.addRect(
            QRectF(-300.0, -170.0, 600.0, 340.0),
            QPen(QColor(72, 82, 95), 1.5),
            QColor(24, 29, 36),
        )
        card.setZValue(10)

        self._add_centered_text(
            "Camp Canvas",
            y=-120,
            point_size=22,
            bold=True,
            color=QColor(245, 247, 250),
        )
        self._add_centered_text(
            "No incident loaded",
            y=-80,
            point_size=14,
            bold=False,
            color=QColor(183, 193, 204),
        )
        self._add_centered_text(
            "This workspace will host camp planning, network layout, and incident overlays.",
            y=-25,
            point_size=11,
            bold=False,
            color=QColor(214, 220, 228),
        )
        self._add_centered_text(
            "- Explore incidents from the left dock.",
            y=18,
            point_size=11,
            bold=False,
            color=QColor(214, 220, 228),
        )
        self._add_centered_text(
            "- Properties and details will appear on the right.",
            y=44,
            point_size=11,
            bold=False,
            color=QColor(214, 220, 228),
        )
        self._add_centered_text(
            "- Canvas tools will be added as planning workflows mature.",
            y=70,
            point_size=11,
            bold=False,
            color=QColor(214, 220, 228),
        )

    def _add_centered_text(
        self,
        text: str,
        *,
        y: float,
        point_size: int,
        bold: bool,
        color: QColor,
    ) -> QGraphicsTextItem:
        """Add a centered text item to the scene."""
        item = self.addText(text)
        font: QFont = item.font()
        font.setPointSize(point_size)
        font.setBold(bold)
        item.setFont(font)
        item.setDefaultTextColor(color)
        bounds = item.boundingRect()
        item.setPos(-bounds.width() / 2.0, y)
        item.setZValue(11)
        return item

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """Draw the grid background for the visible scene area."""
        painter.fillRect(rect, QColor(19, 23, 29))

        minor_pen = QPen(GRID_MINOR_COLOR)
        minor_pen.setWidthF(0.0)
        major_pen = QPen(GRID_MAJOR_COLOR)
        major_pen.setWidthF(0.0)

        start_x = floor(rect.left() / MINOR_GRID_SIZE) * MINOR_GRID_SIZE
        end_x = floor(rect.right() / MINOR_GRID_SIZE) * MINOR_GRID_SIZE
        start_y = floor(rect.top() / MINOR_GRID_SIZE) * MINOR_GRID_SIZE
        end_y = floor(rect.bottom() / MINOR_GRID_SIZE) * MINOR_GRID_SIZE

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)

        for x in range(start_x, end_x + MINOR_GRID_SIZE, MINOR_GRID_SIZE):
            painter.setPen(major_pen if x % MAJOR_GRID_SIZE == 0 else minor_pen)
            painter.drawLine(x, rect.top(), x, rect.bottom())

        for y in range(start_y, end_y + MINOR_GRID_SIZE, MINOR_GRID_SIZE):
            painter.setPen(major_pen if y % MAJOR_GRID_SIZE == 0 else minor_pen)
            painter.drawLine(rect.left(), y, rect.right(), y)

        painter.restore()
