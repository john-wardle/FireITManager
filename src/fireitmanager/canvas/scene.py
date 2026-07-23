"""Graphics scene for the FireIT Manager site map workspace."""

from __future__ import annotations

from math import floor
from pathlib import Path

from PySide6.QtCore import QLineF, QPointF, QRectF, QSizeF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsObject,
    QGraphicsScene,
    QGraphicsTextItem,
    QStyleOptionGraphicsItem,
    QWidget,
)

from fireitmanager.canvas.constants import (
    GRID_MAJOR_COLOR,
    GRID_MINOR_COLOR,
    MAJOR_GRID_SIZE,
    MINOR_GRID_SIZE,
    SCENE_RECT,
    Z_BUILDING,
    Z_DEVICE,
    Z_TEXT,
)
from fireitmanager.models.building import Building
from fireitmanager.models.cable import Cable
from fireitmanager.models.device import Device
from fireitmanager.models.enums import CableType, DeviceStatus, DeviceType
from fireitmanager.models.incident import Incident


class CanvasScene(QGraphicsScene):
    """Scene with a grid background and draggable incident network items."""

    site_item_selected = Signal(str, str, str, str, str)
    site_object_selected = Signal(object)

    def __init__(self, incident: Incident | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setSceneRect(SCENE_RECT)
        self._layout_positions: dict[str, QPointF] = {}
        self._layout_sizes: dict[str, QSizeF] = {}
        self._layout_anchors: dict[str, str] = {}
        self._device_items: dict[str, SiteMapNodeItem] = {}
        self._building_items: dict[str, SiteMapNodeItem] = {}
        self._connection_items: list[SiteMapCableItem] = []
        self.selectionChanged.connect(self._emit_selected_item)

        if incident is None:
            self._build_empty_state()
        else:
            self.load_incident(incident)

    def load_incident(self, incident: Incident) -> None:
        """Populate the scene from the active incident graph."""
        self.clear()
        self._device_items = {}
        self._building_items = {}
        self._connection_items = []

        if not incident.camps:
            self._add_centered_text(
                "No camps available",
                y=-80,
                point_size=14,
                bold=False,
                color=QColor(220, 226, 235),
            )
            return

        for camp_index, camp in enumerate(incident.camps):
            camp_origin = QPointF(-430.0, -400.0 + (camp_index * 520.0))
            self._add_title(camp.name, camp_origin, point_size=16)

            for building_index, building in enumerate(camp.buildings):
                building_position = QPointF(
                    camp_origin.x() + (building_index * 430.0),
                    camp_origin.y() + 62.0,
                )
                self._add_building(building, camp.name, building_position)

            for network_index, network in enumerate(camp.networks):
                network_label = self.addText(
                    f"{network.name}: {len(network.devices)} device(s), "
                    f"{len(network.cables)} cable(s)"
                )
                font = network_label.font()
                font.setPointSize(11)
                font.setBold(True)
                network_label.setFont(font)
                network_label.setDefaultTextColor(QColor(205, 214, 226))
                network_label.setPos(
                    camp_origin.x(),
                    camp_origin.y() + 305.0 + (network_index * 30.0),
                )
                network_label.setZValue(Z_TEXT)

                if network.cables:
                    for cable in network.cables:
                        self._add_cable(cable, network.name)
                else:
                    self._add_membership_lines(network.devices, network.name)

    def remember_item_position(self, item: SiteMapNodeItem) -> None:
        """Remember a dragged node position for the current session."""
        self._layout_positions[item.layout_key] = item.pos()

    def remember_item_size(self, item: SiteMapNodeItem) -> None:
        """Remember a resized node size for the current session."""
        self._layout_sizes[item.layout_key] = QSizeF(item.width, item.height)

    def map_content_rect(self) -> QRectF:
        """Return the bounds of the draggable site-map content."""
        bounds: QRectF | None = None
        for item in [*self._building_items.values(), *self._device_items.values()]:
            item_bounds = item.sceneBoundingRect()
            bounds = item_bounds if bounds is None else bounds.united(item_bounds)

        if bounds is None:
            return self.itemsBoundingRect()
        return bounds.adjusted(-120.0, -120.0, 120.0, 160.0)

    def refresh_connections_for_item(self, item: SiteMapNodeItem) -> None:
        """Update all cable lines attached to a moved map item."""
        self.remember_item_position(item)
        if item.kind == "building":
            self.refresh_all_connections()
            return

        for connection in self._connection_items:
            if connection.source_item is item or connection.destination_item is item:
                connection.refresh()

    def refresh_all_connections(self) -> None:
        """Update every cable line in the scene."""
        for connection in self._connection_items:
            connection.refresh()

    def anchor_item_to_container(self, item: SiteMapNodeItem) -> None:
        """Anchor a non-location item to the location containing its center point."""
        if item.kind == "building":
            return

        center = item.sceneBoundingRect().center()
        for building in self._building_items.values():
            if building.sceneBoundingRect().contains(center):
                self._anchor_item_to_building(item, building)
                return

        self.detach_item_from_container(item)

    def anchor_items_inside(self, building: SiteMapNodeItem) -> None:
        """Anchor all top-level equipment nodes currently inside a location box."""
        if building.kind != "building":
            return

        for item in self._device_items.values():
            if item is building or item.parentItem() is building:
                continue
            if building.sceneBoundingRect().contains(item.sceneBoundingRect().center()):
                self._anchor_item_to_building(item, building)

    def detach_item_from_container(self, item: SiteMapNodeItem) -> None:
        """Detach an item from its parent location while preserving scene position."""
        if item.kind == "building" or item.parentItem() is None:
            return

        scene_pos = item.scenePos()
        item.setParentItem(None)
        item.setPos(scene_pos)
        item.setZValue(Z_DEVICE)
        self._layout_anchors.pop(item.layout_key, None)
        self.remember_item_position(item)
        self.refresh_connections_for_item(item)

    def _anchor_item_to_building(
        self,
        item: SiteMapNodeItem,
        building: SiteMapNodeItem,
    ) -> None:
        """Parent an equipment node to a building while preserving its scene position."""
        scene_pos = item.scenePos()
        item.setParentItem(building)
        item.setPos(building.mapFromScene(scene_pos))
        item.setZValue(Z_DEVICE)
        self._layout_anchors[item.layout_key] = building.layout_key
        self.remember_item_position(item)
        self.refresh_connections_for_item(item)

    def _build_empty_state(self) -> None:
        """Create the centered card shown before data is loaded."""
        card = self.addRect(
            QRectF(-300.0, -170.0, 600.0, 340.0),
            QPen(QColor(72, 82, 95), 1.5),
            QColor(24, 29, 36),
        )
        card.setZValue(10)

        self._add_centered_text(
            "Site Map",
            y=-120,
            point_size=22,
            bold=True,
            color=QColor(245, 247, 250),
        )
        self._add_centered_text(
            "No incident loaded",
            y=-80,
            point_size=14,
            bold=False,
            color=QColor(183, 193, 204),
        )
        self._add_centered_text(
            "Load an incident to place buildings, devices, and network links.",
            y=-25,
            point_size=11,
            bold=False,
            color=QColor(214, 220, 228),
        )
        self._add_centered_text(
            "- Drag device icons to arrange the network map.",
            y=18,
            point_size=11,
            bold=False,
            color=QColor(214, 220, 228),
        )
        self._add_centered_text(
            "- Select an item to view details in Properties.",
            y=44,
            point_size=11,
            bold=False,
            color=QColor(214, 220, 228),
        )
        self._add_centered_text(
            "- Cable lines follow devices as they move.",
            y=70,
            point_size=11,
            bold=False,
            color=QColor(214, 220, 228),
        )

    def _add_building(self, building: Building, camp_name: str, position: QPointF) -> None:
        layout_key = f"building:{building.building_id}"
        size = self._size_for(layout_key, QSizeF(320.0, 210.0))
        item = SiteMapNodeItem(
            layout_key=layout_key,
            label=building.name,
            kind="building",
            path=f"Workspace / Camps / {camp_name} / {building.name}",
            description="Building or operational structure on the incident site map.",
            details=(
                f"Type: {building.building_type.value}\n"
                f"Devices: {len(building.devices)}"
            ),
            width=size.width(),
            height=size.height(),
            accent=QColor("#d6b25f"),
            icon_name=_building_icon_name(building),
            resizable=True,
            target=building,
        )
        item.setPos(self._position_for(layout_key, position))
        item.setZValue(Z_BUILDING)
        self.addItem(item)
        self._building_items[str(building.building_id)] = item

        for device_index, device in enumerate(building.devices):
            column = device_index % 3
            row = device_index // 3
            device_position = QPointF(
                position.x() + 30.0 + (column * 142.0),
                position.y() + 76.0 + (row * 96.0),
            )
            self._add_device(device, camp_name, building.name, device_position, item)

    def _add_device(
        self,
        device: Device,
        camp_name: str,
        building_name: str,
        position: QPointF,
        building_item: SiteMapNodeItem | None = None,
    ) -> None:
        layout_key = f"device:{device.device_id}"
        details = [
            f"Type: {device.device_type.value}",
            f"Status: {device.status.value}",
        ]
        if device.ip_address:
            details.append(f"IP: {device.ip_address}")
        if device.manufacturer or device.model:
            details.append(f"Hardware: {device.manufacturer} {device.model}".strip())

        item = SiteMapNodeItem(
            layout_key=layout_key,
            label=device.hostname,
            kind="device",
            path=(
                f"Workspace / Camps / {camp_name} / {building_name} / "
                f"{device.hostname}"
            ),
            description="Network device placed on the incident site map.",
            details="\n".join(details),
            width=130.0,
            height=86.0,
            accent=_device_accent(device.device_type),
            device_type=device.device_type,
            status=device.status,
            icon_name=_device_icon_name(device.device_type),
            target=device,
        )
        item.setZValue(Z_DEVICE)

        if building_item is not None:
            self._layout_anchors.setdefault(layout_key, building_item.layout_key)
            item.setParentItem(building_item)
            local_position = building_item.mapFromScene(position)
            item.setPos(self._position_for(layout_key, local_position))
        else:
            item.setPos(self._position_for(layout_key, position))
            self.addItem(item)

        self._device_items[str(device.device_id)] = item

    def _add_cable(self, cable: Cable, network_name: str) -> None:
        if cable.source_device is None or cable.destination_device is None:
            return
        source = self._device_items.get(str(cable.source_device.device_id))
        destination = self._device_items.get(str(cable.destination_device.device_id))
        if source is None or destination is None:
            return

        item = SiteMapCableItem(
            source,
            destination,
            f"{network_name} / {cable.cable_type.value}",
            cable.cable_type,
        )
        self.addItem(item)
        self._connection_items.append(item)
        item.refresh()

    def _add_membership_lines(self, devices: list[Device], network_name: str) -> None:
        if len(devices) < 2:
            return
        source = self._device_items.get(str(devices[0].device_id))
        if source is None:
            return
        for device in devices[1:]:
            destination = self._device_items.get(str(device.device_id))
            if destination is None:
                continue
            item = SiteMapCableItem(
                source,
                destination,
                f"{network_name} membership",
                CableType.OTHER,
                dashed=True,
            )
            self.addItem(item)
            self._connection_items.append(item)
            item.refresh()

    def _position_for(self, layout_key: str, fallback: QPointF) -> QPointF:
        position = self._layout_positions.get(layout_key)
        if position is None:
            self._layout_positions[layout_key] = QPointF(fallback)
            return fallback
        return QPointF(position)

    def _size_for(self, layout_key: str, fallback: QSizeF) -> QSizeF:
        size = self._layout_sizes.get(layout_key)
        if size is None:
            self._layout_sizes[layout_key] = QSizeF(fallback)
            return fallback
        return QSizeF(size)

    def _add_title(self, text: str, position: QPointF, *, point_size: int) -> None:
        title = self.addText(text)
        font = title.font()
        font.setPointSize(point_size)
        font.setBold(True)
        title.setFont(font)
        title.setDefaultTextColor(QColor(239, 243, 248))
        title.setPos(position)
        title.setZValue(Z_TEXT)

    def _add_centered_text(
        self,
        text: str,
        *,
        y: float,
        point_size: int,
        bold: bool,
        color: QColor,
    ) -> QGraphicsTextItem:
        """Add a centered text item to the scene."""
        item = self.addText(text)
        font: QFont = item.font()
        font.setPointSize(point_size)
        font.setBold(bold)
        item.setFont(font)
        item.setDefaultTextColor(color)
        bounds = item.boundingRect()
        item.setPos(-bounds.width() / 2.0, y)
        item.setZValue(11)
        return item

    def _emit_selected_item(self) -> None:
        for item in self.selectedItems():
            if isinstance(item, SiteMapNodeItem):
                self.site_item_selected.emit(*item.site_details())
                self.site_object_selected.emit(item.target)
                return
        self.site_object_selected.emit(None)

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """Draw the grid background for the visible scene area."""
        painter.fillRect(rect, QColor(19, 23, 29))

        minor_pen = QPen(GRID_MINOR_COLOR)
        minor_pen.setWidthF(0.0)
        major_pen = QPen(GRID_MAJOR_COLOR)
        major_pen.setWidthF(0.0)

        start_x = floor(rect.left() / MINOR_GRID_SIZE) * MINOR_GRID_SIZE
        end_x = floor(rect.right() / MINOR_GRID_SIZE) * MINOR_GRID_SIZE
        start_y = floor(rect.top() / MINOR_GRID_SIZE) * MINOR_GRID_SIZE
        end_y = floor(rect.bottom() / MINOR_GRID_SIZE) * MINOR_GRID_SIZE

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)

        for x in range(start_x, end_x + MINOR_GRID_SIZE, MINOR_GRID_SIZE):
            painter.setPen(major_pen if x % MAJOR_GRID_SIZE == 0 else minor_pen)
            painter.drawLine(x, rect.top(), x, rect.bottom())

        for y in range(start_y, end_y + MINOR_GRID_SIZE, MINOR_GRID_SIZE):
            painter.setPen(major_pen if y % MAJOR_GRID_SIZE == 0 else minor_pen)
            painter.drawLine(rect.left(), y, rect.right(), y)

        painter.restore()


