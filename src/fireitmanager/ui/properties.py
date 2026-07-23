"""Properties dock content for the FireIT Manager workspace."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from fireitmanager.models.asset import Asset
from fireitmanager.models.building import Building
from fireitmanager.models.cable import Cable
from fireitmanager.models.camp import Camp
from fireitmanager.models.device import Device
from fireitmanager.models.enums import (
    AssetStatus,
    BuildingType,
    CableType,
    DeviceStatus,
    DeviceType,
)
from fireitmanager.models.incident import Incident
from fireitmanager.models.network import Network
from fireitmanager.models.person import Person


PropertyUpdate = Callable[[object], None]
PropertyReader = Callable[[], PropertyUpdate]


class PropertiesWidget(QWidget):
    """Display selection details from the incident explorer."""

    object_updated = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("propertiesWidget")
        self._target: object | None = None
        self._field_readers: list[PropertyReader] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("Properties", self)
        title.setObjectName("propertiesTitle")
        title.setStyleSheet("font-size: 16px; font-weight: 600;")

        self.name_value = QLabel("Workspace", self)
        self.name_value.setObjectName("propertiesNameValue")
        self.name_value.setWordWrap(True)
        self.name_value.setStyleSheet("font-size: 14px; font-weight: 600;")

        self.kind_value = QLabel("workspace", self)
        self.kind_value.setObjectName("propertiesKindValue")
        self.kind_value.setWordWrap(True)

        self.path_value = QLabel("Workspace", self)
        self.path_value.setObjectName("propertiesPathValue")
        self.path_value.setWordWrap(True)

        self.description_value = QLabel(
            "Select an item in the explorer to see its details.",
            self,
        )
        self.description_value.setObjectName("propertiesDescriptionValue")
        self.description_value.setWordWrap(True)

        self.details_value = QLabel("Incident metadata will appear here.", self)
        self.details_value.setObjectName("propertiesDetailsValue")
        self.details_value.setWordWrap(True)
        self.details_value.setStyleSheet("font-family: Consolas, monospace;")

        editor_title = QLabel("Edit Selection", self)
        editor_title.setObjectName("propertiesEditorTitle")
        editor_title.setStyleSheet("font-size: 14px; font-weight: 600;")

        self.editor_message = QLabel("Select a concrete workspace object to edit it.", self)
        self.editor_message.setObjectName("propertiesEditorMessage")
        self.editor_message.setWordWrap(True)
        self.editor_message.setStyleSheet("color: #6b7280;")

        self.editor_container = QWidget(self)
        self.editor_container.setObjectName("propertiesEditorWidget")
        self.editor_form = QFormLayout(self.editor_container)
        self.editor_form.setContentsMargins(0, 0, 0, 0)
        self.editor_form.setSpacing(6)

        self.apply_button = QPushButton("Apply", self)
        self.apply_button.setObjectName("applyPropertiesButton")
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self.apply_changes)

        layout.addWidget(title)
        layout.addWidget(QLabel("Name", self))
        layout.addWidget(self.name_value)
        layout.addWidget(QLabel("Type", self))
        layout.addWidget(self.kind_value)
        layout.addWidget(QLabel("Path", self))
        layout.addWidget(self.path_value)
        layout.addWidget(QLabel("Description", self))
        layout.addWidget(self.description_value)
        layout.addWidget(QLabel("Details", self))
        layout.addWidget(self.details_value)
        layout.addSpacing(8)
        layout.addWidget(editor_title)
        layout.addWidget(self.editor_message)
        layout.addWidget(self.editor_container)
        layout.addWidget(self.apply_button)
        layout.addStretch(1)

    def set_details(
        self,
        name: str,
        kind: str,
        path: str,
        description: str,
        details: str,
    ) -> None:
        """Update the visible properties for the current selection."""
        self.name_value.setText(name)
        self.kind_value.setText(kind)
        self.path_value.setText(path)
        self.description_value.setText(description)
        self.details_value.setText(details or "No additional details available.")

    def set_target(self, target: object | None) -> None:
        """Load editable fields for the selected model object."""
        self._target = target
        self._configure_editor()

    def apply_changes(self) -> None:
        """Apply edited property values to the selected model object."""
        target = self._target
        if target is None or not self._field_readers:
            self.editor_message.setText("No editable object selected.")
            return

        try:
            updates = [reader() for reader in self._field_readers]
        except ValueError as error:
            self.editor_message.setText(str(error))
            return

        for update in updates:
            update(target)

        touch = getattr(target, "touch", None)
        if callable(touch):
            touch()

        self.editor_message.setText("Properties updated.")
        self.object_updated.emit(target)

    def _configure_editor(self) -> None:
        self._clear_editor()
        self._field_readers = []
        self.apply_button.setEnabled(False)

        target = self._target
        if target is None:
            self.editor_message.setText("Select a concrete workspace object to edit it.")
            return

        if isinstance(target, Incident):
            self._add_text_field("Name", "name", target.name, required=True)
            self._add_text_field("Incident Number", "incident_number", target.incident_number)
            self._add_text_field("Agency", "agency", target.agency)
            self._add_text_field("Operational Period", "operational_period", target.operational_period)
        elif isinstance(target, Camp):
            self._add_text_field("Name", "name", target.name, required=True)
        elif isinstance(target, Building):
            self._add_text_field("Name", "name", target.name, required=True)
            self._add_combo_field("Building Type", "building_type", BuildingType, target.building_type)
        elif isinstance(target, Device):
            self._add_text_field("Hostname", "hostname", target.hostname, required=True)
            self._add_text_field("Manufacturer", "manufacturer", target.manufacturer)
            self._add_text_field("Model", "model", target.model)
            self._add_text_field("Serial Number", "serial_number", target.serial_number)
            self._add_text_field("IP Address", "ip_address", target.ip_address, none_when_empty=True)
            self._add_text_field("MAC Address", "mac_address", target.mac_address, none_when_empty=True)
            self._add_combo_field("Device Type", "device_type", DeviceType, target.device_type)
            self._add_combo_field("Status", "status", DeviceStatus, target.status)
        elif isinstance(target, Network):
            self._add_text_field("Name", "name", target.name, required=True)
        elif isinstance(target, Asset):
            self._add_text_field("Name", "name", target.name, required=True)
            self._add_text_field("Owner", "owner", target.owner)
            self._add_text_field("Acquisition Type", "acquisition_type", target.acquisition_type)
            self._add_text_field("Barcode", "barcode", target.barcode)
            self._add_combo_field("Status", "status", AssetStatus, target.status)
        elif isinstance(target, Person):
            self._add_text_field("Name", "name", target.name, required=True)
            self._add_text_field("Position", "position", target.position)
            self._add_text_field("Agency", "agency", target.agency)
        elif isinstance(target, Cable):
            self._add_combo_field("Cable Type", "cable_type", CableType, target.cable_type)
            self._add_float_field("Length", "length", target.length)
            self._add_text_field("Notes", "notes", target.notes)

        if self._field_readers:
            self.editor_message.setText("Edit values and apply to update the selected object.")
            self.apply_button.setEnabled(True)
        else:
            self.editor_message.setText("This selection does not expose editable properties.")

    def _clear_editor(self) -> None:
        while self.editor_form.rowCount():
            self.editor_form.removeRow(0)

    def _add_text_field(
        self,
        label: str,
        attribute: str,
        value: str | None,
        *,
        required: bool = False,
        none_when_empty: bool = False,
    ) -> None:
        edit = QLineEdit(self.editor_container)
        edit.setObjectName(f"propertiesEdit{_camel_name(attribute)}Input")
        edit.setText(value or "")
        self.editor_form.addRow(label, edit)

        def reader() -> PropertyUpdate:
            text = edit.text().strip()
            if required and not text:
                raise ValueError(f"{label} cannot be empty.")
            new_value = None if none_when_empty and not text else text
            return lambda target: setattr(target, attribute, new_value)

        self._field_readers.append(reader)

    def _add_float_field(
        self,
        label: str,
        attribute: str,
        value: float | None,
    ) -> None:
        edit = QLineEdit(self.editor_container)
        edit.setObjectName(f"propertiesEdit{_camel_name(attribute)}Input")
        edit.setText("" if value is None else f"{value:g}")
        self.editor_form.addRow(label, edit)

        def reader() -> PropertyUpdate:
            text = edit.text().strip()
            if not text:
                return lambda target: setattr(target, attribute, None)
            try:
                new_value = float(text)
            except ValueError as exc:
                raise ValueError(f"{label} must be a number.") from exc
            return lambda target: setattr(target, attribute, new_value)

        self._field_readers.append(reader)

    def _add_combo_field(
        self,
        label: str,
        attribute: str,
        enum_type: type[Enum],
        value: Enum,
    ) -> None:
        combo = QComboBox(self.editor_container)
        combo.setObjectName(f"propertiesEdit{_camel_name(attribute)}Input")
        for index, choice in enumerate(enum_type):
            combo.addItem(choice.value, choice)
            if choice == value:
                combo.setCurrentIndex(index)
        self.editor_form.addRow(label, combo)

        def reader() -> PropertyUpdate:
            new_value = enum_type(combo.currentText())
            return lambda target: setattr(target, attribute, new_value)

        self._field_readers.append(reader)


def _camel_name(attribute: str) -> str:
    return "".join(part.capitalize() for part in attribute.split("_"))
