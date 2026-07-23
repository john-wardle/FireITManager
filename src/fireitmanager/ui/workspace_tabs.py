"""Folder-style workspace navigation for the main application shell."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from PySide6.QtCore import QPointF, QRect, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QTabBar,
    QTabWidget,
    QStyleOptionTab,
    QVBoxLayout,
    QWidget,
)


class FolderWorkspaceTabs(QTabWidget):
    """Two-level tab widget that presents workspace areas as file folders."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("workspaceTabs")
        self.setTabBar(FolderTabBar("primary", self))
        self.setDocumentMode(False)
        self.setMovable(False)
        self.setUsesScrollButtons(True)
        self.setElideMode(Qt.ElideRight)
        self._widget_locations: dict[QWidget, tuple[int, QTabWidget, int]] = {}
        self._task_widgets: list[QWidget] = []
        self.setStyleSheet(_folder_tab_stylesheet())

    def add_folder(self, label: str, tasks: Sequence[tuple[str, QWidget]]) -> QTabWidget:
        """Add a top-level folder and its second-level task tabs."""
        task_tabs = QTabWidget(self)
        task_tabs.setObjectName(_object_name_for(label, "TaskTabs"))
        task_tabs.setTabBar(FolderTabBar("secondary", task_tabs))
        task_tabs.setDocumentMode(False)
        task_tabs.setMovable(False)
        task_tabs.setUsesScrollButtons(True)
        task_tabs.setElideMode(Qt.ElideRight)

        folder_index = super().count()
        for task_label, widget in tasks:
            task_index = task_tabs.addTab(widget, task_label)
            task_tabs.setTabToolTip(task_index, task_label)
            self._widget_locations[widget] = (folder_index, task_tabs, task_index)
            self._task_widgets.append(widget)

        super().addTab(task_tabs, label)
        self.setTabToolTip(folder_index, label)
        return task_tabs

    def setCurrentWidget(self, widget: QWidget) -> None:  # noqa: N802 - Qt API name
        """Activate the folder and task tab containing ``widget``."""
        location = self._widget_locations.get(widget)
        if location is None:
            return
        folder_index, task_tabs, task_index = location
        super().setCurrentIndex(folder_index)
        task_tabs.setCurrentIndex(task_index)

    def currentWidget(self) -> QWidget | None:  # noqa: N802 - Qt API name
        """Return the active task widget instead of the active folder container."""
        folder_widget = super().currentWidget()
        if isinstance(folder_widget, QTabWidget):
            return folder_widget.currentWidget()
        return folder_widget

    def count(self) -> int:
        """Return the number of task tabs exposed by the workspace."""
        return len(self._task_widgets)

    def folder_count(self) -> int:
        """Return the number of top-level folders."""
        return super().count()


