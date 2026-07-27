"""Canvas widget wrapper with view control toolbar."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from fireitmanager.models.incident import Incident
from fireitmanager.ui.canvas import CampCanvas


class CanvasWithControlsWidget(QWidget):
    """Canvas wrapped with bottom control toolbar."""

    def __init__(self, incident: Incident | None = None, window: QMainWindow | None = None) -> None:
        super().__init__()
        self.setObjectName("canvasWithControlsWidget")
        self.canvas = CampCanvas(incident)
        self.window = window

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Add the canvas to fill available space
        root_layout.addWidget(self.canvas, 1)

        # Create bottom control toolbar
        button_bar = QWidget(self)
        button_bar.setObjectName("canvasControlBar")
        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(0, 8, 0, 8)
        button_layout.setSpacing(8)
        button_layout.addStretch(1)  # Left spacer

        # Create buttons
        undo_button = QPushButton("Undo", self)
        undo_button.setObjectName("undoButton")
        undo_button.setMaximumWidth(100)
        undo_button.clicked.connect(self.canvas.undo)

        redo_button = QPushButton("Redo", self)
        redo_button.setObjectName("redoButton")
        redo_button.setMaximumWidth(100)
        redo_button.clicked.connect(self.canvas.redo)

        zoom_in_button = QPushButton("Zoom In", self)
        zoom_in_button.setObjectName("zoomInButton")
        zoom_in_button.setMaximumWidth(100)
        zoom_in_button.clicked.connect(self.canvas.zoom_in)

        zoom_out_button = QPushButton("Zoom Out", self)
        zoom_out_button.setObjectName("zoomOutButton")
        zoom_out_button.setMaximumWidth(100)
        zoom_out_button.clicked.connect(self.canvas.zoom_out)

        center_button = QPushButton("Center View", self)
        center_button.setObjectName("centerViewButton")
        center_button.setMaximumWidth(100)
        center_button.clicked.connect(self.canvas.center_scene)

        # Add buttons to layout
        button_layout.addWidget(undo_button)
        button_layout.addWidget(redo_button)
        button_layout.addWidget(zoom_in_button)
        button_layout.addWidget(zoom_out_button)
        button_layout.addWidget(center_button)

        button_layout.addStretch(1)  # Right spacer

        # Add button bar to root layout
        root_layout.addWidget(button_bar)

    def undo(self) -> None:
        """Proxy undo to canvas."""
        self.canvas.undo()

    def redo(self) -> None:
        """Proxy redo to canvas."""
        self.canvas.redo()

    def zoom_in(self) -> None:
        """Proxy zoom_in to canvas."""
        self.canvas.zoom_in()

    def zoom_out(self) -> None:
        """Proxy zoom_out to canvas."""
        self.canvas.zoom_out()

    def center_scene(self) -> None:
        """Proxy center_scene to canvas."""
        self.canvas.center_scene()