class SiteMapNodeItem(QGraphicsObject):
    """Selectable and draggable site-map node for buildings and devices."""

    def __init__(
        self,
        *,
        layout_key: str,
        label: str,
        kind: str,
        path: str,
        description: str,
        details: str,
        width: float,
        height: float,
        accent: QColor,
        device_type: DeviceType | None = None,
        status: DeviceStatus | None = None,
        icon_name: str | None = None,
        resizable: bool = False,
        target: object | None = None,
    ) -> None:
        super().__init__()
        self.layout_key = layout_key
        self.label = label
        self.kind = kind
        self.path = path
        self.description = description
        self.details = details
        self.width = width
        self.height = height
        self.accent = accent
        self.device_type = device_type
        self.status = status
        self.icon_name = icon_name
        self.icon_renderer = _load_icon_renderer(icon_name)
        self.resizable = resizable
        self.target = target
        self._is_resizing = False
        self._resize_start_scene_pos = QPointF()
        self._resize_start_size = QSizeF(width, height)
        self._min_size = QSizeF(260.0, 170.0) if resizable else QSizeF(width, height)
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.OpenHandCursor)

    def boundingRect(self) -> QRectF:  # noqa: N802 - Qt API name
        return QRectF(0.0, 0.0, self.width, self.height)

    def site_details(self) -> tuple[str, str, str, str, str]:
        return (self.label, self.kind, self.path, self.description, self.details)

    def connection_point(self) -> QPointF:
        bounds = self.boundingRect()
        return self.scenePos() + QPointF(bounds.width() / 2.0, bounds.height() / 2.0)

    def itemChange(self, change, value):  # noqa: N802 - Qt API name
        if change == QGraphicsItem.ItemPositionHasChanged:
            scene = self.scene()
            if hasattr(scene, "refresh_connections_for_item"):
                scene.refresh_connections_for_item(self)
        return super().itemChange(change, value)

    def resize_to(self, width: float, height: float) -> None:
        """Resize the node, respecting its minimum dimensions."""
        if not self.resizable:
            return

        new_width = max(self._min_size.width(), width)
        new_height = max(self._min_size.height(), height)
        if new_width == self.width and new_height == self.height:
            return

        self.prepareGeometryChange()
        self.width = new_width
        self.height = new_height
        scene = self.scene()
        if hasattr(scene, "remember_item_size"):
            scene.remember_item_size(self)
        if hasattr(scene, "refresh_connections_for_item"):
            scene.refresh_connections_for_item(self)
        self.update()

    def resize_handle_rect(self) -> QRectF:
        """Return the bottom-right resize handle bounds."""
        return QRectF(self.width - 28.0, self.height - 28.0, 20.0, 20.0)

    def hoverEnterEvent(self, event) -> None:  # noqa: N802 - Qt API name
        self.setCursor(Qt.ClosedHandCursor)
        super().hoverEnterEvent(event)

    def hoverMoveEvent(self, event) -> None:  # noqa: N802 - Qt API name
        if self.resizable and self.resize_handle_rect().contains(event.pos()):
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.ClosedHandCursor)
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event) -> None:  # noqa: N802 - Qt API name
        self.setCursor(Qt.OpenHandCursor)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt API name
        if self.resizable and self.resize_handle_rect().contains(event.pos()):
            self._is_resizing = True
            self._resize_start_scene_pos = event.scenePos()
            self._resize_start_size = QSizeF(self.width, self.height)
            self.setSelected(True)
            self.setCursor(Qt.SizeFDiagCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt API name
        if self._is_resizing:
            delta = event.scenePos() - self._resize_start_scene_pos
            self.resize_to(
                self._resize_start_size.width() + delta.x(),
                self._resize_start_size.height() + delta.y(),
            )
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt API name
        if self._is_resizing:
            self._is_resizing = False
            scene = self.scene()
            if hasattr(scene, "anchor_items_inside"):
                scene.anchor_items_inside(self)
            self.setCursor(Qt.OpenHandCursor)
            event.accept()
            return

        super().mouseReleaseEvent(event)
        scene = self.scene()
        if self.kind == "building" and hasattr(scene, "anchor_items_inside"):
            scene.anchor_items_inside(self)
        elif hasattr(scene, "anchor_item_to_container"):
            scene.anchor_item_to_container(self)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        del option, widget
        painter.setRenderHint(QPainter.Antialiasing)
        if self.kind == "building":
            self._paint_building(painter)
        else:
            self._paint_device(painter)

    def _paint_building(self, painter: QPainter) -> None:
        bounds = self.boundingRect()
        shadow = bounds.translated(4.0, 5.0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 55))
        painter.drawRoundedRect(shadow, 8.0, 8.0)

        fill = QColor("#f0d7a0")
        header = QColor(self.accent)
        border = QColor("#9e7e3f" if not self.isSelected() else "#3b82f6")
        painter.setBrush(fill)
        painter.setPen(QPen(border, 2.0 if self.isSelected() else 1.2))
        painter.drawRoundedRect(bounds, 8.0, 8.0)

        header_path = QPainterPath()
        header_path.addRoundedRect(QRectF(0.0, 0.0, bounds.width(), 42.0), 8.0, 8.0)
        painter.fillPath(header_path, header)
        painter.setPen(QPen(QColor("#8c6c31"), 1.0))
        painter.drawLine(QPointF(0.0, 42.0), QPointF(bounds.width(), 42.0))

        painter.setPen(QColor("#2d2618"))
        font = painter.font()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            QRectF(14.0, 10.0, bounds.width() - 28.0, 24.0),
            Qt.AlignLeft | Qt.AlignVCenter,
            self.label,
        )

        font.setPointSize(9)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor("#5f5138"))
        painter.drawText(
            QRectF(14.0, 58.0, bounds.width() - 96.0, 58.0),
            Qt.TextWordWrap,
            self.details,
        )

        icon_rect = QRectF(bounds.width() - 82.0, 62.0, 56.0, 56.0)
        if not self._paint_svg_icon(painter, icon_rect):
            painter.setBrush(QColor("#fff8e6"))
            painter.setPen(QPen(QColor("#9e7e3f"), 2.0))
            painter.drawRoundedRect(icon_rect, 8.0, 8.0)

        self._paint_resize_handle(painter)

    def _paint_device(self, painter: QPainter) -> None:
        bounds = self.boundingRect()
        shadow = bounds.translated(3.0, 4.0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 75))
        painter.drawRoundedRect(shadow, 7.0, 7.0)

        fill = QColor("#f8fafc")
        border = QColor("#94a3b8" if not self.isSelected() else "#3b82f6")
        painter.setBrush(fill)
        painter.setPen(QPen(border, 2.0 if self.isSelected() else 1.0))
        painter.drawRoundedRect(bounds, 7.0, 7.0)

        icon_rect = QRectF(8.0, 16.0, 48.0, 48.0)
        if not self._paint_svg_icon(painter, icon_rect):
            self._paint_device_icon(painter, icon_rect)

        painter.setPen(QColor("#1f2937"))
        font = painter.font()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            QRectF(64.0, 12.0, bounds.width() - 74.0, 32.0),
            Qt.TextWordWrap,
            self.label,
        )

        font.setPointSize(8)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor("#475569"))
        painter.drawText(
            QRectF(64.0, 49.0, bounds.width() - 74.0, 18.0),
            self.device_type.value if self.device_type is not None else "device",
        )

        painter.setBrush(_status_color(self.status))
        painter.setPen(QPen(QColor("#ffffff"), 1.0))
        painter.drawEllipse(QRectF(bounds.width() - 20.0, 10.0, 10.0, 10.0))

    def _paint_device_icon(self, painter: QPainter, rect: QRectF) -> None:
        painter.setPen(QPen(self.accent.darker(135), 2.0))
        painter.setBrush(self.accent)
        device_type = self.device_type or DeviceType.OTHER

        if device_type == DeviceType.ROUTER:
            painter.drawEllipse(rect)
            painter.setPen(QPen(QColor("#ffffff"), 1.6))
            painter.drawLine(
                rect.center() + QPointF(-12.0, 0.0),
                rect.center() + QPointF(12.0, 0.0),
            )
            painter.drawLine(
                rect.center() + QPointF(0.0, -12.0),
                rect.center() + QPointF(0.0, 12.0),
            )
        elif device_type == DeviceType.SWITCH:
            painter.drawRoundedRect(rect.adjusted(1.0, 8.0, -1.0, -8.0), 4.0, 4.0)
            painter.setBrush(QColor("#ffffff"))
            for index in range(4):
                painter.drawRect(
                    QRectF(
                        rect.left() + 7.0 + (index * 7.0),
                        rect.center().y() - 3.0,
                        4.0,
                        6.0,
                    )
                )
        elif device_type == DeviceType.WORKSTATION:
            painter.drawRoundedRect(rect.adjusted(2.0, 4.0, -2.0, -12.0), 3.0, 3.0)
            painter.drawRect(QRectF(rect.center().x() - 3.0, rect.bottom() - 12.0, 6.0, 8.0))
            painter.drawLine(rect.left() + 10.0, rect.bottom() - 3.0, rect.right() - 10.0, rect.bottom() - 3.0)
        elif device_type == DeviceType.SERVER:
            painter.drawRoundedRect(rect.adjusted(9.0, 1.0, -9.0, -1.0), 4.0, 4.0)
            painter.setPen(QPen(QColor("#ffffff"), 1.4))
            painter.drawLine(rect.left() + 14.0, rect.top() + 12.0, rect.right() - 14.0, rect.top() + 12.0)
            painter.drawLine(rect.left() + 14.0, rect.top() + 22.0, rect.right() - 14.0, rect.top() + 22.0)
        elif device_type == DeviceType.ACCESS_POINT:
            painter.drawEllipse(QRectF(rect.center().x() - 6.0, rect.center().y() - 6.0, 12.0, 12.0))
            painter.setPen(QPen(self.accent.darker(150), 2.0))
            painter.drawArc(rect.adjusted(5.0, 5.0, -5.0, -5.0), 35 * 16, 110 * 16)
            painter.drawArc(rect.adjusted(0.0, 0.0, 0.0, 0.0), 35 * 16, 110 * 16)
        elif device_type == DeviceType.PHONE:
            painter.drawRoundedRect(rect.adjusted(9.0, 1.0, -9.0, -1.0), 5.0, 5.0)
            painter.setBrush(QColor("#ffffff"))
            painter.drawEllipse(QRectF(rect.center().x() - 2.0, rect.bottom() - 8.0, 4.0, 4.0))
        else:
            diamond = QPainterPath()
            diamond.moveTo(rect.center().x(), rect.top())
            diamond.lineTo(rect.right(), rect.center().y())
            diamond.lineTo(rect.center().x(), rect.bottom())
            diamond.lineTo(rect.left(), rect.center().y())
            diamond.closeSubpath()
            painter.drawPath(diamond)

    def _paint_svg_icon(self, painter: QPainter, rect: QRectF) -> bool:
        if self.icon_renderer is None or not self.icon_renderer.isValid():
            return False

        painter.save()
        self.icon_renderer.render(painter, rect)
        painter.restore()
        return True

    def _paint_resize_handle(self, painter: QPainter) -> None:
        if not self.resizable:
            return

        handle = self.resize_handle_rect()
        painter.setPen(QPen(QColor("#8c6c31"), 1.4))
        painter.setBrush(QColor("#f8e6b5"))
        painter.drawRoundedRect(handle, 4.0, 4.0)
        painter.drawLine(
            handle.left() + 5.0,
            handle.bottom() - 4.0,
            handle.right() - 4.0,
            handle.top() + 5.0,
        )
        painter.drawLine(
            handle.left() + 10.0,
            handle.bottom() - 4.0,
            handle.right() - 4.0,
            handle.top() + 10.0,
        )


