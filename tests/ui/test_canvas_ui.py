"""UI-focused tests for the FireIT Manager workspace."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication, QGraphicsItem

from fireitmanager.canvas.constants import SCENE_RECT
from fireitmanager.canvas.scene import CanvasScene, SiteMapCableItem, SiteMapNodeItem
from fireitmanager.ui.canvas import CampCanvas
from fireitmanager.ui.workspace import build_demo_workspace_snapshot


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

    assert "Site Map" in texts
    assert "No incident loaded" in texts


def test_canvas_scene_populates_draggable_network_map() -> None:
    _get_app()
    snapshot = build_demo_workspace_snapshot()

    scene = CanvasScene(snapshot.incident)

    nodes = [item for item in scene.items() if isinstance(item, SiteMapNodeItem)]
    labels = {item.label for item in nodes}
    assert {"IT Staging", "it-router-01", "it-workstation-01"} <= labels

    router = next(item for item in nodes if item.label == "it-router-01")
    workstation = next(item for item in nodes if item.label == "it-workstation-01")
    assert router.flags() & QGraphicsItem.ItemIsMovable
    assert workstation.flags() & QGraphicsItem.ItemIsMovable

    cables = [item for item in scene.items() if isinstance(item, SiteMapCableItem)]
    assert len(cables) == 1
    original_line = cables[0].line()

    router.setPos(router.pos() + QPointF(80.0, 0.0))

    assert cables[0].line() != original_line

    selected_payloads: list[tuple[str, str, str, str, str]] = []
    scene.site_item_selected.connect(
        lambda name, kind, path, description, details: selected_payloads.append(
            (name, kind, path, description, details)
        )
    )
    scene.clearSelection()
    workstation.setSelected(True)

    assert selected_payloads[-1][0] == "it-workstation-01"
    assert selected_payloads[-1][1] == "device"


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
