"""Central canvas widget for the FireIT Manager application."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from fireitmanager.models.incident import Incident
from fireitmanager.canvas.scene import CanvasScene
from fireitmanager.canvas.view import CanvasView


class CampCanvas(CanvasView):
    """Central workspace for incident site-map and network layout."""

    site_item_selected = Signal(str, str, str, str, str)
    site_object_selected = Signal(object)

    def __init__(self, incident: Incident | None = None) -> None:
        self.site_scene = CanvasScene(incident)
        super().__init__(self.site_scene)
        self.setObjectName("campCanvas")
        self._title_base_point_size = 16.0
        self._summary_base_point_size = 11.0
        self._summary_labels: list[QLabel] = []
        self.title_overlay = QLabel(self.viewport())
        self.title_overlay.setObjectName("siteMapTitleOverlay")
        self.title_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.title_overlay.setStyleSheet(
            "color: #f3f6fb;"
            "background-color: rgba(19, 23, 29, 190);"
            "border: 1px solid rgba(148, 163, 184, 120);"
            "border-radius: 4px;"
            "padding: 6px 10px;"
        )
        self.summary_overlay = QWidget(self.viewport())
        self.summary_overlay.setObjectName("siteMapSummaryOverlay")
        self.summary_overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.summary_overlay.setStyleSheet(
            "background-color: rgba(19, 23, 29, 175);"
            "border: 1px solid rgba(148, 163, 184, 105);"
            "border-radius: 4px;"
        )
        self.summary_layout = QVBoxLayout(self.summary_overlay)
        self.summary_layout.setContentsMargins(10, 10, 10, 10)
        self.summary_layout.setSpacing(5)
        self.site_scene.site_item_selected.connect(self.site_item_selected)
        self.site_scene.site_object_selected.connect(self.site_object_selected)
        self.zoom_changed.connect(self._update_overlay_scale)
        self._set_title(incident)
        self._set_summary(incident)

    def load_incident(self, incident: Incident, *, center: bool = True) -> None:
        """Refresh the site map from the active incident graph."""
        self.site_scene.load_incident(incident)
        self._set_title(incident)
        self._set_summary(incident)
        if center:
            self.center_scene(record_history=False)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API name
        super().resizeEvent(event)
        self._position_title_overlay()
        self._position_summary_overlay()

    def _set_title(self, incident: Incident | None) -> None:
        if incident is None:
            self.title_overlay.setText("Site Map")
        else:
            self.title_overlay.setText(f"Site Map - {incident.summary()}")
        self._update_overlay_scale(self.zoom_factor)

    def _set_summary(self, incident: Incident | None) -> None:
        self._clear_summary()
        if incident is None:
            self._add_summary_label("No incident loaded", heading=True)
        elif not incident.camps:
            self._add_summary_label("No camps available", heading=True)
        else:
            for camp_index, camp in enumerate(incident.camps):
                if camp_index:
                    self._add_summary_spacing()
                device_count = sum(len(building.devices) for building in camp.buildings)
                self._add_summary_label(camp.name, heading=True)
                self._add_summary_label(
                    f"{len(camp.buildings)} location(s), {device_count} device(s)"
                )
                for network in camp.networks:
                    self._add_summary_label(
                        f"{network.name}: {len(network.devices)} device(s), "
                        f"{len(network.cables)} cable(s)"
                    )
            if incident.assets:
                self._add_summary_spacing()
                self._add_summary_label(f"Inventory: {len(incident.assets)} asset(s)")
        self._update_overlay_scale(self.zoom_factor)

    def _update_overlay_scale(self, zoom_factor: float) -> None:
        clamped_zoom = max(0.75, min(1.6, zoom_factor))
        font = self.title_overlay.font()
        font.setPointSizeF(self._title_base_point_size * clamped_zoom)
        font.setBold(True)
        self.title_overlay.setFont(font)
        for label in self._summary_labels:
            summary_font = label.font()
            base_size = self._summary_base_point_size
            if label.property("summaryHeading"):
                base_size += 3.0
            summary_font.setPointSizeF(base_size * clamped_zoom)
            summary_font.setBold(bool(label.property("summaryHeading")))
            label.setFont(summary_font)
        self._position_title_overlay()
        self._position_summary_overlay()

    def _position_title_overlay(self) -> None:
        margin = 12
        max_width = max(120, self.viewport().width() - (margin * 2))
        self.title_overlay.setMaximumWidth(max_width)
        self.title_overlay.adjustSize()
        width = min(self.title_overlay.sizeHint().width(), max_width)
        height = self.title_overlay.sizeHint().height()
        self.title_overlay.setGeometry(margin, margin, width, height)
        self.title_overlay.raise_()

    def _position_summary_overlay(self) -> None:
        margin = 12
        top = self.title_overlay.geometry().bottom() + 12
        max_width = max(180, min(340, self.viewport().width() // 3))
        max_height = max(120, self.viewport().height() - top - margin)
        self.summary_overlay.setMaximumWidth(max_width)
        self.summary_overlay.adjustSize()
        width = min(max(self.summary_overlay.sizeHint().width(), 180), max_width)
        height = min(self.summary_overlay.sizeHint().height(), max_height)
        self.summary_overlay.setGeometry(margin, top, width, height)
        self.summary_overlay.raise_()

    def _clear_summary(self) -> None:
        while self.summary_layout.count():
            item = self.summary_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._summary_labels = []

    def _add_summary_label(self, text: str, *, heading: bool = False) -> None:
        label = QLabel(text, self.summary_overlay)
        label.setObjectName("siteMapSummaryHeading" if heading else "siteMapSummaryLine")
        label.setProperty("summaryHeading", heading)
        label.setWordWrap(True)
        label.setStyleSheet("color: #f3f6fb;" if heading else "color: #cbd5e1;")
        self.summary_layout.addWidget(label)
        self._summary_labels.append(label)

    def _add_summary_spacing(self) -> None:
        self.summary_layout.addSpacing(8)
