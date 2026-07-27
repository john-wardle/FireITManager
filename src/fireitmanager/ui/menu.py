"""Menu bar composition for the FireIT Manager application."""

from __future__ import annotations

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow, QMenuBar, QMenu


def create_menu_bar(window: QMainWindow) -> QMenuBar:
    """Create the application menu bar with the requested top-level menus."""
    menu_bar = QMenuBar(window)

    menu_names = [
        "File",
        "Edit",
        "View",
        "Incident",
        "Camp Ops",
        "Inventory",
        "Network",
        "Outputs",
        "Help",
    ]

    menus: dict[str, QMenu] = {}
    for name in menu_names:
        menu = QMenu(name, window)
        menus[name] = menu
        menu_bar.addMenu(menu)

    file_menu = menus["File"]
    file_menu.addAction(
        _create_action("New Incident", window.create_new_incident, window, "Ctrl+N")
    )
    file_menu.addAction(_create_action("Open", window.load_workspace, window, "Ctrl+O"))
    file_menu.addAction(_create_action("Save", window.save_workspace, window, "Ctrl+S"))
    file_menu.addAction(
        _create_action(
            "Save As",
            lambda checked=False: window.save_workspace_as(),
            window,
            "Ctrl+Shift+S",
        )
    )
    recent_menu = file_menu.addMenu("Recent Files")
    recent_menu.setObjectName("recentFilesMenu")
    if hasattr(window, "_register_recent_files_menu"):
        window._register_recent_files_menu(recent_menu)

    edit_menu = menus["Edit"]
    edit_menu.addAction(_create_action("Undo", window.edit_undo, window, "Ctrl+Z"))
    edit_menu.addAction(_create_action("Redo", window.edit_redo, window, "Ctrl+Y"))
    edit_menu.addSeparator()
    edit_menu.addAction(_create_action("Cut", window.edit_cut, window, "Ctrl+X"))
    edit_menu.addAction(_create_action("Copy", window.edit_copy, window, "Ctrl+C"))
    edit_menu.addAction(_create_action("Paste", window.edit_paste, window, "Ctrl+V"))
    edit_menu.addAction(_create_action("Delete", window.edit_delete, window, "Del"))
    edit_menu.addSeparator()
    edit_menu.addAction(
        _create_action("Select All", window.edit_select_all, window, "Ctrl+A")
    )

    view_menu = menus["View"]
    view_menu.addAction(_create_action("Zoom In", window.canvas.zoom_in, window, "Ctrl++"))
    view_menu.addAction(_create_action("Zoom Out", window.canvas.zoom_out, window, "Ctrl+-"))
    view_menu.addAction(
        _create_action("Center View", window.canvas.center_scene, window, "Ctrl+0")
    )

    incident_menu = menus["Incident"]
    incident_menu.addAction(_create_action("Details", window.show_incident_editor, window))
    incident_menu.addAction(_create_action("Personnel", window.show_person_editor, window))

    camp_ops_menu = menus["Camp Ops"]
    camp_ops_menu.addAction(_create_action("Camps", window.show_camp_editor, window))
    camp_ops_menu.addAction(_create_action("Buildings", window.show_building_editor, window))

    inventory_menu = menus["Inventory"]
    inventory_menu.addAction(_create_action("Assets", window.show_asset_editor, window))
    inventory_menu.addAction(_create_action("Devices", window.show_device_editor, window))

    network_menu = menus["Network"]
    network_menu.addAction(_create_action("Site Map", window.show_canvas, window))
    network_menu.addAction(_create_action("Networks", window.show_network_editor, window))

    outputs_menu = menus["Outputs"]
    outputs_menu.addAction(_create_action("Reports", window.show_reports_page, window))
    outputs_menu.addAction(_create_action("Validation", window.show_validation_page, window))

    help_menu = menus["Help"]
    help_menu.addAction(_create_action("About", window.show_about, window))

    return menu_bar


def _create_action(
    text: str,
    callback,
    parent: QMainWindow,
    shortcut: str | None = None,
) -> QAction:
    """Create a menu action with a stable object name."""
    action = QAction(text, parent)
    action.setObjectName(text.lower().replace(" ", "_"))
    if shortcut is not None:
        action.setShortcut(QKeySequence(shortcut))
    action.triggered.connect(callback)
    return action
