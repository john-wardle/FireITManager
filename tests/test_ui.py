import os
from json import loads

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDockWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QTreeWidget,
)

from fireitmanager.models.enums import BuildingType
from fireitmanager.ui.main_window import FireITMainWindow


def test_main_window_contains_expected_panels(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    window = FireITMainWindow()

    assert window.windowTitle() == "FireIT Manager"
    assert window.centralWidget() is not None
    assert window.centralWidget().objectName() == "workspaceTabs"
    workspace_tabs = window.findChild(QTabWidget, "workspaceTabs")
    assert workspace_tabs is not None
    assert workspace_tabs.count() == 4
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
    camp_name = window.findChild(QLineEdit, "campNameInput")
    building_name = window.findChild(QLineEdit, "buildingNameInput")
    building_location_name = window.findChild(QLineEdit, "buildingLocationNameInput")
    building_latitude = window.findChild(QLineEdit, "buildingLatitudeInput")
    building_longitude = window.findChild(QLineEdit, "buildingLongitudeInput")
    building_elevation = window.findChild(QLineEdit, "buildingElevationInput")
    building_notes = window.findChild(QLineEdit, "buildingNotesInput")
    building_type = window.findChild(QComboBox, "buildingTypeInput")
    assert editor_name is not None
    assert editor_number is not None
    assert editor_agency is not None
    assert editor_period is not None
    assert camp_name is not None
    assert building_name is not None
    assert building_location_name is not None
    assert building_latitude is not None
    assert building_longitude is not None
    assert building_elevation is not None
    assert building_notes is not None
    assert building_type is not None
    assert editor_name.text() == "Pine Gulch Incident"
    assert editor_number.text() == "CA-INC-2026-041"
    assert editor_agency.text() == "USFS"
    assert editor_period.text() == "Operational Period 1"
    assert camp_name.text() == "Base Camp"
    assert building_name.text() == "IT Staging"
    assert building_type.currentText() == "command_post"
    assert building_location_name.text() == ""

    incident_editor_summary = window.findChild(QLabel, "incidentEditorSummary")
    incident_editor_message = window.findChild(QLabel, "incidentEditorMessage")
    camp_editor_summary = window.findChild(QLabel, "campEditorSummary")
    camp_editor_message = window.findChild(QLabel, "campEditorMessage")
    building_editor_summary = window.findChild(QLabel, "buildingEditorSummary")
    building_editor_message = window.findChild(QLabel, "buildingEditorMessage")
    assert incident_editor_summary is not None
    assert incident_editor_message is not None
    assert camp_editor_summary is not None
    assert camp_editor_message is not None
    assert building_editor_summary is not None
    assert building_editor_message is not None
    assert incident_editor_summary.text() == "Editing Pine Gulch Incident (CA-INC-2026-041)"
    assert camp_editor_summary.text() == "Editing Base Camp for Pine Gulch Incident (CA-INC-2026-041)"
    assert building_editor_summary.text() == "Editing IT Staging (command_post) for Pine Gulch Incident (CA-INC-2026-041)"

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
    assert actions["Camp Editor"].isEnabled()
    assert actions["Building Editor"].isEnabled()
    assert actions["Canvas"].isEnabled()
    assert actions["New Incident"].isEnabled()
    assert actions["Save"].isEnabled()
    assert actions["Zoom In"].isEnabled()
    assert actions["Zoom Out"].isEnabled()
    assert actions["Center View"].isEnabled()

    actions["Camp Editor"].trigger()
    assert workspace_tabs.currentWidget().objectName() == "campEditorWidget"
    actions["Building Editor"].trigger()
    assert workspace_tabs.currentWidget().objectName() == "buildingEditorWidget"
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
    assert camp_editor_summary.text() == "Editing Base Camp for Pine Gulch Base Incident (CA-INC-2026-041)"
    explorer_subtitle = window.findChild(QLabel, "incidentExplorerSubtitle")
    assert explorer_subtitle is not None
    assert "Pine Gulch Base Incident" in explorer_subtitle.text()

    camp_name.setText("Alpha Base Camp")
    apply_camp_button = window.findChild(QPushButton, "applyCampChangesButton")
    assert apply_camp_button is not None
    apply_camp_button.click()

    assert camp_editor_message.text() == "Camp updated in memory."
    assert camp_editor_summary.text() == "Editing Alpha Base Camp for Pine Gulch Base Incident (CA-INC-2026-041)"
    explorer_tree = window.findChild(QTreeWidget, "incidentExplorerTree")
    assert explorer_tree is not None
    camps_group = explorer_tree.topLevelItem(0).child(1)
    assert camps_group is not None
    camp_item = camps_group.child(0)
    assert camp_item is not None
    assert camp_item.text(0) == "Alpha Base Camp"

    network_group = explorer_tree.topLevelItem(0).child(2)
    assert network_group is not None
    network_item = network_group.child(0)
    assert network_item is not None
    explorer_tree.setCurrentItem(network_item)
    assert name_value.text() == "Camp LAN"
    assert kind_value.text() == "network"
    assert path_value.text() == "Workspace / Camps / Alpha Base Camp / Network / Camp LAN"
    assert description_value.text() == "The active camp LAN supporting the IT staging area."
    assert "Devices: 2" in details_value.text()
    assert selection_label.text() == "Selected: Camp LAN (network)"

    building_name.setText("Staging HQ")
    building_type.setCurrentIndex(building_type.findData(BuildingType.OPERATIONS.value))
    building_location_name.setText("North Pad")
    building_latitude.setText("45.1234")
    building_longitude.setText("-118.9876")
    building_elevation.setText("5120")
    building_notes.setText("Primary IT staging location.")
    apply_building_button = window.findChild(QPushButton, "applyBuildingChangesButton")
    assert apply_building_button is not None
    apply_building_button.click()

    assert building_editor_message.text() == "Building updated in memory."
    assert building_editor_summary.text() == "Editing Staging HQ (operations) for Pine Gulch Base Incident (CA-INC-2026-041)"
    explorer_tree = window.findChild(QTreeWidget, "incidentExplorerTree")
    assert explorer_tree is not None
    camps_group = explorer_tree.topLevelItem(0).child(1)
    assert camps_group is not None
    camp_item = camps_group.child(0)
    assert camp_item is not None
    building_item = camp_item.child(0)
    assert building_item is not None
    assert building_item.text(0) == "Staging HQ"

    explorer_tree.setCurrentItem(building_item)
    assert name_value.text() == "Staging HQ"
    assert kind_value.text() == "building"
    assert path_value.text() == "Workspace / Camps / Alpha Base Camp / Staging HQ"
    assert "Location: North Pad" in details_value.text()
    assert selection_label.text() == "Selected: Staging HQ (building)"

    actions["New Incident"].trigger()
    assert "Untitled Incident" in incident_editor_summary.text()
    assert "Untitled Incident" in incident_label.text()
    assert camp_editor_summary.text() == "Editing Base Camp for Untitled Incident (no-number)"
    assert building_editor_summary.text().startswith("Editing IT Staging (command_post) for Untitled Incident (no-number)")

    save_path = tmp_path / "incident.json"
    window.save_path = save_path
    actions["Save"].trigger()
    assert save_path.exists()
    saved = loads(save_path.read_text(encoding="utf-8"))
    assert saved["incident"]["name"] == "Untitled Incident"
    assert saved["schema_version"] == 1

    window.close()
    app.quit()
