"""UI-focused tests for the FireIT Manager workspace."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication, QGraphicsItem, QLabel, QWidget

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
    scene_texts = {
        item.toPlainText()
        for item in scene.items()
        if hasattr(item, "toPlainText")
    }
    assert "Base Camp" not in scene_texts
    assert "Camp LAN: 2 device(s), 1 cable(s)" not in scene_texts

    router = next(item for item in nodes if item.label == "it-router-01")
    workstation = next(item for item in nodes if item.label == "it-workstation-01")
    building = next(item for item in nodes if item.label == "IT Staging")
    assert router.flags() & QGraphicsItem.ItemIsMovable
    assert workstation.flags() & QGraphicsItem.ItemIsMovable
    assert building.flags() & QGraphicsItem.ItemIsMovable
    assert building.resizable
    assert router.parentItem() is building
    assert workstation.parentItem() is building
    assert router.icon_name == "router.svg"
    assert router.icon_renderer is not None
    assert router.icon_renderer.isValid()
    assert workstation.icon_name == "laptop.svg"
    assert workstation.icon_renderer is not None
    assert workstation.icon_renderer.isValid()

    cables = [item for item in scene.items() if isinstance(item, SiteMapCableItem)]
    assert len(cables) == 1
    original_line = cables[0].line()

    original_router_scene_pos = router.scenePos()
    building_delta = QPointF(70.0, 35.0)
    building.setPos(building.pos() + building_delta)

    assert router.scenePos() == original_router_scene_pos + building_delta
    assert cables[0].line() != original_line

    line_after_building_move = cables[0].line()
    router.setPos(router.pos() + QPointF(80.0, 0.0))

    assert cables[0].line() != line_after_building_move

    original_width = building.boundingRect().width()
    original_height = building.boundingRect().height()
    building.resize_to(original_width + 140.0, original_height + 90.0)

    assert building.boundingRect().width() == original_width + 140.0
    assert building.boundingRect().height() == original_height + 90.0

    scene.detach_item_from_container(workstation)
    assert workstation.parentItem() is None
    workstation.setPos(building.scenePos() + QPointF(90.0, 95.0))
    scene.anchor_item_to_container(workstation)

    assert workstation.parentItem() is building

    selected_payloads: list[tuple[str, str, str, str, str]] = []
    selected_targets: list[object | None] = []
    scene.site_item_selected.connect(
        lambda name, kind, path, description, details: selected_payloads.append(
            (name, kind, path, description, details)
        )
    )
    scene.site_object_selected.connect(selected_targets.append)
    scene.clearSelection()
    workstation.setSelected(True)

    assert selected_payloads[-1][0] == "it-workstation-01"
    assert selected_payloads[-1][1] == "device"
    assert selected_targets[-1] is snapshot.incident.camps[0].buildings[0].devices[1]


def test_canvas_view_exposes_zoom_state() -> None:
    _get_app()

    snapshot = build_demo_workspace_snapshot()
    canvas = CampCanvas(snapshot.incident)

    assert canvas.objectName() == "campCanvas"
    assert canvas.zoom_factor == 1.0
    title_overlay = canvas.findChild(QLabel, "siteMapTitleOverlay")
    assert title_overlay is not None
    assert title_overlay.text() == "Site Map - Pine Gulch Incident (CA-INC-2026-041)"
    assert title_overlay.geometry().x() == 12
    assert title_overlay.geometry().y() == 12
    base_title_size = title_overlay.font().pointSizeF()
    summary_overlay = canvas.findChild(QWidget, "siteMapSummaryOverlay")
    assert summary_overlay is not None
    assert summary_overlay.geometry().x() == 12
    assert summary_overlay.geometry().top() > title_overlay.geometry().bottom()
    summary_texts = [
        label.text()
        for label in summary_overlay.findChildren(QLabel)
    ]
    assert "Base Camp" in summary_texts
    assert "1 location(s), 2 device(s)" in summary_texts
    assert "Camp LAN: 2 device(s), 1 cable(s)" in summary_texts
    assert "Inventory: 1 asset(s)" in summary_texts
    base_summary_size = summary_overlay.findChild(QLabel, "siteMapSummaryHeading").font().pointSizeF()

    canvas.zoom(2.0)

    assert canvas.zoom_factor > 1.0
    assert title_overlay.font().pointSizeF() > base_title_size
    assert summary_overlay.findChild(QLabel, "siteMapSummaryHeading").font().pointSizeF() > base_summary_size
    assert title_overlay.geometry().x() == 12
    assert title_overlay.geometry().y() == 12
    assert summary_overlay.geometry().x() == 12
    assert summary_overlay.geometry().top() > title_overlay.geometry().bottom()
    zoomed = canvas.zoom_factor

    canvas.undo()

    assert canvas.zoom_factor == 1.0
    assert title_overlay.font().pointSizeF() == base_title_size

    canvas.redo()

    assert canvas.zoom_factor == zoomed
