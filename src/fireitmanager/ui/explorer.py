"""Incident explorer widget for the FireIT Manager workspace."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from fireitmanager.ui.workspace import WorkspaceNode, WorkspaceSnapshot


class IncidentExplorerWidget(QWidget):
    """Simple tree-based explorer for incident workspace structure."""

    selection_changed = Signal(str, str, str, str, str)
    selection_target_changed = Signal(object)

    def __init__(self, snapshot: WorkspaceSnapshot, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("incidentExplorerWidget")
        self._snapshot = snapshot

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("Incident Explorer", self)
        title.setObjectName("incidentExplorerTitle")
        title.setStyleSheet("font-size: 16px; font-weight: 600;")

        self.subtitle_label = QLabel(snapshot.incident.summary(), self)
        self.subtitle_label.setObjectName("incidentExplorerSubtitle")
        self.subtitle_label.setStyleSheet("color: #6b7280;")

        self.tree = QTreeWidget(self)
        self.tree.setObjectName("incidentExplorerTree")
        self.tree.setHeaderHidden(True)
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.setRootIsDecorated(True)
        self.tree.currentItemChanged.connect(self._on_current_item_changed)

        layout.addWidget(title)
        layout.addWidget(self.subtitle_label)
        layout.addWidget(self.tree, 1)

        self._build_tree(self._snapshot.root)

    def set_snapshot(self, snapshot: WorkspaceSnapshot) -> None:
        """Replace the displayed snapshot and refresh the tree."""
        self._snapshot = snapshot
        self.subtitle_label.setText(snapshot.incident.summary())
        self._build_tree(snapshot.root)

    def _build_tree(self, root: WorkspaceNode) -> None:
        """Populate the explorer from the workspace snapshot."""
        self.tree.blockSignals(True)
        self.tree.clear()
        self.tree.addTopLevelItem(self._create_item(root))
        top_level = self.tree.topLevelItem(0)
        if top_level is not None:
            top_level.setExpanded(True)
        self.tree.expandAll()
        self.tree.setCurrentItem(self.tree.topLevelItem(0))
        self.tree.blockSignals(False)
        current = self.tree.currentItem()
        if current is not None:
            self._on_current_item_changed(current, None)

    def _create_item(self, node: WorkspaceNode) -> QTreeWidgetItem:
        """Create a tree item with metadata for the properties panel."""
        item = QTreeWidgetItem([node.label])
        item.setData(
            0,
            Qt.UserRole,
            node,
        )
        for child in node.children:
            item.addChild(self._create_item(child))
        return item

    def _on_current_item_changed(
        self,
        current: QTreeWidgetItem | None,
        previous: QTreeWidgetItem | None,
    ) -> None:
        """Emit a properties summary for the newly selected item."""
        del previous
        if current is None:
            return

        data = current.data(0, Qt.UserRole)
        if not isinstance(data, WorkspaceNode):
            return
        self.selection_changed.emit(
            data.label,
            data.kind,
            data.path,
            data.description,
            "\n".join(f"{key}: {value}" for key, value in data.details.items()),
        )
        self.selection_target_changed.emit(data.target)

    def select_target(self, target: object) -> bool:
        """Select the tree item backed by the given model object."""
        top_level = self.tree.topLevelItem(0)
        if top_level is None:
            return False

        item = self._find_item_by_target(top_level, target)
        if item is None:
            return False

        self.tree.setCurrentItem(item)
        return True

    def _find_item_by_target(
        self,
        item: QTreeWidgetItem,
        target: object,
    ) -> QTreeWidgetItem | None:
        node = item.data(0, Qt.UserRole)
        if isinstance(node, WorkspaceNode) and node.target is target:
            return item

        for index in range(item.childCount()):
            match = self._find_item_by_target(item.child(index), target)
            if match is not None:
                return match
        return None
