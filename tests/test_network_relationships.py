import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QLineEdit, QListWidget, QPushButton

from fireitmanager.ui.main_window import FireITMainWindow


def test_network_editor_adds_and_removes_device_membership() -> None:
    app = QApplication.instance() or QApplication([])
    window = FireITMainWindow()

    new_device_button = window.findChild(QPushButton, "newDeviceButton")
    device_name_input = window.findChild(QLineEdit, "deviceHostnameInput")
    apply_device_button = window.findChild(QPushButton, "applyDeviceChangesButton")
    device_networks = window.findChild(QLabel, "deviceNetworksValue")
    network_selector = window.findChild(QComboBox, "networkDeviceSelectorInput")
    network_list = window.findChild(QListWidget, "networkDeviceList")
    add_button = window.findChild(QPushButton, "addNetworkDeviceButton")
    remove_button = window.findChild(QPushButton, "removeNetworkDeviceButton")

    assert new_device_button is not None
    assert device_name_input is not None
    assert apply_device_button is not None
    assert device_networks is not None
    assert network_selector is not None
    assert network_list is not None
    assert add_button is not None
    assert remove_button is not None

    new_device_button.click()
    device_name_input.setText("it-switch-02")
    apply_device_button.click()

    selector_index = network_selector.findText("it-switch-02 (IT Staging)")
    assert selector_index >= 0
    network_selector.setCurrentIndex(selector_index)

    add_button.click()
    assert network_list.count() == 3
    assert any("it-switch-02" in network_list.item(index).text() for index in range(network_list.count()))
    assert device_networks.text() == "Camp LAN"

    matched_items = network_list.findItems("it-switch-02 (IT Staging)", Qt.MatchFlag.MatchExactly)
    assert len(matched_items) == 1
    network_list.setCurrentItem(matched_items[0])
    remove_button.click()

    assert network_list.count() == 2
    assert device_networks.text() == "Unassigned"

    window.close()
    app.quit()
