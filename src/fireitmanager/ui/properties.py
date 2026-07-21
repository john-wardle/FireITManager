"""Properties dock content for the FireIT Manager workspace."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PropertiesWidget(QWidget):
    """Display selection details from the incident explorer."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("propertiesWidget")

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
