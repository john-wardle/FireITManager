import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QTreeWidget,
)

from fireitmanager.ui.main_window import FireITMainWindow


def test_main_window_contains_expected_panels() -> None:
    app = QApplication.instance() or QApplication([])
    window = FireITMainWindow()

    assert window.windowTitle() == "FireIT Manager"
    assert window.centralWidget() is not None
    assert window.centralWidget().objectName() == "workspaceTabs"
    workspace_tabs = window.findChild(QTabWidget, "workspaceTabs")
    assert workspace_tabs is not None
    assert workspace_tabs.count() == 2
    assert workspace_tabs.currentWidget().objectName() == "incidentEditorWidget"

    dock_titles = {dock.windowTitle() for dock in window.findChildren(QDockWidget)}
    assert "Incident Explorer" in dock_titles
    assert "Properties" in dock_titles

    explorer_tree = window.findChild(QTreeWidget, "incidentExplorerTree")
    assert explorer_tree is not None
    assert explorer_tree.topLevelItemCount() == 1
    workspace = explorer_tree.topLevelItem(0)
    assert workspace is not None
    assert workspace.text(0) == "Workspace"
    assert workspace.childCount() == 5

    properties_widget = window.findChild(QDockWidget, "propertiesDock")
    assert properties_widget is not None
    properties_content = properties_widget.widget()
    assert properties_content is not None
    assert properties_content.objectName() == "propertiesWidget"

    name_value = properties_content.findChild(QLabel, "propertiesNameValue")
    kind_value = properties_content.findChild(QLabel, "propertiesKindValue")
    path_value = properties_content.findChild(QLabel, "propertiesPathValue")
    description_value = properties_content.findChild(QLabel, "propertiesDescriptionValue")
    details_value = properties_content.findChild(QLabel, "propertiesDetailsValue")
    assert name_value is not None
    assert kind_value is not None
    assert path_value is not None
    assert description_value is not None
    assert details_value is not None
    assert name_value.text() == "Workspace"
    assert kind_value.text() == "workspace"
    assert path_value.text() == "Workspace"
    assert "Loaded incident workspace" in description_value.text()
    assert "Incident:" in details_value.text()

    editor_name = window.findChild(QLineEdit, "incidentNameInput")
    editor_number = window.findChild(QLineEdit, "incidentNumberInput")
    editor_agency = window.findChild(QLineEdit, "incidentAgencyInput")
    editor_period = window.findChild(QLineEdit, "operationalPeriodInput")
    assert editor_name is not None
    assert editor_number is not None
    assert editor_agency is not None
    assert editor_period is not None
    assert editor_name.text() == "Pine Gulch Incident"
    assert editor_number.text() == "CA-INC-2026-041"
    assert editor_agency.text() == "USFS"
    assert editor_period.text() == "Operational Period 1"

    incident_editor_summary = window.findChild(QLabel, "incidentEditorSummary")
    incident_editor_message = window.findChild(QLabel, "incidentEditorMessage")
    assert incident_editor_summary is not None
    assert incident_editor_message is not None
    assert incident_editor_summary.text() == "Editing Pine Gulch Incident (CA-INC-2026-041)"

    zoom_label = window.findChild(QLabel, "zoomStatusLabel")
    assert zoom_label is not None
    assert zoom_label.text() == "Zoom: 100%"
    incident_label = window.findChild(QLabel, "incidentStatusLabel")
    selection_label = window.findChild(QLabel, "selectionStatusLabel")
    operational_label = window.findChild(QLabel, "operationalStatusLabel")
    assert incident_label is not None
    assert selection_label is not None
    assert operational_label is not None
    assert "Pine Gulch Incident" in incident_label.text()
    assert selection_label.text() == "Selected: Workspace (workspace)"
    assert operational_label.text() == "OP: Operational Period 1"

    actions = {action.text(): action for action in window.findChildren(QAction)}
    assert actions["Incident Editor"].isEnabled()
    assert actions["Canvas"].isEnabled()
    assert actions["Zoom In"].isEnabled()
    assert actions["Zoom Out"].isEnabled()
    assert actions["Center View"].isEnabled()

    actions["Canvas"].trigger()
    assert workspace_tabs.currentWidget().objectName() == "campCanvas"
    actions["Incident Editor"].trigger()
    assert workspace_tabs.currentWidget().objectName() == "incidentEditorWidget"

    current_zoom = window.canvas.zoom_factor
    actions["Zoom In"].trigger()
    assert window.canvas.zoom_factor > current_zoom
    assert zoom_label.text() == "Zoom: 115%"

    editor_name.setText("Pine Gulch Base Incident")
    editor_period.setText("Operational Period 2")
    apply_button = window.findChild(QPushButton, "applyIncidentChangesButton")
    assert apply_button is not None
    apply_button.click()

    assert incident_editor_message.text() == "Incident updated in memory."
    assert incident_editor_summary.text() == "Editing Pine Gulch Base Incident (CA-INC-2026-041)"
    assert "Pine Gulch Base Incident" in incident_label.text()
    assert operational_label.text() == "OP: Operational Period 2"
    explorer_subtitle = window.findChild(QLabel, "incidentExplorerSubtitle")
    assert explorer_subtitle is not None
    assert "Pine Gulch Base Incident" in explorer_subtitle.text()

    network_group = explorer_tree.topLevelItem(0).child(2)
    assert network_group is not None
    network_item = network_group.child(0)
    assert network_item is not None
    explorer_tree.setCurrentItem(network_item)
    assert name_value.text() == "Camp LAN"
    assert kind_value.text() == "network"
    assert path_value.text() == "Workspace / Camps / Base Camp / Network / Camp LAN"
    assert description_value.text() == "The active camp LAN supporting the IT staging area."
    assert "Devices: 2" in details_value.text()
    assert selection_label.text() == "Selected: Camp LAN (network)"

    window.close()
    app.quit()
