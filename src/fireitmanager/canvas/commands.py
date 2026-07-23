"""Undoable canvas commands."""

from __future__ import annotations

from PySide6.QtCore import QPoint
from PySide6.QtGui import QUndoCommand
from PySide6.QtWidgets import QGraphicsView


class CanvasCommand(QUndoCommand):
    """Base class for undoable canvas operations."""

    def __init__(self, view: QGraphicsView, label: str) -> None:
        super().__init__(label)
        self._view = view


class ZoomCanvasCommand(CanvasCommand):
    """Apply a zoom change that can be undone and redone."""

    def __init__(self, view: QGraphicsView, factor: float) -> None:
        super().__init__(view, "Zoom Canvas")
        self._factor = factor

    def redo(self) -> None:  # noqa: D401 - Qt override
        """Apply the zoom factor."""
        self._view._apply_zoom(self._factor)  # type: ignore[attr-defined]

    def undo(self) -> None:  # noqa: D401 - Qt override
        """Restore the previous zoom factor."""
        self._view._apply_zoom(1.0 / self._factor)  # type: ignore[attr-defined]


class CenterSceneCommand(CanvasCommand):
    """Center the canvas on the active scene."""

    def __init__(self, view: QGraphicsView) -> None:
        super().__init__(view, "Center Scene")
        self._previous_position = QPoint(
            view.horizontalScrollBar().value(),
            view.verticalScrollBar().value(),
        )

    def redo(self) -> None:  # noqa: D401 - Qt override
        """Center the scene."""
        if hasattr(self._view, "_center_target"):
            self._view.centerOn(self._view._center_target())  # type: ignore[attr-defined]
            return
        self._view.centerOn(self._view.scene().sceneRect().center())

    def undo(self) -> None:  # noqa: D401 - Qt override
        """Restore the previous scroll position."""
        self._view.horizontalScrollBar().setValue(self._previous_position.x())
        self._view.verticalScrollBar().setValue(self._previous_position.y())
