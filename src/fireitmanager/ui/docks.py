"""Dock widgets for the main FireIT Manager workspace."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QMainWindow

from fireitmanager.ui.explorer import IncidentExplorerWidget
from fireitmanager.ui.properties import PropertiesWidget
from fireitmanager.ui.workspace import WorkspaceSnapshot


def create_docks(
    window: QMainWindow,
    snapshot: WorkspaceSnapshot,
) -> tuple[QDockWidget, QDockWidget]:
    """Create the incident explorer and properties dock widgets."""
    left_dock = QDockWidget("Incident Explorer", window)
    left_dock.setObjectName("incidentExplorerDock")
    left_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
    left_dock.setWidget(IncidentExplorerWidget(snapshot, left_dock))

    right_dock = QDockWidget("Properties", window)
    right_dock.setObjectName("propertiesDock")
    right_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
    right_dock.setWidget(PropertiesWidget(right_dock))

    return left_dock, right_dock
