"""Building editor widget for the FireIT Manager workspace."""

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
from fireitmanager.models.camp import Camp
from fireitmanager.models.enums import BuildingType
from fireitmanager.models.incident import Incident
from fireitmanager.models.location import Location


class BuildingEditorWidget(QWidget):
    """Manual entry form for the primary building in the active camp."""

    building_updated = Signal(object)

    def __init__(self, incident: Incident, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("buildingEditorWidget")
        self._incident = incident
        self._camp = self._ensure_camp()
        self._building = self._ensure_building()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        title = QLabel("Building Editor", self)
        title.setObjectName("buildingEditorTitle")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")

        self.summary_label = QLabel("", self)
        self.summary_label.setObjectName("buildingEditorSummary")
        self.summary_label.setWordWrap(True)

        form = QFormLayout()
        self.name_input = QLineEdit(self)
        self.name_input.setObjectName("buildingNameInput")

        self.type_input = QComboBox(self)
        self.type_input.setObjectName("buildingTypeInput")
        for building_type in BuildingType:
            self.type_input.addItem(building_type.value, building_type.value)

        self.location_name_input = QLineEdit(self)
        self.location_name_input.setObjectName("buildingLocationNameInput")
        self.latitude_input = QLineEdit(self)
        self.latitude_input.setObjectName("buildingLatitudeInput")
        self.longitude_input = QLineEdit(self)
        self.longitude_input.setObjectName("buildingLongitudeInput")
        self.elevation_input = QLineEdit(self)
        self.elevation_input.setObjectName("buildingElevationInput")
        self.notes_input = QLineEdit(self)
        self.notes_input.setObjectName("buildingNotesInput")

        form.addRow("Building Name", self.name_input)
        form.addRow("Building Type", self.type_input)
        form.addRow("Location Name", self.location_name_input)
        form.addRow("Latitude", self.latitude_input)
        form.addRow("Longitude", self.longitude_input)
        form.addRow("Elevation (ft)", self.elevation_input)
        form.addRow("Notes", self.notes_input)

        self.device_count_value = QLabel("0", self)
        self.device_count_value.setObjectName("buildingDeviceCountValue")
        counts_form = QFormLayout()
        counts_form.addRow("Devices", self.device_count_value)

        self.message_label = QLabel("", self)
        self.message_label.setObjectName("buildingEditorMessage")
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: #1d4ed8;")

        button_row = QHBoxLayout()
        self.apply_button = QPushButton("Apply Changes", self)
        self.apply_button.setObjectName("applyBuildingChangesButton")
        self.reset_button = QPushButton("Reset", self)
        self.reset_button.setObjectName("resetBuildingButton")
        self.new_button = QPushButton("New Building", self)
        self.new_button.setObjectName("newBuildingButton")
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
        self.reset_button.clicked.connect(lambda: self.load_building())
        self.new_button.clicked.connect(self.create_new_building)
        self.load_building()

    @property
    def building(self) -> Building:
        """Return the building currently being edited."""
        return self._building

    def bind_incident(self, incident: Incident) -> None:
        """Switch the editor to a different incident and ensure it has a building."""
        self._incident = incident
        self._camp = self._ensure_camp()
        self.load_building()

    def load_building(self, building: Building | None = None) -> None:
        """Populate the form from the current building."""
        self._camp = self._ensure_camp()
        if building is not None:
            self._building = building
            if self._building not in self._camp.buildings:
                self._camp.add_building(self._building)
        elif self._building not in self._camp.buildings:
            self._building = self._ensure_building()

        self.name_input.setText(self._building.name)
        index = self.type_input.findData(self._building.building_type.value)
        self.type_input.setCurrentIndex(index if index >= 0 else 0)

        location = self._building.location
        self.location_name_input.setText(location.name if location is not None else "")
        self.latitude_input.setText("" if location is None or location.latitude is None else str(location.latitude))
        self.longitude_input.setText("" if location is None or location.longitude is None else str(location.longitude))
        self.elevation_input.setText("" if location is None or location.elevation_ft is None else str(location.elevation_ft))
        self.notes_input.setText("" if location is None else location.notes)

        self._refresh_counts()
        self._refresh_summary()
        self.message_label.setText("")

    def sync_from_model(self) -> None:
        """Refresh derived labels without clearing the current feedback message."""
        self._refresh_counts()
        self._refresh_summary()

    def create_new_building(self) -> None:
        """Create a fresh building record under the active camp."""
        self._camp = self._ensure_camp()
        self._building = Building("Untitled Building")
        self._camp.add_building(self._building)
        self.load_building(self._building)
        self.message_label.setText("New building created in memory.")
        self.building_updated.emit(self._incident)

    def apply_changes(self) -> None:
        """Validate and apply the form values to the building model."""
        name = self.name_input.text().strip()
        if not name:
            self.message_label.setText("Building name is required.")
            return

        self._building.name = name
        self._building.building_type = BuildingType(self.type_input.currentData())

        location_name = self.location_name_input.text().strip()
        latitude = self._parse_optional_float(self.latitude_input.text().strip(), "latitude")
        if isinstance(latitude, str):
            self.message_label.setText(latitude)
            return
        longitude = self._parse_optional_float(self.longitude_input.text().strip(), "longitude")
        if isinstance(longitude, str):
            self.message_label.setText(longitude)
            return
        elevation = self._parse_optional_float(self.elevation_input.text().strip(), "elevation")
        if isinstance(elevation, str):
            self.message_label.setText(elevation)
            return
        notes = self.notes_input.text().strip()

        if any([location_name, latitude is not None, longitude is not None, elevation is not None, notes]):
            if self._building.location is None:
                self._building.location = Location(location_name or f"{self._building.name} Location")
            elif location_name:
                self._building.location.name = location_name
            self._building.location.latitude = latitude
            self._building.location.longitude = longitude
            self._building.location.elevation_ft = elevation
            self._building.location.notes = notes
            self._building.location.touch()
        else:
            self._building.location = None

        self._building.touch()
        self._refresh_summary()
        self.message_label.setText("Building updated in memory.")
        self.building_updated.emit(self._incident)

    def _ensure_camp(self) -> Camp:
        """Return the primary camp, creating one if the incident is empty."""
        if self._incident.camps:
            return self._incident.camps[0]

        camp = Camp("Base Camp")
        self._incident.add_camp(camp)
        return camp

    def _ensure_building(self) -> Building:
        """Return the primary building, creating one if the camp is empty."""
        if self._camp.buildings:
            return self._camp.buildings[0]

        building = Building("IT Staging", building_type=BuildingType.COMMAND_POST)
        self._camp.add_building(building)
        return building

    def _refresh_summary(self) -> None:
        """Refresh the summary banner from the current building."""
        self.summary_label.setText(
            f"Editing {self._building.name} ({self._building.building_type.value}) for {self._incident.summary()}"
        )

    def _refresh_counts(self) -> None:
        """Refresh the related building counts."""
        self.device_count_value.setText(str(len(self._building.devices)))

    @staticmethod
    def _parse_optional_float(text: str, field_name: str) -> float | None | str:
        """Parse an optional float field, returning an error string on failure."""
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return f"{field_name.capitalize()} must be a number."
