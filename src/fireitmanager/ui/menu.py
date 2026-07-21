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

    edit_menu = menu_bar.actions()[1].menu()
    if edit_menu is not None:
        edit_menu.addAction(_create_action("Undo", window.canvas.undo, window))
        edit_menu.addAction(_create_action("Redo", window.canvas.redo, window))

    view_menu = menu_bar.actions()[2].menu()
    if view_menu is not None:
        view_menu.addAction(_create_action("Canvas", window.show_canvas, window))
        view_menu.addAction(_create_action("Incident Editor", window.show_incident_editor, window))
        view_menu.addAction(_create_action("Camp Editor", window.show_camp_editor, window))
        view_menu.addAction(_create_action("Asset Editor", window.show_asset_editor, window))
        view_menu.addAction(_create_action("Person Editor", window.show_person_editor, window))
        view_menu.addAction(_create_action("Building Editor", window.show_building_editor, window))
        view_menu.addAction(_create_action("Device Editor", window.show_device_editor, window))
        view_menu.addAction(_create_action("Network Editor", window.show_network_editor, window))

    incident_menu = menu_bar.actions()[3].menu()
    if incident_menu is not None:
        incident_menu.addAction(_create_action("Person Editor", window.show_person_editor, window))

    network_menu = menu_bar.actions()[4].menu()
    if network_menu is not None:
        network_menu.addAction(_create_action("Network Editor", window.show_network_editor, window))

    inventory_menu = menu_bar.actions()[5].menu()
    if inventory_menu is not None:
        inventory_menu.addAction(_create_action("Asset Editor", window.show_asset_editor, window))
        inventory_menu.addAction(_create_action("Device Editor", window.show_device_editor, window))

    reports_menu = menu_bar.actions()[6].menu()
    if reports_menu is not None:
        reports_menu.addAction(_create_action("Incident Summary", window.export_incident_summary, window))

    tools_menu = menu_bar.actions()[7].menu()
    if tools_menu is not None:
        tools_menu.addAction(_create_action("Validate Workspace", window.validate_workspace, window))

    help_menu = menu_bar.actions()[8].menu()
    if help_menu is not None:
        help_menu.addAction(_create_action("About", window.show_about, window))

    return menu_bar


def _create_action(text: str, callback, parent: QMainWindow) -> QAction:
    """Create a menu action with a stable object name."""
    action = QAction(text, parent)
    action.setObjectName(text.lower().replace(" ", "_"))
    action.triggered.connect(callback)
    return action
