"""Incident editor widget for the FireIT Manager workspace."""

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


class IncidentEditorWidget(QWidget):
    """Manual entry form for the active incident record."""

    incident_updated = Signal(object)
    incident_created = Signal(object)

    def __init__(self, incident: Incident, parent=None, window=None) -> None:
        super().__init__(parent)
        self.setObjectName("incidentEditorWidget")
        self._incident = incident
        self._window = window

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        # Add file operation toolbar at the top
        file_toolbar = QHBoxLayout()
        file_toolbar.setSpacing(8)
        file_toolbar.setContentsMargins(0, 0, 0, 0)

        new_incident_button = QPushButton("New Incident", self)
        new_incident_button.setObjectName("newIncidentToolbarButton")
        new_incident_button.setMaximumWidth(120)
        new_incident_button.clicked.connect(self._handle_new_incident_toolbar)

        open_button = QPushButton("Open", self)
        open_button.setObjectName("openIncidentToolbarButton")
        open_button.setMaximumWidth(80)
        open_button.clicked.connect(self._handle_open_toolbar)

        save_button = QPushButton("Save", self)
        save_button.setObjectName("saveIncidentToolbarButton")
        save_button.setMaximumWidth(80)
        save_button.clicked.connect(self._handle_save_toolbar)

        save_as_button = QPushButton("Save As", self)
        save_as_button.setObjectName("saveAsIncidentToolbarButton")
        save_as_button.setMaximumWidth(100)
        save_as_button.clicked.connect(self._handle_save_as_toolbar)

        file_toolbar.addWidget(new_incident_button)
        file_toolbar.addWidget(open_button)
        file_toolbar.addWidget(save_button)
        file_toolbar.addWidget(save_as_button)
        file_toolbar.addStretch(1)

        root_layout.addLayout(file_toolbar)

        title = QLabel("Incident Editor", self)
        title.setObjectName("incidentEditorTitle")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")

        self.summary_label = QLabel("", self)
        self.summary_label.setObjectName("incidentEditorSummary")
        self.summary_label.setWordWrap(True)

        form = QFormLayout()
        form.setLabelAlignment(form.labelAlignment())

        self.name_input = QLineEdit(self)
        self.name_input.setObjectName("incidentNameInput")
        self.number_input = QLineEdit(self)
        self.number_input.setObjectName("incidentNumberInput")
        self.agency_input = QLineEdit(self)
        self.agency_input.setObjectName("incidentAgencyInput")
        self.period_input = QLineEdit(self)
        self.period_input.setObjectName("operationalPeriodInput")

        form.addRow("Incident Name", self.name_input)
        form.addRow("Incident Number", self.number_input)
        form.addRow("Agency", self.agency_input)
        form.addRow("Operational Period", self.period_input)

        self.camp_count_label = QLabel("0", self)
        self.camp_count_label.setObjectName("campCountValue")
        self.personnel_count_label = QLabel("0", self)
        self.personnel_count_label.setObjectName("personnelCountValue")
        self.asset_count_label = QLabel("0", self)
        self.asset_count_label.setObjectName("assetCountValue")

        counts_form = QFormLayout()
        counts_form.addRow("Camps", self.camp_count_label)
        counts_form.addRow("Personnel", self.personnel_count_label)
        counts_form.addRow("Assets", self.asset_count_label)

        self.message_label = QLabel("", self)
        self.message_label.setObjectName("incidentEditorMessage")
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: #7c2d12;")

        button_row = QHBoxLayout()
        self.apply_button = QPushButton("Apply Changes", self)
        self.apply_button.setObjectName("applyIncidentChangesButton")
        self.reset_button = QPushButton("Reset", self)
        self.reset_button.setObjectName("resetIncidentButton")
        button_row.addWidget(self.apply_button)
        button_row.addWidget(self.reset_button)
        button_row.addStretch(1)

        root_layout.addWidget(title)
        root_layout.addWidget(self.summary_label)
        root_layout.addLayout(form)
        root_layout.addLayout(counts_form)
        root_layout.addWidget(self.message_label)
        root_layout.addLayout(button_row)
        root_layout.addStretch(1)

        self.apply_button.clicked.connect(self.apply_changes)
        self.reset_button.clicked.connect(lambda: self.load_incident())
        self.load_incident()

    def _handle_new_incident_toolbar(self) -> None:
        """Handle new incident from toolbar."""
        self.create_new_incident()
        if self._window is not None:
            self._window.show_incident_editor()

    def _handle_open_toolbar(self) -> None:
        """Handle open from toolbar."""
        if self._window is not None:
            self._window.load_workspace()

    def _handle_save_toolbar(self) -> None:
        """Handle save from toolbar."""
        if self._window is not None:
            self._window.save_workspace()

    def _handle_save_as_toolbar(self) -> None:
        """Handle save as from toolbar."""
        if self._window is not None:
            self._window.save_workspace_as()

    @property
    def incident(self) -> Incident:
        """Return the incident currently being edited."""
        return self._incident

    def load_incident(self, incident: Incident | None = None) -> None:
        """Populate the form from the current incident."""
        if incident is not None:
            self._incident = incident

        self.name_input.setText(self._incident.name)
        self.number_input.setText(self._incident.incident_number)
        self.agency_input.setText(self._incident.agency)
        self.period_input.setText(self._incident.operational_period)
        self._refresh_counts()
        self._refresh_summary()
        self.message_label.setText("")

    def sync_from_model(self) -> None:
        """Refresh derived labels without discarding the user's feedback message."""
        self._refresh_counts()
        self._refresh_summary()

    def create_new_incident(self) -> None:
        """Create a fresh incident record for manual entry."""
        incident = Incident("Untitled Incident")
        self.load_incident(incident)
        self.message_label.setText("New incident created in memory.")
        self.incident_created.emit(self._incident)

    def apply_changes(self) -> None:
        """Validate and apply the form values to the incident model."""
        name = self.name_input.text().strip()
        if not name:
            self.message_label.setText("Incident name is required.")
            return

        self._incident.name = name
        self._incident.incident_number = self.number_input.text().strip()
        self._incident.agency = self.agency_input.text().strip()
        self._incident.operational_period = self.period_input.text().strip()
        self._incident.touch()
        self._refresh_summary()
        self.message_label.setText("Incident updated in memory.")
        self.incident_updated.emit(self._incident)

    def _refresh_summary(self) -> None:
        """Refresh the summary banner from the incident model."""
        self.summary_label.setText(f"Editing {self._incident.summary()}")

    def _refresh_counts(self) -> None:
        """Refresh the related object counts."""
        self.camp_count_label.setText(str(len(self._incident.camps)))
        self.personnel_count_label.setText(str(len(self._incident.personnel)))
        self.asset_count_label.setText(str(len(self._incident.assets)))
