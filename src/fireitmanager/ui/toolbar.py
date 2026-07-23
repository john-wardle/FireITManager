"""Toolbar definitions for the FireIT Manager main window."""

from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QToolBar


def create_tool_bar(window: QMainWindow) -> QToolBar:
    """Create the top toolbar and wire the active canvas controls."""
    toolbar = QToolBar("Main Toolbar", window)
    toolbar.setObjectName("mainToolbar")
    toolbar.setMovable(False)

    action_groups = [
        [
            ("New Incident", True, window.create_new_incident),
            ("Open", True, window.load_workspace),
            ("Save", True, window.save_workspace),
            ("Save As", True, lambda checked=False: window.save_workspace_as()),
        ],
        [
            ("Undo", True, window.canvas.undo),
            ("Redo", True, window.canvas.redo),
        ],
        [
            ("Zoom In", True, window.canvas.zoom_in),
            ("Zoom Out", True, window.canvas.zoom_out),
            ("Center View", True, window.canvas.center_scene),
        ],
    ]

    for group_index, action_specs in enumerate(action_groups):
        if group_index > 0:
            toolbar.addSeparator()
        for text, enabled, callback in action_specs:
            action = QAction(text, window)
            action.setObjectName(text.lower().replace(" ", "_"))
            action.setToolTip(text)
            action.setEnabled(enabled)
            if callback is not None:
                action.triggered.connect(callback)
            toolbar.addAction(action)

    return toolbar
