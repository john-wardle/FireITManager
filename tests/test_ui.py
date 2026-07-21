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
    QListWidget,
    QPushButton,
    QTabWidget,
    QTreeWidget,
)

from fireitmanager.models.enums import AssetStatus, BuildingType, DeviceStatus, DeviceType
from fireitmanager.ui.main_window import FireITMainWindow


def test_main_window_contains_expected_panels(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    window = FireITMainWindow()

    assert window.windowTitle() == "FireIT Manager"
    assert window.centralWidget() is not None
    assert window.centralWidget().objectName() == "workspaceTabs"
    workspace_tabs = window.findChild(QTabWidget, "workspaceTabs")
    assert workspace_tabs is not None
    assert workspace_tabs.count() == 8
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
    asset_name = window.findChild(QLineEdit, "assetNameInput")
    asset_owner = window.findChild(QLineEdit, "assetOwnerInput")
    asset_acquisition = window.findChild(QLineEdit, "assetAcquisitionInput")
    asset_barcode = window.findChild(QLineEdit, "assetBarcodeInput")
    asset_assigned_person = window.findChild(QLineEdit, "assetAssignedPersonInput")
    asset_assigned_person_selector = window.findChild(QComboBox, "assetAssignedPersonSelectorInput")
    asset_status = window.findChild(QComboBox, "assetStatusInput")
    person_name = window.findChild(QLineEdit, "personNameInput")
    person_position = window.findChild(QLineEdit, "personPositionInput")
    person_agency = window.findChild(QLineEdit, "personAgencyInput")
    person_assigned_devices = window.findChild(QLineEdit, "personAssignedDevicesInput")
    person_device_selector = window.findChild(QComboBox, "personDeviceSelectorInput")
    person_assigned_device_list = window.findChild(QListWidget, "personAssignedDeviceList")
    building_name = window.findChild(QLineEdit, "buildingNameInput")
    building_location_name = window.findChild(QLineEdit, "buildingLocationNameInput")
    building_latitude = window.findChild(QLineEdit, "buildingLatitudeInput")
    building_longitude = window.findChild(QLineEdit, "buildingLongitudeInput")
    building_elevation = window.findChild(QLineEdit, "buildingElevationInput")
    building_notes = window.findChild(QLineEdit, "buildingNotesInput")
    building_type = window.findChild(QComboBox, "buildingTypeInput")
    device_hostname = window.findChild(QLineEdit, "deviceHostnameInput")
    device_manufacturer = window.findChild(QLineEdit, "deviceManufacturerInput")
    device_model = window.findChild(QLineEdit, "deviceModelInput")
    device_serial = window.findChild(QLineEdit, "deviceSerialInput")
    device_ip = window.findChild(QLineEdit, "deviceIpInput")
    device_mac = window.findChild(QLineEdit, "deviceMacInput")
    device_type = window.findChild(QComboBox, "deviceTypeInput")
    device_status = window.findChild(QComboBox, "deviceStatusInput")
    network_name = window.findChild(QLineEdit, "networkNameInput")
    assert editor_name is not None
    assert editor_number is not None
    assert editor_agency is not None
    assert editor_period is not None
    assert camp_name is not None
    assert asset_name is not None
    assert asset_owner is not None
    assert asset_acquisition is not None
    assert asset_barcode is not None
    assert asset_assigned_person is not None
    assert asset_assigned_person_selector is not None
    assert asset_status is not None
    assert person_name is not None
    assert person_position is not None
    assert person_agency is not None
    assert person_assigned_devices is not None
    assert person_device_selector is not None
    assert person_assigned_device_list is not None
    assert building_name is not None
    assert building_location_name is not None
    assert building_latitude is not None
    assert building_longitude is not None
    assert building_elevation is not None
    assert building_notes is not None
    assert building_type is not None
    assert device_hostname is not None
    assert device_manufacturer is not None
    assert device_model is not None
    assert device_serial is not None
    assert device_ip is not None
    assert device_mac is not None
    assert device_type is not None
    assert device_status is not None
    assert network_name is not None
    assert editor_name.text() == "Pine Gulch Incident"
    assert editor_number.text() == "CA-INC-2026-041"
    assert editor_agency.text() == "USFS"
    assert editor_period.text() == "Operational Period 1"
    assert camp_name.text() == "Base Camp"
    assert asset_name.text() == "Generator 1"
    assert asset_status.currentText() == AssetStatus.AVAILABLE.value
    assert asset_assigned_person.text() == ""
    assert person_name.text() == "Alex Morgan"
    assert person_assigned_devices.text() == ""
    assert building_name.text() == "IT Staging"
    assert device_hostname.text() == "it-router-01"
    assert device_type.currentText() == DeviceType.ROUTER.value
    assert device_status.currentText() == DeviceStatus.ONLINE.value
    assert network_name.text() == "Camp LAN"
    assert building_type.currentText() == "command_post"
    assert building_location_name.text() == ""

    incident_editor_summary = window.findChild(QLabel, "incidentEditorSummary")
    incident_editor_message = window.findChild(QLabel, "incidentEditorMessage")
    camp_editor_summary = window.findChild(QLabel, "campEditorSummary")
    camp_editor_message = window.findChild(QLabel, "campEditorMessage")
    asset_editor_summary = window.findChild(QLabel, "assetEditorSummary")
    asset_editor_message = window.findChild(QLabel, "assetEditorMessage")
    person_editor_summary = window.findChild(QLabel, "personEditorSummary")
    person_editor_message = window.findChild(QLabel, "personEditorMessage")
    building_editor_summary = window.findChild(QLabel, "buildingEditorSummary")
    building_editor_message = window.findChild(QLabel, "buildingEditorMessage")
    device_editor_summary = window.findChild(QLabel, "deviceEditorSummary")
    device_editor_message = window.findChild(QLabel, "deviceEditorMessage")
    network_editor_summary = window.findChild(QLabel, "networkEditorSummary")
    network_editor_message = window.findChild(QLabel, "networkEditorMessage")
    assert incident_editor_summary is not None
    assert incident_editor_message is not None
    assert camp_editor_summary is not None
    assert camp_editor_message is not None
    assert asset_editor_summary is not None
    assert asset_editor_message is not None
    assert person_editor_summary is not None
    assert person_editor_message is not None
    assert building_editor_summary is not None
    assert building_editor_message is not None
    assert device_editor_summary is not None
    assert device_editor_message is not None
    assert network_editor_summary is not None
    assert network_editor_message is not None
    assert incident_editor_summary.text() == "Editing Pine Gulch Incident (CA-INC-2026-041)"
    assert camp_editor_summary.text() == "Editing Base Camp for Pine Gulch Incident (CA-INC-2026-041)"
    assert asset_editor_summary.text() == "Editing Generator 1 (available) for Pine Gulch Incident (CA-INC-2026-041)"
    assert person_editor_summary.text() == "Editing Alex Morgan for Pine Gulch Incident (CA-INC-2026-041)"
    assert building_editor_summary.text() == "Editing IT Staging (command_post) for Pine Gulch Incident (CA-INC-2026-041)"
    assert device_editor_summary.text() == "Editing it-router-01 for Pine Gulch Incident (CA-INC-2026-041)"
    assert network_editor_summary.text() == "Editing Camp LAN for Pine Gulch Incident (CA-INC-2026-041)"
    assert window.validate_workspace() == []
    assert window.findChild(QLabel, "readyStatusLabel").text() == "Workspace is valid."

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
    assert actions["Asset Editor"].isEnabled()
    assert actions["Person Editor"].isEnabled()
    assert actions["Building Editor"].isEnabled()
    assert actions["Device Editor"].isEnabled()
    assert actions["Network Editor"].isEnabled()
    assert actions["Canvas"].isEnabled()
    assert actions["New Incident"].isEnabled()
    assert actions["Open"].isEnabled()
    assert actions["Save"].isEnabled()
    assert actions["Save As"].isEnabled()
    assert actions["Validate Workspace"].isEnabled()
    assert actions["About"].isEnabled()
    assert actions["Zoom In"].isEnabled()
    assert actions["Zoom Out"].isEnabled()
    assert actions["Center View"].isEnabled()

    actions["Camp Editor"].trigger()
    assert workspace_tabs.currentWidget().objectName() == "campEditorWidget"
    actions["Asset Editor"].trigger()
    assert workspace_tabs.currentWidget().objectName() == "assetEditorWidget"
    actions["Person Editor"].trigger()
    assert workspace_tabs.currentWidget().objectName() == "personEditorWidget"
    actions["Building Editor"].trigger()
    assert workspace_tabs.currentWidget().objectName() == "buildingEditorWidget"
    actions["Device Editor"].trigger()
    assert workspace_tabs.currentWidget().objectName() == "deviceEditorWidget"
    actions["Network Editor"].trigger()
    assert workspace_tabs.currentWidget().objectName() == "networkEditorWidget"
    actions["Canvas"].trigger()
    assert workspace_tabs.currentWidget().objectName() == "campCanvas"
    actions["Incident Editor"].trigger()
    assert workspace_tabs.currentWidget().objectName() == "incidentEditorWidget"
    actions["About"].trigger()
    assert window.findChild(QLabel, "readyStatusLabel").text().startswith("FireIT Manager ")

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

    asset_name.setText("Generator 2")
    asset_owner.setText("Logistics")
    asset_acquisition.setText("Assigned")
    asset_barcode.setText("BAR-001")
    asset_status.setCurrentIndex(asset_status.findData(AssetStatus.IN_USE.value))
    apply_asset_button = window.findChild(QPushButton, "applyAssetChangesButton")
    assert apply_asset_button is not None
    apply_asset_button.click()

    assert asset_editor_message.text() == "Asset updated in memory."
    assert asset_editor_summary.text() == "Editing Generator 2 (in_use) for Pine Gulch Base Incident (CA-INC-2026-041)"

    person_name.setText("Jordan Lee")
    person_position.setText("IT Support")
    person_agency.setText("State")
    person_assigned_devices.setText("it-workstation-01")
    apply_person_button = window.findChild(QPushButton, "applyPersonChangesButton")
    assert apply_person_button is not None
    apply_person_button.click()

    assert person_editor_message.text() == "Person updated in memory."
    assert person_editor_summary.text() == "Editing Jordan Lee for Pine Gulch Base Incident (CA-INC-2026-041)"
    assert person_assigned_devices.text() == "it-workstation-01"

    asset_assigned_person.setText("Jordan Lee")
    apply_asset_button.click()
    assert asset_editor_message.text() == "Asset updated in memory."
    assert asset_editor_summary.text() == "Editing Generator 2 (in_use) for Pine Gulch Base Incident (CA-INC-2026-041)"

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
    workspace_tabs.setCurrentWidget(window.canvas)
    explorer_tree.itemDoubleClicked.emit(building_item, 0)
    assert workspace_tabs.currentWidget().objectName() == "buildingEditorWidget"

    device_hostname.setText("it-workstation-01")
    device_manufacturer.setText("Dell")
    device_model.setText("Latitude 5440")
    device_serial.setText("SN-12345")
    device_ip.setText("10.0.0.10")
    device_mac.setText("AA:BB:CC:DD:EE:FF")
    device_type.setCurrentIndex(device_type.findData(DeviceType.WORKSTATION.value))
    device_status.setCurrentIndex(device_status.findData(DeviceStatus.MAINTENANCE.value))
    apply_device_button = window.findChild(QPushButton, "applyDeviceChangesButton")
    assert apply_device_button is not None
    apply_device_button.click()

    assert device_editor_message.text() == "Device updated in memory."
    assert device_editor_summary.text() == "Editing it-workstation-01 for Pine Gulch Base Incident (CA-INC-2026-041)"

    network_name.setText("Alpha LAN")
    apply_network_button = window.findChild(QPushButton, "applyNetworkChangesButton")
    assert apply_network_button is not None
    apply_network_button.click()

    assert network_editor_message.text() == "Network updated in memory."
    assert network_editor_summary.text() == "Editing Alpha LAN for Pine Gulch Base Incident (CA-INC-2026-041)"

    relation_path = tmp_path / "relations.json"
    default_save_path = tmp_path / "incident.json"
    window.save_path = relation_path
    actions["Save"].trigger()
    assert relation_path.exists()
    window.load_workspace(relation_path)
    assert asset_editor_summary.text() == "Editing Generator 2 (in_use) for Pine Gulch Base Incident (CA-INC-2026-041)"
    assert asset_assigned_person.text() == "Jordan Lee"
    assert person_editor_summary.text() == "Editing Jordan Lee for Pine Gulch Base Incident (CA-INC-2026-041)"
    assert person_assigned_devices.text() == "it-workstation-01"

    window.save_path = default_save_path
    actions["New Incident"].trigger()
    assert "Untitled Incident" in incident_editor_summary.text()
    assert "Untitled Incident" in incident_label.text()
    assert camp_editor_summary.text() == "Editing Base Camp for Untitled Incident (no-number)"
    assert building_editor_summary.text().startswith("Editing IT Staging (command_post) for Untitled Incident (no-number)")

    window.save_path = default_save_path
    actions["Save"].trigger()
    assert default_save_path.exists()
    saved = loads(default_save_path.read_text(encoding="utf-8"))
    assert saved["incident"]["name"] == "Untitled Incident"
    assert saved["schema_version"] == 1

    editor_name.setText("Loaded Incident")
    apply_button.click()
    assert "Loaded Incident" in incident_label.text()

    window.load_workspace(default_save_path)
    assert "Untitled Incident" in incident_label.text()
    assert incident_editor_summary.text() == "Editing Untitled Incident (no-number)"
    assert camp_editor_summary.text() == "Editing Base Camp for Untitled Incident (no-number)"
    assert asset_editor_summary.text() == "Editing Generator 1 (available) for Untitled Incident (no-number)"
    assert asset_assigned_person.text() == ""
    assert person_editor_summary.text() == "Editing Alex Morgan for Untitled Incident (no-number)"
    assert person_assigned_devices.text() == ""
    assert building_editor_summary.text().startswith("Editing IT Staging (command_post) for Untitled Incident (no-number)")
    assert device_editor_summary.text().startswith("Editing it-router-01 for Untitled Incident (no-number)")
    assert network_editor_summary.text().startswith("Editing Camp LAN for Untitled Incident (no-number)")

    window.close()
    app.quit()
