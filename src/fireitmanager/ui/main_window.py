"""Main application window for FireIT Manager."""

from __future__ import annotations

from pathlib import Path
from tempfile import gettempdir

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QMainWindow, QLabel, QStatusBar, QTabWidget

from fireitmanager.ui.canvas import CampCanvas
from fireitmanager.ui.camp_editor import CampEditorWidget
from fireitmanager.ui.building_editor import BuildingEditorWidget
from fireitmanager.ui.device_editor import DeviceEditorWidget
from fireitmanager.ui.docks import create_docks
from fireitmanager.ui.explorer import IncidentExplorerWidget
from fireitmanager.ui.incident_editor import IncidentEditorWidget
from fireitmanager.ui.menu import create_menu_bar
from fireitmanager.ui.network_editor import NetworkEditorWidget
from fireitmanager.ui.properties import PropertiesWidget
from fireitmanager.models.incident import Incident
from fireitmanager.ui.workspace import (
    WorkspaceNode,
    build_demo_workspace_snapshot,
    build_workspace_snapshot,
)
from fireitmanager.persistence import IncidentRepository
from fireitmanager.ui.toolbar import create_tool_bar


class FireITMainWindow(QMainWindow):
    """Application shell for the FireIT Manager desktop experience."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FireIT Manager")
        self.resize(1280, 900)
        self.workspace_snapshot = build_demo_workspace_snapshot()
        self.repository = IncidentRepository()
        self.save_path = Path(gettempdir()) / "fireitmanager" / "incident.json"
        self.load_path = self.save_path

        self._setup_menu_bar()
        self._setup_central_widget()
        self._setup_tool_bar()
        self._setup_status_bar()
        self._setup_docks()

    def _setup_menu_bar(self) -> None:
        """Create and attach the top-level menu bar."""
        self.setMenuBar(create_menu_bar(self))

    def _setup_tool_bar(self) -> None:
        """Create and attach the application toolbar."""
        self.addToolBar(create_tool_bar(self))

    def _setup_status_bar(self) -> None:
        """Create and populate the status bar with the requested labels."""
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.ready_label = QLabel("Ready", self)
        self.ready_label.setObjectName("readyStatusLabel")
        self.incident_label = QLabel("", self)
        self.incident_label.setObjectName("incidentStatusLabel")
        self.selection_label = QLabel(
            f"Selected: {self.workspace_snapshot.root.label}",
            self,
        )
        self.selection_label.setObjectName("selectionStatusLabel")
        self.operational_label = QLabel(
            "",
            self,
        )
        self.operational_label.setObjectName("operationalStatusLabel")
        self.zoom_label = QLabel("Zoom: 100%", self)
        self.zoom_label.setObjectName("zoomStatusLabel")
        self.status_bar.addPermanentWidget(self.ready_label)
        self.status_bar.addPermanentWidget(self.incident_label)
        self.status_bar.addPermanentWidget(self.selection_label)
        self.status_bar.addPermanentWidget(self.operational_label)
        self.status_bar.addPermanentWidget(self.zoom_label)
        self._sync_incident_status()

    def _setup_central_widget(self) -> None:
        """Attach the central workspace tabs to the main window."""
        self.canvas = CampCanvas()
        self.incident_editor = IncidentEditorWidget(self.workspace_snapshot.incident)
        self.camp_editor = CampEditorWidget(self.workspace_snapshot.incident)
        self.building_editor = BuildingEditorWidget(self.workspace_snapshot.incident)
        self.device_editor = DeviceEditorWidget(self.workspace_snapshot.incident)
        self.network_editor = NetworkEditorWidget(self.workspace_snapshot.incident)
        self.incident_editor.incident_updated.connect(self._handle_incident_updated)
        self.incident_editor.incident_created.connect(self._handle_incident_created)
        self.camp_editor.camp_updated.connect(self._handle_incident_updated)
        self.building_editor.building_updated.connect(self._handle_incident_updated)
        self.device_editor.device_updated.connect(self._handle_incident_updated)
        self.network_editor.network_updated.connect(self._handle_incident_updated)

        self.workspace_tabs = QTabWidget(self)
        self.workspace_tabs.setObjectName("workspaceTabs")
        self.workspace_tabs.addTab(self.incident_editor, "Incident Editor")
        self.workspace_tabs.addTab(self.camp_editor, "Camp Editor")
        self.workspace_tabs.addTab(self.building_editor, "Building Editor")
        self.workspace_tabs.addTab(self.device_editor, "Device Editor")
        self.workspace_tabs.addTab(self.network_editor, "Network Editor")
        self.workspace_tabs.addTab(self.canvas, "Canvas")
        self.workspace_tabs.setCurrentIndex(0)
        self.setCentralWidget(self.workspace_tabs)

    def _setup_docks(self) -> None:
        """Create and place the explorer and properties docks."""
        left_dock, right_dock = create_docks(self, self.workspace_snapshot)
        self.addDockWidget(Qt.LeftDockWidgetArea, left_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, right_dock)

        self.explorer_widget = left_dock.widget()
        self.properties_widget = right_dock.widget()

        if isinstance(self.explorer_widget, IncidentExplorerWidget) and isinstance(
            self.properties_widget, PropertiesWidget
        ):
            self.explorer_widget.selection_changed.connect(self.properties_widget.set_details)
            self.explorer_widget.selection_changed.connect(self._update_selection_status)
            self._sync_current_selection()
        self.canvas.zoom_changed.connect(self._update_zoom_status)

    def show_canvas(self) -> None:
        """Switch the workspace to the canvas tab."""
        self.workspace_tabs.setCurrentWidget(self.canvas)

    def show_incident_editor(self) -> None:
        """Switch the workspace to the incident editor tab."""
        self.workspace_tabs.setCurrentWidget(self.incident_editor)

    def show_camp_editor(self) -> None:
        """Switch the workspace to the camp editor tab."""
        self.workspace_tabs.setCurrentWidget(self.camp_editor)

    def show_building_editor(self) -> None:
        """Switch the workspace to the building editor tab."""
        self.workspace_tabs.setCurrentWidget(self.building_editor)

    def show_device_editor(self) -> None:
        """Switch the workspace to the device editor tab."""
        self.workspace_tabs.setCurrentWidget(self.device_editor)

    def show_network_editor(self) -> None:
        """Switch the workspace to the network editor tab."""
        self.workspace_tabs.setCurrentWidget(self.network_editor)

    def create_new_incident(self) -> None:
        """Start a new incident record for manual entry."""
        self.incident_editor.create_new_incident()

    def load_workspace(self, path: str | Path | None = None) -> None:
        """Load an incident graph from disk into the active workspace."""
        target = Path(path) if path is not None else self._prompt_for_load_path()
        if target is None:
            return

        incident = self.repository.load(target)
        self._reset_workspace(incident)
        self.load_path = target
        self.save_path = target
        self.ready_label.setText(f"Loaded from {target}")

    def save_workspace(self) -> None:
        """Persist the active incident graph to disk."""
        saved_path = self.repository.save(self.workspace_snapshot.incident, self.save_path)
        self.ready_label.setText(f"Saved to {saved_path}")

    def _prompt_for_load_path(self) -> Path | None:
        """Show a file picker for incident files."""
        selected_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Incident",
            str(self.load_path.parent),
            "Incident JSON (*.json);;All Files (*)",
        )
        if not selected_path:
            return None
        return Path(selected_path)

    def _sync_incident_status(self) -> None:
        """Update the incident status labels from the loaded incident."""
        self.incident_label.setText(
            f"Incident: {self.workspace_snapshot.incident.summary()}"
        )
        self.operational_label.setText(
            f"OP: {self.workspace_snapshot.incident.operational_period}"
        )

    def _sync_current_selection(self) -> None:
        """Push the current explorer item into the property panel and status bar."""
        current = self.explorer_widget.tree.currentItem()
        if current is None:
            return
        node = current.data(0, Qt.UserRole)
        if not isinstance(node, WorkspaceNode):
            return
        details = "\n".join(f"{key}: {value}" for key, value in node.details.items())
        self.properties_widget.set_details(
            node.label,
            node.kind,
            node.path,
            node.description,
            details,
        )
        self._update_selection_status(
            node.label,
            node.kind,
            node.path,
            node.description,
            details,
        )

    def _handle_incident_updated(self, incident: object) -> None:
        """Refresh the workspace when the incident editor applies changes."""
        if not isinstance(incident, type(self.workspace_snapshot.incident)):
            return
        self._sync_workspace(incident, preserve_messages=True)

    def _handle_incident_created(self, incident: object) -> None:
        """Refresh the workspace when the incident editor creates a new incident."""
        if not isinstance(incident, type(self.workspace_snapshot.incident)):
            return
        self._reset_workspace(incident)

    def _reset_workspace(self, incident: Incident) -> None:
        """Bind the workspace widgets to a new incident model and reset messages."""
        self.workspace_snapshot = build_workspace_snapshot(incident)
        self.incident_editor.load_incident(incident)
        self.camp_editor.bind_incident(incident)
        self.building_editor.bind_incident(incident)
        self.device_editor.bind_incident(incident)
        self.network_editor.bind_incident(incident)
        self.incident_editor.sync_from_model()
        self.camp_editor.sync_from_model()
        self.building_editor.sync_from_model()
        self.device_editor.sync_from_model()
        self.network_editor.sync_from_model()
        self._sync_incident_status()
        self.explorer_widget.set_snapshot(self.workspace_snapshot)
        self._sync_current_selection()

    def _sync_workspace(self, incident: Incident, *, preserve_messages: bool) -> None:
        """Rebuild the snapshot while preserving editor messages when requested."""
        self.workspace_snapshot = build_workspace_snapshot(incident)
        if preserve_messages:
            self.incident_editor.sync_from_model()
        else:
            self.incident_editor.load_incident(incident)
        self.camp_editor.sync_from_model()
        self.building_editor.sync_from_model()
        self.device_editor.sync_from_model()
        self.network_editor.sync_from_model()
        self._sync_incident_status()
        self.explorer_widget.set_snapshot(self.workspace_snapshot)
        self._sync_current_selection()

    def _update_zoom_status(self, zoom_factor: float) -> None:
        """Reflect the current canvas zoom level in the status bar."""
        self.zoom_label.setText(f"Zoom: {zoom_factor * 100:.0f}%")

    def _update_selection_status(
        self,
        name: str,
        kind: str,
        path: str,
        description: str,
        details: str,
    ) -> None:
        """Reflect the active explorer selection in the status bar."""
        del path, description, details
        self.selection_label.setText(f"Selected: {name} ({kind})")
