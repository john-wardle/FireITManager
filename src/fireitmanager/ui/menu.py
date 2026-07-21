"""Menu bar composition for the FireIT Manager application."""

from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMenuBar, QMenu


def create_menu_bar(window: QMainWindow) -> QMenuBar:
    """Create the application menu bar with the requested top-level menus."""
    menu_bar = QMenuBar(window)

    menu_names = [
        "File",
        "Edit",
        "View",
        "Incident",
        "Network",
        "Inventory",
        "Reports",
        "Tools",
        "Help",
    ]

    for name in menu_names:
        menu_bar.addMenu(QMenu(name, window))

    file_menu = menu_bar.actions()[0].menu()
    if file_menu is not None:
        file_menu.addAction(_create_action("New Incident", window.create_new_incident, window))
        file_menu.addAction(_create_action("Open", window.load_workspace, window))
        file_menu.addAction(_create_action("Save", window.save_workspace, window))

    network_menu = menu_bar.actions()[3].menu()
    if network_menu is not None:
        network_menu.addAction(_create_action("Network Editor", window.show_network_editor, window))

    inventory_menu = menu_bar.actions()[5].menu()
    if inventory_menu is not None:
        inventory_menu.addAction(_create_action("Asset Editor", window.show_asset_editor, window))
        inventory_menu.addAction(_create_action("Device Editor", window.show_device_editor, window))

    return menu_bar


def _create_action(text: str, callback, parent: QMainWindow) -> QAction:
    """Create a menu action with a stable object name."""
    action = QAction(text, parent)
    action.setObjectName(text.lower().replace(" ", "_"))
    action.triggered.connect(callback)
    return action
