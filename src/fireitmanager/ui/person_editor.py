"""Person editor widget for the FireIT Manager workspace."""

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

from fireitmanager.models.incident import Incident
from fireitmanager.models.person import Person


class PersonEditorWidget(QWidget):
    """Manual entry form for the primary person in the active incident."""

    person_updated = Signal(object)

    def __init__(self, incident: Incident, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("personEditorWidget")
        self._incident = incident
        self._person = self._ensure_person()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        title = QLabel("Person Editor", self)
        title.setObjectName("personEditorTitle")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")

        self.summary_label = QLabel("", self)
        self.summary_label.setObjectName("personEditorSummary")
        self.summary_label.setWordWrap(True)

        form = QFormLayout()
        self.name_input = QLineEdit(self)
        self.name_input.setObjectName("personNameInput")
        self.position_input = QLineEdit(self)
        self.position_input.setObjectName("personPositionInput")
        self.agency_input = QLineEdit(self)
        self.agency_input.setObjectName("personAgencyInput")
        self.assigned_devices_input = QLineEdit(self)
        self.assigned_devices_input.setObjectName("personAssignedDevicesInput")

        form.addRow("Name", self.name_input)
        form.addRow("Position", self.position_input)
        form.addRow("Agency", self.agency_input)
        form.addRow("Assigned Devices", self.assigned_devices_input)

        self.message_label = QLabel("", self)
        self.message_label.setObjectName("personEditorMessage")
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: #155e75;")

        button_row = QHBoxLayout()
        self.apply_button = QPushButton("Apply Changes", self)
        self.apply_button.setObjectName("applyPersonChangesButton")
        self.reset_button = QPushButton("Reset", self)
        self.reset_button.setObjectName("resetPersonButton")
        self.new_button = QPushButton("New Person", self)
        self.new_button.setObjectName("newPersonButton")
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
        self.reset_button.clicked.connect(lambda: self.load_person())
        self.new_button.clicked.connect(self.create_new_person)
        self.load_person()

    @property
    def person(self) -> Person:
        """Return the person currently being edited."""
        return self._person

    def bind_incident(self, incident: Incident) -> None:
        """Switch the editor to a different incident and ensure it has a person."""
        self._incident = incident
        self.load_person()

    def load_person(self, person: Person | None = None) -> None:
        """Populate the form from the current person."""
        if person is not None:
            self._person = person
            if not self._contains_person(self._person):
                self._incident.personnel.append(self._person)
        elif not self._contains_person(self._person):
            self._person = self._ensure_person()

        self.name_input.setText(self._person.name)
        self.position_input.setText(self._person.position)
        self.agency_input.setText(self._person.agency)
        self.assigned_devices_input.setText(
            ", ".join(device.hostname for device in self._person.assigned_devices)
        )
        self._refresh_summary()
        self.message_label.setText("")

    def sync_from_model(self) -> None:
        """Refresh derived labels without clearing the current feedback message."""
        self._refresh_summary()

    def create_new_person(self) -> None:
        """Create a fresh person record under the active incident."""
        self._person = Person("Untitled Person")
        self._incident.personnel.append(self._person)
        self.load_person(self._person)
        self.message_label.setText("New person created in memory.")
        self.person_updated.emit(self._incident)

    def apply_changes(self) -> None:
        """Validate and apply the form values to the person model."""
        name = self.name_input.text().strip()
        if not name:
            self.message_label.setText("Person name is required.")
            return

        self._person.name = name
        self._person.position = self.position_input.text().strip()
        self._person.agency = self.agency_input.text().strip()
        assigned_device_names = [
            hostname.strip()
            for hostname in self.assigned_devices_input.text().split(",")
            if hostname.strip()
        ]
        assigned_devices = []
        for hostname in assigned_device_names:
            device = self._incident.find_device(hostname)
            if device is None:
                self.message_label.setText(f"Device '{hostname}' not found.")
                return
            if device not in assigned_devices:
                assigned_devices.append(device)
        self._person.assigned_devices = assigned_devices
        self._person.touch()
        self._refresh_summary()
        self.message_label.setText("Person updated in memory.")
        self.person_updated.emit(self._incident)

    def _ensure_person(self) -> Person:
        """Return the primary person, creating one if the incident is empty."""
        if self._incident.personnel:
            return self._incident.personnel[0]

        person = Person("Alex Morgan")
        self._incident.personnel.append(person)
        return person

    def _refresh_summary(self) -> None:
        """Refresh the summary banner from the current person."""
        self.summary_label.setText(
            f"Editing {self._person.name} for {self._incident.summary()}"
        )

    def _contains_person(self, person: Person) -> bool:
        """Return True when the incident already owns the given person by identity."""
        return any(existing is person for existing in self._incident.personnel)
