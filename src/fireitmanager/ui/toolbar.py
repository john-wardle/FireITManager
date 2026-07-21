"""Toolbar definitions for the FireIT Manager main window."""

from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QToolBar


def create_tool_bar(window: QMainWindow) -> QToolBar:
    """Create the top toolbar and wire the active canvas controls."""
    toolbar = QToolBar("Main Toolbar", window)
    toolbar.setMovable(False)

    action_specs = [
        ("New Incident", True, window.create_new_incident),
        ("Open", True, window.load_workspace),
        ("Save", True, window.save_workspace),
        ("Save As", True, lambda checked=False: window.save_workspace_as()),
        ("Undo", True, window.canvas.undo),
        ("Redo", True, window.canvas.redo),
        ("Incident Editor", True, window.show_incident_editor),
        ("Camp Editor", True, window.show_camp_editor),
        ("Asset Editor", True, window.show_asset_editor),
        ("Person Editor", True, window.show_person_editor),
        ("Building Editor", True, window.show_building_editor),
        ("Device Editor", True, window.show_device_editor),
        ("Network Editor", True, window.show_network_editor),
        ("Canvas", True, window.show_canvas),
        ("Zoom In", True, window.canvas.zoom_in),
        ("Zoom Out", True, window.canvas.zoom_out),
        ("Center View", True, window.canvas.center_scene),
    ]

    for text, enabled, callback in action_specs:
        action = QAction(text, window)
        action.setObjectName(text.lower().replace(" ", "_"))
        action.setToolTip(text)
        action.setEnabled(enabled)
        if callback is not None:
            action.triggered.connect(callback)
        toolbar.addAction(action)

    return toolbar
