import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QLineEdit, QListWidget, QPushButton

from fireitmanager.ui.main_window import FireITMainWindow


def test_asset_and_person_relationship_editors_support_picker_flows() -> None:
    app = QApplication.instance() or QApplication([])
    window = FireITMainWindow()

    asset_person_input = window.findChild(QLineEdit, "assetAssignedPersonInput")
    asset_person_selector = window.findChild(QComboBox, "assetAssignedPersonSelectorInput")
    asset_assign_button = window.findChild(QPushButton, "assignSelectedAssetPersonButton")
    asset_clear_button = window.findChild(QPushButton, "clearAssetAssignedPersonButton")

    person_device_input = window.findChild(QLineEdit, "personAssignedDevicesInput")
    person_device_selector = window.findChild(QComboBox, "personDeviceSelectorInput")
    person_add_button = window.findChild(QPushButton, "addPersonDeviceButton")
    person_remove_button = window.findChild(QPushButton, "removePersonDeviceButton")
    person_device_list = window.findChild(QListWidget, "personAssignedDeviceList")

    asset_summary = window.findChild(QLabel, "assetEditorSummary")
    person_summary = window.findChild(QLabel, "personEditorSummary")

    assert asset_person_input is not None
    assert asset_person_selector is not None
    assert asset_assign_button is not None
    assert asset_clear_button is not None
    assert person_device_input is not None
    assert person_device_selector is not None
    assert person_add_button is not None
    assert person_remove_button is not None
    assert person_device_list is not None
    assert asset_summary is not None
    assert person_summary is not None

    asset_selector_index = asset_person_selector.findText("Alex Morgan")
    assert asset_selector_index >= 0
    asset_person_selector.setCurrentIndex(asset_selector_index)
    asset_assign_button.click()
    assert asset_person_input.text() == "Alex Morgan"
    apply_asset_button = window.findChild(QPushButton, "applyAssetChangesButton")
    assert apply_asset_button is not None
    apply_asset_button.click()
    assert window.workspace_snapshot.incident.assets[0].assigned_person is not None
    assert window.workspace_snapshot.incident.assets[0].assigned_person.name == "Alex Morgan"

    asset_clear_button.click()
    assert asset_person_input.text() == ""
    assert window.workspace_snapshot.incident.assets[0].assigned_person is None

    person_selector_index = person_device_selector.findText("it-router-01 (IT Staging)")
    assert person_selector_index >= 0
    person_device_selector.setCurrentIndex(person_selector_index)
    person_add_button.click()
    assert person_device_input.text() == "it-router-01"
    assert person_device_list.count() == 1
    assert person_device_list.item(0).text().startswith("it-router-01")

    selected_items = person_device_list.selectedItems()
    if not selected_items:
        person_device_list.setCurrentRow(0)
    person_remove_button.click()
    assert person_device_input.text() == ""
    assert person_device_list.count() == 0
    assert "Alex Morgan" in person_summary.text()

    window.close()
    app.quit()
