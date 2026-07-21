"""Graphics view for the FireIT Manager camp workspace."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QFrame

from fireitmanager.canvas.constants import ZOOM_MAX, ZOOM_MIN, ZOOM_STEP


class CanvasView(QGraphicsView):
    """Canvas view with zoom controls and a stable pan interaction."""

    zoom_changed = Signal(float)

    def __init__(self, scene: QGraphicsScene, parent=None) -> None:
        super().__init__(scene, parent)
        self._zoom_factor = 1.0
        self._zoom_step = ZOOM_STEP
        self.setRenderHints(
            QPainter.Antialiasing
            | QPainter.TextAntialiasing
            | QPainter.SmoothPixmapTransform
        )
        self.setBackgroundBrush(QColor(19, 23, 29))
        self.setFrameShape(QFrame.NoFrame)
        self.setAlignment(Qt.AlignCenter)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.centerOn(scene.sceneRect().center())

    @property
    def zoom_factor(self) -> float:
        """Return the current zoom factor."""
        return self._zoom_factor

    def wheelEvent(self, event) -> None:  # type: ignore[override]
        """Zoom the canvas when the user uses the mouse wheel."""
        delta = event.angleDelta().y()
        if delta == 0:
            super().wheelEvent(event)
            return

        factor = self._zoom_step if delta > 0 else 1.0 / self._zoom_step
        self.zoom(factor)
        event.accept()

    def zoom(self, factor: float) -> None:
        """Apply a bounded zoom step."""
        target_zoom = max(ZOOM_MIN, min(ZOOM_MAX, self._zoom_factor * factor))
        actual_factor = target_zoom / self._zoom_factor

        if actual_factor == 1.0:
            return

        self.scale(actual_factor, actual_factor)
        self._zoom_factor = target_zoom
        self.zoom_changed.emit(self._zoom_factor)

    def zoom_in(self) -> None:
        """Convenience wrapper for a zoom-in action."""
        self.zoom(self._zoom_step)

    def zoom_out(self) -> None:
        """Convenience wrapper for a zoom-out action."""
        self.zoom(1.0 / self._zoom_step)

    def reset_zoom(self) -> None:
        """Restore the default zoom level."""
        self.resetTransform()
        self._zoom_factor = 1.0
        self.zoom_changed.emit(self._zoom_factor)

    def center_scene(self) -> None:
        """Center the visible view on the current scene."""
        self.centerOn(self.scene().sceneRect().center())

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        """Temporarily enable panning with the space bar."""
        if event.key() == Qt.Key_Space:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event) -> None:  # type: ignore[override]
        """Restore the default drag mode when panning ends."""
        if event.key() == Qt.Key_Space:
            self.setDragMode(QGraphicsView.NoDrag)
        super().keyReleaseEvent(event)
