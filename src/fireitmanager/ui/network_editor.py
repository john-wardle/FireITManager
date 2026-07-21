"""Network editor widget for the FireIT Manager workspace."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from fireitmanager.models.camp import Camp
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

        self.device_count_value = QLabel("0", self)
        self.device_count_value.setObjectName("networkDeviceCountValue")
        self.cable_count_value = QLabel("0", self)
        self.cable_count_value.setObjectName("networkCableCountValue")

        counts_form = QFormLayout()
        counts_form.addRow("Devices", self.device_count_value)
        counts_form.addRow("Cables", self.cable_count_value)

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
        root_layout.addWidget(self.message_label)
        root_layout.addLayout(button_row)
        root_layout.addStretch(1)

        self.apply_button.clicked.connect(self.apply_changes)
        self.reset_button.clicked.connect(lambda: self.load_network())
        self.new_button.clicked.connect(self.create_new_network)
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
            if self._network not in self._camp.networks:
                self._camp.add_network(self._network)
        elif self._network not in self._camp.networks:
            self._network = self._ensure_network()

        self.name_input.setText(self._network.name)
        self._refresh_counts()
        self._refresh_summary()
        self.message_label.setText("")

    def sync_from_model(self) -> None:
        """Refresh derived labels without clearing the current feedback message."""
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
