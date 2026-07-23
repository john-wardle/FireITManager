"""Central canvas widget for the FireIT Manager application."""

from __future__ import annotations

from PySide6.QtCore import Signal

from fireitmanager.models.incident import Incident
from fireitmanager.canvas.scene import CanvasScene
from fireitmanager.canvas.view import CanvasView


class CampCanvas(CanvasView):
    """Central workspace for incident site-map and network layout."""

    site_item_selected = Signal(str, str, str, str, str)

    def __init__(self, incident: Incident | None = None) -> None:
        self.site_scene = CanvasScene(incident)
        super().__init__(self.site_scene)
        self.setObjectName("campCanvas")
        self.site_scene.site_item_selected.connect(self.site_item_selected)

    def load_incident(self, incident: Incident) -> None:
        """Refresh the site map from the active incident graph."""
        self.site_scene.load_incident(incident)
        self.center_scene(record_history=False)
