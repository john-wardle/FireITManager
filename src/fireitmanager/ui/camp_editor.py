"""Camp editor widget for the FireIT Manager workspace."""

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


class CampEditorWidget(QWidget):
    """Manual entry form for the primary camp in the active incident."""

    camp_updated = Signal(object)

    def __init__(self, incident: Incident, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("campEditorWidget")
        self._incident = incident
        self._camp = self._ensure_camp()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        title = QLabel("Camp Editor", self)
        title.setObjectName("campEditorTitle")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")

        self.summary_label = QLabel("", self)
        self.summary_label.setObjectName("campEditorSummary")
        self.summary_label.setWordWrap(True)

        form = QFormLayout()
        self.name_input = QLineEdit(self)
        self.name_input.setObjectName("campNameInput")

        self.building_count_value = QLabel("0", self)
        self.building_count_value.setObjectName("campBuildingCountValue")
        self.network_count_value = QLabel("0", self)
        self.network_count_value.setObjectName("campNetworkCountValue")

        form.addRow("Camp Name", self.name_input)

        counts_form = QFormLayout()
        counts_form.addRow("Buildings", self.building_count_value)
        counts_form.addRow("Networks", self.network_count_value)

        self.message_label = QLabel("", self)
        self.message_label.setObjectName("campEditorMessage")
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: #0f766e;")

        button_row = QHBoxLayout()
        self.apply_button = QPushButton("Apply Changes", self)
        self.apply_button.setObjectName("applyCampChangesButton")
        self.reset_button = QPushButton("Reset", self)
        self.reset_button.setObjectName("resetCampButton")
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
        self.reset_button.clicked.connect(lambda: self.load_camp())
        self.load_camp()

    @property
    def camp(self) -> Camp:
        """Return the camp currently being edited."""
        return self._camp

    def load_camp(self, camp: Camp | None = None) -> None:
        """Populate the form from the current camp."""
        if camp is not None:
            self._camp = camp
        self._camp = self._ensure_camp()
        self.name_input.setText(self._camp.name)
        self._refresh_counts()
        self._refresh_summary()
        self.message_label.setText("")

    def sync_from_model(self) -> None:
        """Refresh derived labels without clearing the current feedback message."""
        self._refresh_counts()
        self._refresh_summary()

    def bind_incident(self, incident: Incident) -> None:
        """Switch the editor to a different incident and ensure it has a camp."""
        self._incident = incident
        self._camp = self._ensure_camp()
        self.load_camp(self._camp)

    def apply_changes(self) -> None:
        """Validate and apply the form values to the camp model."""
        name = self.name_input.text().strip()
        if not name:
            self.message_label.setText("Camp name is required.")
            return

        self._camp.name = name
        self._camp.touch()
        self._refresh_summary()
        self.message_label.setText("Camp updated in memory.")
        self.camp_updated.emit(self._incident)

    def _ensure_camp(self) -> Camp:
        """Return the primary camp, creating one if the incident is empty."""
        if self._incident.camps:
            return self._incident.camps[0]

        camp = Camp("Base Camp")
        self._incident.add_camp(camp)
        return camp

    def _refresh_summary(self) -> None:
        """Refresh the summary banner from the current camp."""
        self.summary_label.setText(
            f"Editing {self._camp.name} for {self._incident.summary()}"
        )

    def _refresh_counts(self) -> None:
        """Refresh the related camp counts."""
        self.building_count_value.setText(str(len(self._camp.buildings)))
        self.network_count_value.setText(str(len(self._camp.networks)))
