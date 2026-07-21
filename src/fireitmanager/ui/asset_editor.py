"""Asset editor widget for the FireIT Manager workspace."""

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

from fireitmanager.models.asset import Asset
from fireitmanager.models.enums import AssetStatus
from fireitmanager.models.incident import Incident


class AssetEditorWidget(QWidget):
    """Manual entry form for the primary asset in the active incident."""

    asset_updated = Signal(object)

    def __init__(self, incident: Incident, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("assetEditorWidget")
        self._incident = incident
        self._asset = self._ensure_asset()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        title = QLabel("Asset Editor", self)
        title.setObjectName("assetEditorTitle")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")

        self.summary_label = QLabel("", self)
        self.summary_label.setObjectName("assetEditorSummary")
        self.summary_label.setWordWrap(True)

        form = QFormLayout()
        self.name_input = QLineEdit(self)
        self.name_input.setObjectName("assetNameInput")
        self.owner_input = QLineEdit(self)
        self.owner_input.setObjectName("assetOwnerInput")
        self.acquisition_input = QLineEdit(self)
        self.acquisition_input.setObjectName("assetAcquisitionInput")
        self.barcode_input = QLineEdit(self)
        self.barcode_input.setObjectName("assetBarcodeInput")
        self.assigned_person_input = QLineEdit(self)
        self.assigned_person_input.setObjectName("assetAssignedPersonInput")
        self.assigned_person_selector = QComboBox(self)
        self.assigned_person_selector.setObjectName("assetAssignedPersonSelectorInput")
        self.assign_selected_person_button = QPushButton("Use Selected Person", self)
        self.assign_selected_person_button.setObjectName("assignSelectedAssetPersonButton")
        self.clear_assigned_person_button = QPushButton("Clear Assigned Person", self)
        self.clear_assigned_person_button.setObjectName("clearAssetAssignedPersonButton")

        self.status_input = QComboBox(self)
        self.status_input.setObjectName("assetStatusInput")
        for status in AssetStatus:
            self.status_input.addItem(status.value, status.value)

        form.addRow("Asset Name", self.name_input)
        form.addRow("Owner", self.owner_input)
        form.addRow("Acquisition Type", self.acquisition_input)
        form.addRow("Barcode", self.barcode_input)
        form.addRow("Assigned Person", self.assigned_person_input)
        form.addRow("People Picker", self.assigned_person_selector)
        form.addRow("Status", self.status_input)

        self.message_label = QLabel("", self)
        self.message_label.setObjectName("assetEditorMessage")
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: #9a3412;")

        button_row = QHBoxLayout()
        self.apply_button = QPushButton("Apply Changes", self)
        self.apply_button.setObjectName("applyAssetChangesButton")
        self.reset_button = QPushButton("Reset", self)
        self.reset_button.setObjectName("resetAssetButton")
        self.new_button = QPushButton("New Asset", self)
        self.new_button.setObjectName("newAssetButton")
        button_row.addWidget(self.apply_button)
        button_row.addWidget(self.reset_button)
        button_row.addWidget(self.new_button)
        button_row.addWidget(self.assign_selected_person_button)
        button_row.addWidget(self.clear_assigned_person_button)
        button_row.addStretch(1)

        root_layout.addWidget(title)
        root_layout.addWidget(self.summary_label)
        root_layout.addLayout(form)
        root_layout.addWidget(self.message_label)
        root_layout.addLayout(button_row)
        root_layout.addStretch(1)

        self.apply_button.clicked.connect(self.apply_changes)
        self.reset_button.clicked.connect(lambda: self.load_asset())
        self.new_button.clicked.connect(self.create_new_asset)
        self.assign_selected_person_button.clicked.connect(self.assign_selected_person)
        self.clear_assigned_person_button.clicked.connect(self.clear_assigned_person)
        self.load_asset()

    @property
    def asset(self) -> Asset:
        """Return the asset currently being edited."""
        return self._asset

    def bind_incident(self, incident: Incident) -> None:
        """Switch the editor to a different incident and ensure it has an asset."""
        self._incident = incident
        self.load_asset()

    def load_asset(self, asset: Asset | None = None) -> None:
        """Populate the form from the current asset."""
        if asset is not None:
            self._asset = asset
            if not self._contains_asset(self._asset):
                self._incident.assets.append(self._asset)
        elif not self._contains_asset(self._asset):
            self._asset = self._ensure_asset()

        self.name_input.setText(self._asset.name)
        self.owner_input.setText(self._asset.owner)
        self.acquisition_input.setText(self._asset.acquisition_type)
        self.barcode_input.setText(self._asset.barcode)
        self.assigned_person_input.setText(
            self._asset.assigned_person.name if self._asset.assigned_person is not None else ""
        )
        self._refresh_person_selector()
        self.status_input.setCurrentIndex(
            max(0, self.status_input.findData(self._asset.status.value))
        )
        self._refresh_summary()
        self.message_label.setText("")

    def sync_from_model(self) -> None:
        """Refresh the summary without clearing the current feedback message."""
        self._refresh_person_selector()
        self._refresh_summary()

    def create_new_asset(self) -> None:
        """Create a fresh asset record under the active incident."""
        self._asset = Asset("Untitled Asset")
        self._incident.assets.append(self._asset)
        self.load_asset(self._asset)
        self.message_label.setText("New asset created in memory.")
        self.asset_updated.emit(self._incident)

    def apply_changes(self) -> None:
        """Validate and apply the form values to the asset model."""
        name = self.name_input.text().strip()
        if not name:
            self.message_label.setText("Asset name is required.")
            return

        self._asset.name = name
        self._asset.owner = self.owner_input.text().strip()
        self._asset.acquisition_type = self.acquisition_input.text().strip()
        self._asset.barcode = self.barcode_input.text().strip()
        assigned_person_name = self.assigned_person_input.text().strip()
        if assigned_person_name:
            assigned_person = self._find_person(assigned_person_name)
            if assigned_person is None:
                self.message_label.setText("Assigned person not found.")
                return
            self._asset.assign_person(assigned_person)
        else:
            self._asset.assigned_person = None
        self._asset.status = AssetStatus(self.status_input.currentData())
        self._asset.touch()
        self._refresh_summary()
        self.message_label.setText("Asset updated in memory.")
        self.asset_updated.emit(self._incident)

    def _ensure_asset(self) -> Asset:
        """Return the primary asset, creating one if the incident is empty."""
        if self._incident.assets:
            return self._incident.assets[0]

        asset = Asset("Generator 1")
        self._incident.assets.append(asset)
        return asset

    def _refresh_summary(self) -> None:
        """Refresh the summary banner from the current asset."""
        self.summary_label.setText(
            f"Editing {self._asset.name} ({self._asset.status.value}) for {self._incident.summary()}"
        )

    def _refresh_person_selector(self) -> None:
        """Populate the picker with the people in the incident."""
        current_person = self._asset.assigned_person
        self.assigned_person_selector.blockSignals(True)
        self.assigned_person_selector.clear()
        self.assigned_person_selector.addItem("Unassigned", None)
        for person in self._incident.personnel:
            self.assigned_person_selector.addItem(person.name, person)
        if current_person is not None:
            index = self.assigned_person_selector.findData(current_person)
            if index >= 0:
                self.assigned_person_selector.setCurrentIndex(index)
        elif self.assigned_person_input.text().strip():
            index = self.assigned_person_selector.findText(self.assigned_person_input.text().strip())
            if index >= 0:
                self.assigned_person_selector.setCurrentIndex(index)
        self.assigned_person_selector.blockSignals(False)

    def assign_selected_person(self) -> None:
        """Copy the selected picker value into the manual assignment field."""
        person = self.assigned_person_selector.currentData()
        if person is None:
            self.assigned_person_input.clear()
            self.message_label.setText("Cleared the assigned person picker.")
            return
        self.assigned_person_input.setText(person.name)
        self.message_label.setText(f"Selected {person.name} for the asset.")

    def clear_assigned_person(self) -> None:
        """Clear the assigned person from the asset."""
        self.assigned_person_selector.setCurrentIndex(0)
        self.assigned_person_input.clear()
        self._asset.assigned_person = None
        self._asset.touch()
        self._refresh_summary()
        self.message_label.setText("Assigned person cleared.")
        self.asset_updated.emit(self._incident)

    def _contains_asset(self, asset: Asset) -> bool:
        """Return True when the incident already owns the given asset by identity."""
        return any(existing is asset for existing in self._incident.assets)

    def _find_person(self, name: str):
        """Find a person by name within the active incident."""
        for person in self._incident.personnel:
            if person.name.lower() == name.lower():
                return person
        return None