class WorkspaceActionPage(QWidget):
    """Simple page for workspace actions that do not yet need full editors."""

    def __init__(
        self,
        title: str,
        subtitle: str,
        actions: Sequence[tuple[str, Callable[[], object]]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(_object_name_for(title, "Page"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        title_label = QLabel(title, self)
        title_label.setObjectName(_object_name_for(title, "Title"))
        title_label.setProperty("role", "folderPageTitle")
        layout.addWidget(title_label)

        subtitle_label = QLabel(subtitle, self)
        subtitle_label.setObjectName(_object_name_for(title, "Subtitle"))
        subtitle_label.setWordWrap(True)
        subtitle_label.setProperty("role", "folderPageSubtitle")
        layout.addWidget(subtitle_label)

        for action_label, callback in actions:
            button = QPushButton(action_label, self)
            button.setObjectName(_object_name_for(action_label, "Button"))
            button.clicked.connect(
                lambda checked=False, action_callback=callback: action_callback()
            )
            layout.addWidget(button)

        layout.addStretch(1)


class FolderTabBar(QTabBar):
    """Paint tabs as overlapping file-folder labels."""

    def __init__(self, level: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.level = level
        self.setObjectName(
            "workspaceFolderTabBar" if level == "primary" else "workspaceTaskTabBar"
        )
        self.setDrawBase(False)
        self.setExpanding(False)
        self.setMouseTracking(True)

    def tabSizeHint(self, index: int) -> QSize:  # noqa: N802 - Qt API name
        """Reserve enough space for the folder shape and label."""
        base = super().tabSizeHint(index)
        if self.level == "primary":
            return QSize(max(base.width() + 74, 150), 58)
        return QSize(max(base.width() + 48, 122), 42)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API name
        """Draw unselected folders first and the active folder last."""
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        selected_index = self.currentIndex()
        for index in range(self.count()):
            if index != selected_index:
                self._paint_tab(painter, index, selected=False)
        if selected_index >= 0:
            self._paint_tab(painter, selected_index, selected=True)

    def _paint_tab(self, painter: QPainter, index: int, *, selected: bool) -> None:
        option = QStyleOptionTab()
        self.initStyleOption(option, index)

        rect = QRectF(self.tabRect(index))
        if self.level == "primary":
            rect.adjust(1, 7 if not selected else 2, -3, -1)
            tab_width = min(rect.width() * 0.55, 104)
            body_top_offset = 18
            radius = 5
            fill = QColor("#f0d99b" if selected else "#d1b46a")
            border = QColor("#9d8042")
            shadow = QColor(60, 44, 20, 48 if selected else 30)
            text_color = QColor("#2e2414")
            font = QFont(self.font())
            font.setBold(selected)
        else:
            rect.adjust(1, 4 if not selected else 1, -3, -1)
            tab_width = min(rect.width() * 0.52, 78)
            body_top_offset = 13
            radius = 4
            fill = QColor("#fffaf0" if selected else "#ead8a5")
            border = QColor("#b79d5e")
            shadow = QColor(60, 44, 20, 32 if selected else 18)
            text_color = QColor("#3a2f1d")
            font = QFont(self.font())
            font.setPointSize(max(font.pointSize() - 1, 8))
            font.setBold(selected)

        shadow_path = _folder_tab_path(rect.translated(2, 2), tab_width, body_top_offset, radius)
        painter.fillPath(shadow_path, shadow)

        folder_path = _folder_tab_path(rect, tab_width, body_top_offset, radius)
        painter.fillPath(folder_path, fill)
        painter.setPen(QPen(border, 1))
        painter.drawPath(folder_path)

        crease_y = rect.top() + body_top_offset + 4
        crease = QPen(QColor(255, 248, 225, 130), 1)
        painter.setPen(crease)
        painter.drawLine(
            QPointF(rect.left() + 13, crease_y),
            QPointF(rect.right() - 14, crease_y),
        )

        if selected:
            highlight = QPen(QColor(255, 255, 255, 140), 1)
            painter.setPen(highlight)
            painter.drawLine(
                QPointF(rect.left() + 12, rect.top() + body_top_offset + 1),
                QPointF(rect.right() - 16, rect.top() + body_top_offset + 1),
            )

        painter.setPen(text_color)
        painter.setFont(font)
        label_rect = QRect(
            int(rect.left() + 12),
            int(rect.top() + body_top_offset),
            int(rect.width() - 24),
            int(rect.height() - body_top_offset - 2),
        )
        painter.drawText(label_rect, Qt.AlignCenter, option.text)


def _object_name_for(label: str, suffix: str) -> str:
    """Convert a label into a stable Qt object name."""
    words = "".join(part.capitalize() for part in label.replace("&", " ").split())
    return f"{words[:1].lower()}{words[1:]}{suffix}" if words else suffix[:1].lower() + suffix[1:]


def _folder_tab_path(
    rect: QRectF,
    tab_width: float,
    body_top_offset: float,
    radius: float,
) -> QPainterPath:
    """Build a file-folder silhouette for a tab rectangle."""
    left = rect.left()
    right = rect.right()
    top = rect.top()
    bottom = rect.bottom()
    body_top = top + body_top_offset
    tab_left = left + 16
    tab_right = min(tab_left + tab_width, right - 20)
    tab_slope = 12

    path = QPainterPath()
    path.moveTo(left + radius, body_top)
    path.lineTo(tab_left - 6, body_top)
    path.cubicTo(
        tab_left - 2,
        body_top,
        tab_left + 1,
        body_top - 8,
        tab_left + 6,
        body_top - 12,
    )
    path.lineTo(tab_left + 16, top + 2)
    path.quadTo(tab_left + 18, top, tab_left + 24, top)
    path.lineTo(tab_right - tab_slope, top)
    path.quadTo(tab_right - 4, top, tab_right, top + 5)
    path.lineTo(tab_right + tab_slope, body_top)
    path.lineTo(right - radius, body_top)
    path.quadTo(right, body_top, right, body_top + radius)
    path.lineTo(right, bottom)
    path.lineTo(left, bottom)
    path.lineTo(left, body_top + radius)
    path.quadTo(left, body_top, left + radius, body_top)
    path.closeSubpath()
    return path


def _folder_tab_stylesheet() -> str:
    """Return the stylesheet for the workspace folder tabs."""
    return """
        QTabWidget#workspaceTabs::pane {
            border: 1px solid #b99a55;
            background: #f7eccf;
            margin-top: -2px;
        }

        QTabWidget::pane {
            border: 1px solid #ceb271;
            background: #fffaf0;
            margin-top: -2px;
        }

        QLabel[role="folderPageTitle"] {
            color: #231f18;
            font-size: 22px;
            font-weight: 700;
        }

        QLabel[role="folderPageSubtitle"] {
            color: #5c5547;
            font-size: 13px;
        }

        QPushButton {
            background: #f8f1dd;
            border: 1px solid #c8b176;
            border-radius: 4px;
            color: #2f281b;
            padding: 8px 14px;
            text-align: left;
            max-width: 260px;
        }

        QPushButton:hover {
            background: #efe0b8;
        }
    """