class SiteMapCableItem(QGraphicsLineItem):
    """Cable line that follows two draggable site-map nodes."""

    def __init__(
        self,
        source_item: SiteMapNodeItem,
        destination_item: SiteMapNodeItem,
        label: str,
        cable_type: CableType,
        *,
        dashed: bool = False,
    ) -> None:
        super().__init__()
        self.source_item = source_item
        self.destination_item = destination_item
        self.label = label
        self.cable_type = cable_type
        self.dashed = dashed
        self.setZValue(Z_DEVICE - 2)
        self.setAcceptedMouseButtons(Qt.NoButton)
        pen = QPen(_cable_color(cable_type), 3.0)
        if dashed:
            pen.setStyle(Qt.DashLine)
        self.setPen(pen)

    def refresh(self) -> None:
        self.setLine(
            QLineF(
                self.source_item.connection_point(),
                self.destination_item.connection_point(),
            )
        )


def _device_accent(device_type: DeviceType) -> QColor:
    colors = {
        DeviceType.ROUTER: QColor("#2563eb"),
        DeviceType.SWITCH: QColor("#0f766e"),
        DeviceType.ACCESS_POINT: QColor("#7c3aed"),
        DeviceType.SERVER: QColor("#475569"),
        DeviceType.WORKSTATION: QColor("#ea580c"),
        DeviceType.PHONE: QColor("#0891b2"),
        DeviceType.OTHER: QColor("#64748b"),
    }
    return colors.get(device_type, QColor("#64748b"))


