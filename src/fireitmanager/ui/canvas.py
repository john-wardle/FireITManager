"""Central canvas widget for the FireIT Manager application."""

from __future__ import annotations

from fireitmanager.canvas.scene import CanvasScene
from fireitmanager.canvas.view import CanvasView


class CampCanvas(CanvasView):
    """Central workspace for incident planning and operational layout."""

    def __init__(self) -> None:
        super().__init__(CanvasScene())
        self.setObjectName("campCanvas")
