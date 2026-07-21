"""Network editor widget for the FireIT Manager workspace."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from fireitmanager.models.camp import Camp
from fireitmanager.models.device import Device
from fireitmanager.models.incident import Incident
from fireitmanager.models.network import Network


class NetworkEditorWidget(QWidget):
    """Manual entry form for the primary network in the active camp."""

    network_updated = Signal(object)

    def __init__(self, incident: Incident, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("networkEditorWidget")
        self._incident = incident
        self._camp = self._ensure_camp()
        self._network = self._ensure_network()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        title = QLabel("Network Editor", self)
        title.setObjectName("networkEditorTitle")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")

        self.summary_label = QLabel("", self)
        self.summary_label.setObjectName("networkEditorSummary")
        self.summary_label.setWordWrap(True)

        form = QFormLayout()
        self.name_input = QLineEdit(self)
        self.name_input.setObjectName("networkNameInput")
        form.addRow("Network Name", self.name_input)

        self.device_selector = QComboBox(self)
        self.device_selector.setObjectName("networkDeviceSelectorInput")
        self.add_device_button = QPushButton("Add Selected Device", self)
        self.add_device_button.setObjectName("addNetworkDeviceButton")
        self.remove_device_button = QPushButton("Remove Selected Device", self)
        self.remove_device_button.setObjectName("removeNetworkDeviceButton")
        self.device_list = QListWidget(self)
        self.device_list.setObjectName("networkDeviceList")

        self.device_count_value = QLabel("0", self)
        self.device_count_value.setObjectName("networkDeviceCountValue")
        self.cable_count_value = QLabel("0", self)
        self.cable_count_value.setObjectName("networkCableCountValue")

        counts_form = QFormLayout()
        counts_form.addRow("Devices", self.device_count_value)
        counts_form.addRow("Cables", self.cable_count_value)

        device_form = QFormLayout()
        device_form.addRow("Available Devices", self.device_selector)
        device_form.addRow("Network Members", self.device_list)

        self.message_label = QLabel("", self)
        self.message_label.setObjectName("networkEditorMessage")
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: #334155;")

        button_row = QHBoxLayout()
        self.apply_button = QPushButton("Apply Changes", self)
        self.apply_button.setObjectName("applyNetworkChangesButton")
        self.reset_button = QPushButton("Reset", self)
        self.reset_button.setObjectName("resetNetworkButton")
        self.new_button = QPushButton("New Network", self)
        self.new_button.setObjectName("newNetworkButton")
        button_row.addWidget(self.apply_button)
        button_row.addWidget(self.reset_button)
        button_row.addWidget(self.new_button)
        button_row.addStretch(1)

        root_layout.addWidget(title)
        root_layout.addWidget(self.summary_label)
        root_layout.addLayout(form)
        root_layout.addLayout(counts_form)
        root_layout.addLayout(device_form)
        root_layout.addWidget(self.add_device_button)
        root_layout.addWidget(self.remove_device_button)
        root_layout.addWidget(self.message_label)
        root_layout.addLayout(button_row)
        root_layout.addStretch(1)

        self.apply_button.clicked.connect(self.apply_changes)
        self.reset_button.clicked.connect(lambda: self.load_network())
        self.new_button.clicked.connect(self.create_new_network)
        self.add_device_button.clicked.connect(self.add_selected_device)
        self.remove_device_button.clicked.connect(self.remove_selected_device)
        self.load_network()

    @property
    def network(self) -> Network:
        """Return the network currently being edited."""
        return self._network

    def bind_incident(self, incident: Incident) -> None:
        """Switch the editor to a different incident and ensure it has a network."""
        self._incident = incident
        self._camp = self._ensure_camp()
        self.load_network()

    def load_network(self, network: Network | None = None) -> None:
        """Populate the form from the current network."""
        self._camp = self._ensure_camp()
        if network is not None:
            self._network = network
            if not self._contains_network(self._network):
                self._camp.add_network(self._network)
        elif not self._contains_network(self._network):
            self._network = self._ensure_network()

        self.name_input.setText(self._network.name)
        self._refresh_device_selector()
        self._refresh_device_list()
        self._refresh_counts()
        self._refresh_summary()
        self.message_label.setText("")

    def sync_from_model(self) -> None:
        """Refresh derived labels without clearing the current feedback message."""
        self._refresh_device_selector()
        self._refresh_device_list()
        self._refresh_counts()
        self._refresh_summary()

    def create_new_network(self) -> None:
        """Create a fresh network record under the active camp."""
        self._camp = self._ensure_camp()
        self._network = Network("Untitled Network")
        self._camp.add_network(self._network)
        self.load_network(self._network)
        self.message_label.setText("New network created in memory.")
        self.network_updated.emit(self._incident)

    def apply_changes(self) -> None:
        """Validate and apply the form values to the network model."""
        name = self.name_input.text().strip()
        if not name:
            self.message_label.setText("Network name is required.")
            return

        self._network.name = name
        self._network.touch()
        self._refresh_summary()
        self.message_label.setText("Network updated in memory.")
        self.network_updated.emit(self._incident)

    def add_selected_device(self) -> None:
        """Add the selected available device to the network."""
        device = self._selected_device_from_selector()
        if device is None:
            self.message_label.setText("Select a device to add.")
            return

        if device in self._network.devices:
            self.message_label.setText(f"{device.hostname} is already in this network.")
            return

        self._network.add_device(device)
        self._refresh_device_list()
        self._refresh_counts()
        self.message_label.setText(f"Added {device.hostname} to the network.")
        self.network_updated.emit(self._incident)

    def remove_selected_device(self) -> None:
        """Remove the selected member device from the network."""
        item = self.device_list.currentItem()
        if item is None:
            self.message_label.setText("Select a network member to remove.")
            return

        device = item.data(Qt.UserRole)
        if not isinstance(device, Device):
            self.message_label.setText("Selected network member is unavailable.")
            return

        self._network.remove_device(device)
        self._refresh_device_list()
        self._refresh_counts()
        self.message_label.setText(f"Removed {device.hostname} from the network.")
        self.network_updated.emit(self._incident)

    def _ensure_camp(self) -> Camp:
        """Return the primary camp, creating one if the incident is empty."""
        if self._incident.camps:
            return self._incident.camps[0]

        camp = Camp("Base Camp")
        self._incident.add_camp(camp)
        return camp

    def _ensure_network(self) -> Network:
        """Return the primary network, creating one if the camp is empty."""
        if self._camp.networks:
            return self._camp.networks[0]

        network = Network("Camp LAN")
        self._camp.add_network(network)
        return network

    def _refresh_summary(self) -> None:
        """Refresh the summary banner from the current network."""
        self.summary_label.setText(
            f"Editing {self._network.name} for {self._incident.summary()}"
        )

    def _refresh_counts(self) -> None:
        """Refresh the related network counts."""
        self.device_count_value.setText(str(len(self._network.devices)))
        self.cable_count_value.setText(str(len(self._network.cables)))

    def _refresh_device_selector(self) -> None:
        """Populate the available-device picker from the incident graph."""
        current_value = self.device_selector.currentData()
        self.device_selector.blockSignals(True)
        self.device_selector.clear()
        devices = self._all_devices()
        for device in devices:
            label = f"{device.hostname}"
            if device.assigned_building is not None:
                label = f"{label} ({device.assigned_building.name})"
            self.device_selector.addItem(label, device)
        if current_value is not None:
            index = self.device_selector.findData(current_value)
            if index >= 0:
                self.device_selector.setCurrentIndex(index)
        self.device_selector.blockSignals(False)

    def _refresh_device_list(self) -> None:
        """Refresh the list of devices currently assigned to the network."""
        self.device_list.clear()
        for device in self._network.devices:
            label = device.hostname
            if device.assigned_building is not None:
                label = f"{label} ({device.assigned_building.name})"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, device)
            self.device_list.addItem(item)

    def _selected_device_from_selector(self) -> Device | None:
        """Return the currently selected device from the picker."""
        candidate = self.device_selector.currentData()
        if isinstance(candidate, Device):
            return candidate
        return None

    def _all_devices(self) -> list[Device]:
        """Return all devices in the incident, preserving first-seen order."""
        devices: list[Device] = []
        seen: set[str] = set()
        for camp in self._incident.camps:
            for building in camp.buildings:
                for device in building.devices:
                    device_key = str(device.device_id)
                    if device_key in seen:
                        continue
                    seen.add(device_key)
                    devices.append(device)
        return devices

    def _contains_network(self, network: Network) -> bool:
        """Return True when the camp already owns the given network by identity."""
        return any(existing is network for existing in self._camp.networks)
