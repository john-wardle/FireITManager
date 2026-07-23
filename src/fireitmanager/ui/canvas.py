"""Central canvas widget for the FireIT Manager application."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel

from fireitmanager.models.incident import Incident
from fireitmanager.canvas.scene import CanvasScene
from fireitmanager.canvas.view import CanvasView


class CampCanvas(CanvasView):
    """Central workspace for incident site-map and network layout."""

    site_item_selected = Signal(str, str, str, str, str)
    site_object_selected = Signal(object)

    def __init__(self, incident: Incident | None = None) -> None:
        self.site_scene = CanvasScene(incident)
        super().__init__(self.site_scene)
        self.setObjectName("campCanvas")
        self._title_base_point_size = 16.0
        self.title_overlay = QLabel(self.viewport())
        self.title_overlay.setObjectName("siteMapTitleOverlay")
        self.title_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.title_overlay.setStyleSheet(
            "color: #f3f6fb;"
            "background-color: rgba(19, 23, 29, 190);"
            "border: 1px solid rgba(148, 163, 184, 120);"
            "border-radius: 4px;"
            "padding: 6px 10px;"
        )
        self.site_scene.site_item_selected.connect(self.site_item_selected)
        self.site_scene.site_object_selected.connect(self.site_object_selected)
        self.zoom_changed.connect(self._update_title_scale)
        self._set_title(incident)

    def load_incident(self, incident: Incident, *, center: bool = True) -> None:
        """Refresh the site map from the active incident graph."""
        self.site_scene.load_incident(incident)
        self._set_title(incident)
        if center:
            self.center_scene(record_history=False)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API name
        super().resizeEvent(event)
        self._position_title_overlay()

    def _set_title(self, incident: Incident | None) -> None:
        if incident is None:
            self.title_overlay.setText("Site Map")
        else:
            self.title_overlay.setText(f"Site Map - {incident.summary()}")
        self._update_title_scale(self.zoom_factor)

    def _update_title_scale(self, zoom_factor: float) -> None:
        clamped_zoom = max(0.75, min(1.6, zoom_factor))
        font = self.title_overlay.font()
        font.setPointSizeF(self._title_base_point_size * clamped_zoom)
        font.setBold(True)
        self.title_overlay.setFont(font)
        self._position_title_overlay()

    def _position_title_overlay(self) -> None:
        margin = 12
        max_width = max(120, self.viewport().width() - (margin * 2))
        self.title_overlay.setMaximumWidth(max_width)
        self.title_overlay.adjustSize()
        width = min(self.title_overlay.sizeHint().width(), max_width)
        height = self.title_overlay.sizeHint().height()
        self.title_overlay.setGeometry(margin, margin, width, height)
        self.title_overlay.raise_()
