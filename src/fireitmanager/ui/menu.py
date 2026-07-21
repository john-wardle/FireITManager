"""Menu bar composition for the FireIT Manager application."""

from __future__ import annotations

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

    return menu_bar
