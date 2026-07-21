"""Toolbar definitions for the FireIT Manager main window."""

from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QToolBar


def create_tool_bar(window: QMainWindow) -> QToolBar:
    """Create the top toolbar and wire the active canvas controls."""
    toolbar = QToolBar("Main Toolbar", window)
    toolbar.setMovable(False)

    action_specs = [
        ("New Incident", False, None),
        ("Open", False, None),
        ("Save", False, None),
        ("Undo", False, None),
        ("Redo", False, None),
        ("Incident Editor", True, window.show_incident_editor),
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
