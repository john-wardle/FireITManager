"""Main application window for FireIT Manager."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from tempfile import gettempdir

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QMainWindow, QLabel, QMenu, QStatusBar

from fireitmanager.ui.canvas import CampCanvas
from fireitmanager.ui.camp_editor import CampEditorWidget
from fireitmanager.ui.asset_editor import AssetEditorWidget
from fireitmanager.ui.building_editor import BuildingEditorWidget
from fireitmanager.ui.device_editor import DeviceEditorWidget
from fireitmanager.ui.docks import create_docks
from fireitmanager.ui.explorer import IncidentExplorerWidget
from fireitmanager.ui.incident_editor import IncidentEditorWidget
from fireitmanager.ui.menu import create_menu_bar
from fireitmanager.ui.network_editor import NetworkEditorWidget
from fireitmanager.ui.person_editor import PersonEditorWidget
from fireitmanager.ui.properties import PropertiesWidget
from fireitmanager.models.incident import Incident
from fireitmanager.core import validate_incident_workspace
from fireitmanager.ui.workspace import (
    WorkspaceNode,
    build_demo_workspace_snapshot,
    build_workspace_snapshot,
)
from fireitmanager.ui.workspace_tabs import FolderWorkspaceTabs, WorkspaceActionPage
from fireitmanager.persistence import IncidentRepository
from fireitmanager.reports import (
    write_incident_summary_csv_report,
    write_incident_summary_html_report,
    write_incident_summary_report,
)
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
        self.report_path = Path(gettempdir()) / "fireitmanager" / "incident-summary.md"
        self.report_csv_path = self.report_path.with_suffix(".csv")
        self.report_html_path = self.report_path.with_suffix(".html")
        self.load_dialog_dir = self.load_path.parent
        self.save_dialog_dir = self.save_path.parent
        self.report_dialog_dir = self.report_path.parent
        self.report_csv_dialog_dir = self.report_csv_path.parent
        self.report_html_dialog_dir = self.report_html_path.parent
        self.recent_paths: list[Path] = []
        self.max_recent_paths = 5
        self.recent_files_menu: QMenu | None = None

        self._setup_central_widget()
        self._setup_menu_bar()
        self._setup_tool_bar()
        self._setup_status_bar()
        self._setup_docks()

    def _setup_menu_bar(self) -> None:
        """Create and attach the top-level menu bar."""
        self.setMenuBar(create_menu_bar(self))
        self._refresh_recent_files_menu()

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
        self.canvas = CampCanvas(self.workspace_snapshot.incident)
        self.incident_editor = IncidentEditorWidget(self.workspace_snapshot.incident)
        self.camp_editor = CampEditorWidget(self.workspace_snapshot.incident)
        self.asset_editor = AssetEditorWidget(self.workspace_snapshot.incident)
        self.person_editor = PersonEditorWidget(self.workspace_snapshot.incident)
        self.building_editor = BuildingEditorWidget(self.workspace_snapshot.incident)
        self.device_editor = DeviceEditorWidget(self.workspace_snapshot.incident)
        self.network_editor = NetworkEditorWidget(self.workspace_snapshot.incident)
        self.incident_editor.incident_updated.connect(self._handle_incident_updated)
        self.incident_editor.incident_created.connect(self._handle_incident_created)
        self.camp_editor.camp_updated.connect(self._handle_incident_updated)
        self.asset_editor.asset_updated.connect(self._handle_incident_updated)
        self.person_editor.person_updated.connect(self._handle_incident_updated)
        self.building_editor.building_updated.connect(self._handle_incident_updated)
        self.device_editor.device_updated.connect(self._handle_incident_updated)
        self.network_editor.network_updated.connect(self._handle_incident_updated)

        self.reports_page = WorkspaceActionPage(
            "Reports",
            "Export incident summaries from the active workspace.",
            [
                ("Export Summary Markdown", self.export_incident_summary),
                ("Export Summary CSV", self.export_incident_summary_csv),
                ("Export Summary HTML", self.export_incident_summary_html),
            ],
            self,
        )
        self.validation_page = WorkspaceActionPage(
            "Validation",
            "Run workspace checks before saving or exporting incident data.",
            [("Validate Workspace", self.validate_workspace)],
            self,
        )

        self.workspace_tabs = FolderWorkspaceTabs(self)
        self.workspace_tabs.add_folder(
            "Incident",
            [
                ("Details", self.incident_editor),
                ("Personnel", self.person_editor),
            ],
        )
        self.workspace_tabs.add_folder(
            "Camp Ops",
            [
                ("Camps", self.camp_editor),
                ("Buildings", self.building_editor),
            ],
        )
        self.workspace_tabs.add_folder(
            "Inventory",
            [
                ("Assets", self.asset_editor),
                ("Devices", self.device_editor),
            ],
        )
        self.workspace_tabs.add_folder(
            "Network",
            [
                ("Site Map", self.canvas),
                ("Networks", self.network_editor),
            ],
        )
        self.workspace_tabs.add_folder(
            "Outputs",
            [
                ("Reports", self.reports_page),
                ("Validation", self.validation_page),
            ],
        )
        self.workspace_tabs.setCurrentWidget(self.incident_editor)
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
            self.canvas.site_item_selected.connect(self.properties_widget.set_details)
            self.canvas.site_item_selected.connect(self._update_selection_status)
            self.explorer_widget.tree.itemDoubleClicked.connect(self._activate_editor_for_item)
            self._sync_current_selection()
        self.canvas.zoom_changed.connect(self._update_zoom_status)

    def show_canvas(self) -> None:
        """Switch the workspace to the site map tab."""
        self.workspace_tabs.setCurrentWidget(self.canvas)

    def show_incident_editor(self) -> None:
        """Switch the workspace to the incident editor tab."""
        self.workspace_tabs.setCurrentWidget(self.incident_editor)

    def show_camp_editor(self) -> None:
        """Switch the workspace to the camp editor tab."""
        self.workspace_tabs.setCurrentWidget(self.camp_editor)

    def show_asset_editor(self) -> None:
        """Switch the workspace to the asset editor tab."""
        self.workspace_tabs.setCurrentWidget(self.asset_editor)

    def show_person_editor(self) -> None:
        """Switch the workspace to the person editor tab."""
        self.workspace_tabs.setCurrentWidget(self.person_editor)

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
        self._record_recent_path(target)
        self._reset_workspace(incident)
        self.load_path = target
        self.save_path = target
        self.load_dialog_dir = target.parent
        self.ready_label.setText(f"Loaded from {target}")

    def save_workspace(self) -> Path:
        """Persist the active incident graph to disk."""
        saved_path = self.repository.save(self.workspace_snapshot.incident, self.save_path)
        self.load_path = saved_path
        self._record_recent_path(saved_path)
        self.ready_label.setText(f"Saved to {saved_path}")
        return saved_path

    def save_workspace_as(self, path: str | Path | None = None) -> Path | None:
        """Persist the active incident graph to a chosen path."""
        target = Path(path) if path is not None else self._prompt_for_save_path()
        if target is None:
            return None

        saved_path = self.repository.save(self.workspace_snapshot.incident, target)
        self.save_path = saved_path
        self.load_path = saved_path
        self.save_dialog_dir = saved_path.parent
        self._record_recent_path(saved_path)
        self.ready_label.setText(f"Saved to {saved_path}")
        return saved_path

    def export_incident_summary(self, path: str | Path | None = None) -> Path | None:
        """Export a markdown summary report for the active incident."""
        target = Path(path) if path is not None else self._prompt_for_report_path()
        if target is None:
            return None
        saved_path = write_incident_summary_report(self.workspace_snapshot.incident, target)
        self.report_path = saved_path
        self.report_dialog_dir = saved_path.parent
        self.ready_label.setText(f"Report written to {saved_path}")
        return saved_path

    def export_incident_summary_csv(self, path: str | Path | None = None) -> Path | None:
        """Export a CSV summary report for the active incident."""
        target = Path(path) if path is not None else self._prompt_for_report_csv_path()
        if target is None:
            return None
        saved_path = write_incident_summary_csv_report(self.workspace_snapshot.incident, target)
        self.report_csv_path = saved_path
        self.report_csv_dialog_dir = saved_path.parent
        self.ready_label.setText(f"CSV report written to {saved_path}")
        return saved_path

    def export_incident_summary_html(self, path: str | Path | None = None) -> Path | None:
        """Export an HTML summary report for the active incident."""
        target = Path(path) if path is not None else self._prompt_for_report_html_path()
        if target is None:
            return None
        saved_path = write_incident_summary_html_report(self.workspace_snapshot.incident, target)
        self.report_html_path = saved_path
        self.report_html_dialog_dir = saved_path.parent
        self.ready_label.setText(f"HTML report written to {saved_path}")
        return saved_path

    def validate_workspace(self) -> list[str]:
        """Validate the active incident workspace and show the result."""
        issues = validate_incident_workspace(self.workspace_snapshot.incident)
        if issues:
            self.ready_label.setText(f"Validation found {len(issues)} issue(s).")
        else:
            self.ready_label.setText("Workspace is valid.")
        return issues

    def show_about(self) -> None:
        """Show lightweight about information in the status bar."""
        try:
            package_version = version("fireitmanager")
        except PackageNotFoundError:
            package_version = "unknown"
        self.ready_label.setText(f"FireIT Manager {package_version}")

    def _prompt_for_load_path(self) -> Path | None:
        """Show a file picker for incident files."""
        selected_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Incident",
            str(self.load_dialog_dir),
            "Incident JSON (*.json);;All Files (*)",
        )
        if not selected_path:
            return None
        return Path(selected_path)

    def _prompt_for_save_path(self) -> Path | None:
        """Show a file picker for saving incident files."""
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Incident As",
            str(self.save_dialog_dir),
            "Incident JSON (*.json);;All Files (*)",
        )
        if not selected_path:
            return None
        return Path(selected_path)

    def _prompt_for_report_path(self) -> Path | None:
        """Show a file picker for markdown report exports."""
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Incident Summary",
            str(self.report_dialog_dir / self.report_path.name),
            "Markdown (*.md);;All Files (*)",
        )
        if not selected_path:
            return None
        return Path(selected_path)

    def _prompt_for_report_csv_path(self) -> Path | None:
        """Show a file picker for CSV report exports."""
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Incident Summary CSV",
            str(self.report_csv_dialog_dir / self.report_csv_path.name),
            "CSV (*.csv);;All Files (*)",
        )
        if not selected_path:
            return None
        return Path(selected_path)

    def _prompt_for_report_html_path(self) -> Path | None:
        """Show a file picker for HTML report exports."""
        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Incident Summary HTML",
            str(self.report_html_dialog_dir / self.report_html_path.name),
            "HTML (*.html);;All Files (*)",
        )
        if not selected_path:
            return None
        return Path(selected_path)

    def _register_recent_files_menu(self, menu: QMenu) -> None:
        """Attach the recent-files submenu created by the menu builder."""
        self.recent_files_menu = menu
        self._refresh_recent_files_menu()

    def _refresh_recent_files_menu(self) -> None:
        """Rebuild the recent-files submenu from the current MRU list."""
        if self.recent_files_menu is None:
            return

        self.recent_files_menu.clear()
        if not self.recent_paths:
            placeholder = QAction("No recent files", self)
            placeholder.setEnabled(False)
            self.recent_files_menu.addAction(placeholder)
            return

        for recent_path in self.recent_paths:
            action = QAction(recent_path.name, self)
            action.setToolTip(str(recent_path))
            action.triggered.connect(
                lambda checked=False, path=recent_path: self.open_recent_workspace(path)
            )
            self.recent_files_menu.addAction(action)

    def open_recent_workspace(self, path: str | Path) -> None:
        """Open a workspace from the recent-files list."""
        target = Path(path)
        if not target.exists():
            if target in self.recent_paths:
                self.recent_paths.remove(target)
                self._refresh_recent_files_menu()
            self.ready_label.setText(f"Recent file missing: {target}")
            return
        self.load_workspace(target)

    def _record_recent_path(self, path: Path) -> None:
        """Promote a file path into the MRU list."""
        resolved = Path(path)
        self.recent_paths = [existing for existing in self.recent_paths if existing != resolved]
        self.recent_paths.insert(0, resolved)
        self.recent_paths = self.recent_paths[: self.max_recent_paths]
        self._refresh_recent_files_menu()

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
        self.asset_editor.bind_incident(incident)
        self.person_editor.bind_incident(incident)
        self.building_editor.bind_incident(incident)
        self.device_editor.bind_incident(incident)
        self.network_editor.bind_incident(incident)
        self.incident_editor.sync_from_model()
        self.camp_editor.sync_from_model()
        self.asset_editor.sync_from_model()
        self.person_editor.sync_from_model()
        self.building_editor.sync_from_model()
        self.device_editor.sync_from_model()
        self.network_editor.sync_from_model()
        self.canvas.load_incident(incident)
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
        self.asset_editor.sync_from_model()
        self.person_editor.sync_from_model()
        self.building_editor.sync_from_model()
        self.device_editor.sync_from_model()
        self.network_editor.sync_from_model()
        self.canvas.load_incident(incident)
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

    def _activate_editor_for_item(self, item, column: int) -> None:
        """Switch to the editor tab that matches the double-clicked explorer node."""
        del column
        node = item.data(0, Qt.UserRole)
        if not isinstance(node, WorkspaceNode):
            return

        tab_map = {
            "incident": self.incident_editor,
            "camp": self.camp_editor,
            "asset": self.asset_editor,
            "person": self.person_editor,
            "building": self.building_editor,
            "device": self.device_editor,
            "network": self.network_editor,
        }
        editor = tab_map.get(node.kind)
        if editor is not None:
            self.workspace_tabs.setCurrentWidget(editor)
