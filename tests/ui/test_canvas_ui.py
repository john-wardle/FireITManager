"""UI-focused tests for the FireIT Manager workspace."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from fireitmanager.canvas.constants import SCENE_RECT
from fireitmanager.canvas.scene import CanvasScene
from fireitmanager.ui.canvas import CampCanvas


def _get_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_canvas_scene_bootstraps_empty_state() -> None:
    _get_app()

    scene = CanvasScene()

    assert scene.sceneRect() == SCENE_RECT

    texts = {
        item.toPlainText()
        for item in scene.items()
        if hasattr(item, "toPlainText")
    }

    assert "Camp Canvas" in texts
    assert "No incident loaded" in texts


def test_canvas_view_exposes_zoom_state() -> None:
    _get_app()

    canvas = CampCanvas()

    assert canvas.objectName() == "campCanvas"
    assert canvas.zoom_factor == 1.0

    canvas.zoom(2.0)

    assert canvas.zoom_factor > 1.0
    zoomed = canvas.zoom_factor

    canvas.undo()

    assert canvas.zoom_factor == 1.0

    canvas.redo()

    assert canvas.zoom_factor == zoomed
