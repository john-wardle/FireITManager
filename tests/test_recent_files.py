import os
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton

from fireitmanager.ui.main_window import FireITMainWindow


def test_recent_files_are_recorded_and_reopened(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    window = FireITMainWindow()

    name_input = window.findChild(QLineEdit, "incidentNameInput")
    assert name_input is not None
    apply_button = window.findChild(QPushButton, "applyIncidentChangesButton")
    assert apply_button is not None

    first_path = tmp_path / "first-incident.json"
    second_path = tmp_path / "second-incident.json"

    window.save_path = first_path
    window.save_workspace()
    assert window.recent_paths[0] == first_path

    name_input.setText("Changed Incident")
    apply_button = window.findChild(QPushButton, "applyIncidentChangesButton")
    assert apply_button is not None
    apply_button.click()

    with patch(
        "fireitmanager.ui.main_window.QFileDialog.getSaveFileName",
        return_value=(str(second_path), "Incident JSON (*.json)"),
    ):
        saved_as_path = window.save_workspace_as()
    assert saved_as_path == second_path
    assert window.save_path == second_path
    assert window.load_path == second_path
    assert window.recent_paths[0] == second_path
    assert window.recent_paths[1] == first_path
    assert window.recent_files_menu is not None
    assert [action.text() for action in window.recent_files_menu.actions()] == [
        second_path.name,
        first_path.name,
    ]

    window.open_recent_workspace(first_path)
    assert "Pine Gulch Incident" in window.findChild(QLabel, "incidentStatusLabel").text()
    assert window.findChild(QLabel, "incidentEditorSummary").text() == "Editing Pine Gulch Incident (CA-INC-2026-041)"

    window.close()
    app.quit()