def _device_icon_name(device_type: DeviceType) -> str:
    icons = {
        DeviceType.ROUTER: "router.svg",
        DeviceType.SWITCH: "network_switch.svg",
        DeviceType.ACCESS_POINT: "wifi_access_point.svg",
        DeviceType.SERVER: "server_tower.svg",
        DeviceType.WORKSTATION: "laptop.svg",
        DeviceType.PHONE: "voip_phone.svg",
        DeviceType.OTHER: "workstation_tower.svg",
    }
    return icons.get(device_type, "workstation_tower.svg")


def _building_icon_name(building: Building) -> str:
    name = building.name.lower()
    if "tent" in name or "staging" in name:
        return "it_staging_tent.svg"
    if "trailer" in name:
        return "command_post_trailer.svg"
    return "command_post.svg"


def _load_icon_renderer(icon_name: str | None) -> QSvgRenderer | None:
    if icon_name is None:
        return None
    icon_path = _icon_path(icon_name)
    if icon_path is None:
        return None
    renderer = QSvgRenderer(str(icon_path))
    return renderer if renderer.isValid() else None


def _icon_path(icon_name: str) -> Path | None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "assets" / "icons" / "topology" / icon_name
        if candidate.exists():
            return candidate
    return None


def _status_color(status: DeviceStatus | None) -> QColor:
    colors = {
        DeviceStatus.ONLINE: QColor("#16a34a"),
        DeviceStatus.OFFLINE: QColor("#dc2626"),
        DeviceStatus.DEGRADED: QColor("#f59e0b"),
        DeviceStatus.MAINTENANCE: QColor("#2563eb"),
        DeviceStatus.UNKNOWN: QColor("#94a3b8"),
    }
    return colors.get(status or DeviceStatus.UNKNOWN, QColor("#94a3b8"))


def _cable_color(cable_type: CableType) -> QColor:
    colors = {
        CableType.COPPER: QColor("#f97316"),
        CableType.FIBER: QColor("#06b6d4"),
        CableType.WIRELESS: QColor("#a855f7"),
        CableType.OTHER: QColor("#94a3b8"),
    }
    return colors.get(cable_type, QColor("#94a3b8"))
