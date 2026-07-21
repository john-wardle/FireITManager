"""Device editor widget for the FireIT Manager workspace."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from fireitmanager.models.building import Building
from fireitmanager.models.device import Device
from fireitmanager.models.enums import DeviceStatus, DeviceType
from fireitmanager.models.incident import Incident


class DeviceEditorWidget(QWidget):
    """Manual entry form for the primary device in the active building."""

    device_updated = Signal(object)

    def __init__(self, incident: Incident, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("deviceEditorWidget")
        self._incident = incident
        self._building = self._ensure_building()
        self._device = self._ensure_device()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        title = QLabel("Device Editor", self)
        title.setObjectName("deviceEditorTitle")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")

        self.summary_label = QLabel("", self)
        self.summary_label.setObjectName("deviceEditorSummary")
        self.summary_label.setWordWrap(True)

        form = QFormLayout()
        self.hostname_input = QLineEdit(self)
        self.hostname_input.setObjectName("deviceHostnameInput")
        self.manufacturer_input = QLineEdit(self)
        self.manufacturer_input.setObjectName("deviceManufacturerInput")
        self.model_input = QLineEdit(self)
        self.model_input.setObjectName("deviceModelInput")
        self.serial_input = QLineEdit(self)
        self.serial_input.setObjectName("deviceSerialInput")
        self.ip_input = QLineEdit(self)
        self.ip_input.setObjectName("deviceIpInput")
        self.mac_input = QLineEdit(self)
        self.mac_input.setObjectName("deviceMacInput")

        self.type_input = QComboBox(self)
        self.type_input.setObjectName("deviceTypeInput")
        for device_type in DeviceType:
            self.type_input.addItem(device_type.value, device_type.value)

        self.status_input = QComboBox(self)
        self.status_input.setObjectName("deviceStatusInput")
        for status in DeviceStatus:
            self.status_input.addItem(status.value, status.value)

        self.networks_value = QLabel("", self)
        self.networks_value.setObjectName("deviceNetworksValue")
        self.networks_value.setWordWrap(True)

        form.addRow("Hostname", self.hostname_input)
        form.addRow("Manufacturer", self.manufacturer_input)
        form.addRow("Model", self.model_input)
        form.addRow("Serial Number", self.serial_input)
        form.addRow("IP Address", self.ip_input)
        form.addRow("MAC Address", self.mac_input)
        form.addRow("Device Type", self.type_input)
        form.addRow("Status", self.status_input)
        form.addRow("Networks", self.networks_value)

        self.message_label = QLabel("", self)
        self.message_label.setObjectName("deviceEditorMessage")
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: #7c3aed;")

        button_row = QHBoxLayout()
        self.apply_button = QPushButton("Apply Changes", self)
        self.apply_button.setObjectName("applyDeviceChangesButton")
        self.reset_button = QPushButton("Reset", self)
        self.reset_button.setObjectName("resetDeviceButton")
        self.new_button = QPushButton("New Device", self)
        self.new_button.setObjectName("newDeviceButton")
        button_row.addWidget(self.apply_button)
        button_row.addWidget(self.reset_button)
        button_row.addWidget(self.new_button)
        button_row.addStretch(1)

        root_layout.addWidget(title)
        root_layout.addWidget(self.summary_label)
        root_layout.addLayout(form)
        root_layout.addWidget(self.message_label)
        root_layout.addLayout(button_row)
        root_layout.addStretch(1)

        self.apply_button.clicked.connect(self.apply_changes)
        self.reset_button.clicked.connect(lambda: self.load_device())
        self.new_button.clicked.connect(self.create_new_device)
        self.load_device()

    @property
    def device(self) -> Device:
        """Return the device currently being edited."""
        return self._device

    def bind_incident(self, incident: Incident) -> None:
        """Switch the editor to a different incident and ensure it has a device."""
        self._incident = incident
        self._building = self._ensure_building()
        self.load_device()

    def load_device(self, device: Device | None = None) -> None:
        """Populate the form from the current device."""
        self._building = self._ensure_building()
        if device is not None:
            self._device = device
            if not self._contains_device(self._device):
                self._building.add_device(self._device)
        elif not self._contains_device(self._device):
            self._device = self._ensure_device()

        self.hostname_input.setText(self._device.hostname)
        self.manufacturer_input.setText(self._device.manufacturer)
        self.model_input.setText(self._device.model)
        self.serial_input.setText(self._device.serial_number)
        self.ip_input.setText(self._device.ip_address or "")
        self.mac_input.setText(self._device.mac_address or "")
        self.type_input.setCurrentIndex(
            max(0, self.type_input.findData(self._device.device_type.value))
        )
        self.status_input.setCurrentIndex(
            max(0, self.status_input.findData(self._device.status.value))
        )
        self._refresh_summary()
        self._refresh_network_membership()
        self.message_label.setText("")

    def sync_from_model(self) -> None:
        """Refresh derived labels without clearing the current feedback message."""
        self._refresh_summary()
        self._refresh_network_membership()

    def create_new_device(self) -> None:
        """Create a fresh device record under the active building."""
        self._building = self._ensure_building()
        self._device = Device("Untitled Device")
        self._building.add_device(self._device)
        self.load_device(self._device)
        self.message_label.setText("New device created in memory.")
        self.device_updated.emit(self._incident)

    def apply_changes(self) -> None:
        """Validate and apply the form values to the device model."""
        hostname = self.hostname_input.text().strip()
        if not hostname:
            self.message_label.setText("Hostname is required.")
            return

        self._device.hostname = hostname
        self._device.manufacturer = self.manufacturer_input.text().strip()
        self._device.model = self.model_input.text().strip()
        self._device.serial_number = self.serial_input.text().strip()
        self._device.ip_address = self.ip_input.text().strip() or None
        self._device.mac_address = self.mac_input.text().strip() or None
        self._device.device_type = DeviceType(self.type_input.currentData())
        self._device.status = DeviceStatus(self.status_input.currentData())
        self._device.touch()
        self._refresh_summary()
        self._refresh_network_membership()
        self.message_label.setText("Device updated in memory.")
        self.device_updated.emit(self._incident)

    def _ensure_building(self) -> Building:
        """Return the primary building, creating one if the incident is empty."""
        if self._incident.camps and self._incident.camps[0].buildings:
            return self._incident.camps[0].buildings[0]

        from fireitmanager.models.camp import Camp
        from fireitmanager.models.building import Building

        if not self._incident.camps:
            camp = Camp("Base Camp")
            self._incident.add_camp(camp)
        else:
            camp = self._incident.camps[0]

        building = Building("IT Staging")
        camp.add_building(building)
        return building

    def _ensure_device(self) -> Device:
        """Return the primary device, creating one if the building is empty."""
        if self._building.devices:
            return self._building.devices[0]

        device = Device("it-router-01", device_type=DeviceType.ROUTER, status=DeviceStatus.ONLINE)
        self._building.add_device(device)
        return device

    def _refresh_summary(self) -> None:
        """Refresh the summary banner from the current device."""
        self.summary_label.setText(
            f"Editing {self._device.hostname} for {self._incident.summary()}"
        )

    def _refresh_network_membership(self) -> None:
        """Show the networks that currently include this device."""
        network_names: list[str] = []
        for camp in self._incident.camps:
            for network in camp.networks:
                if any(existing is self._device for existing in network.devices):
                    network_names.append(network.name)
        self.networks_value.setText(", ".join(network_names) or "Unassigned")

    def _contains_device(self, device: Device) -> bool:
        """Return True when the building already owns the given device by identity."""
        return any(existing is device for existing in self._building.devices)
