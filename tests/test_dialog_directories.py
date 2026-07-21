from __future__ import annotations

from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from fireitmanager.ui.main_window import FireITMainWindow


def test_dialogs_remember_individual_last_directories(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    window = FireITMainWindow()

    load_dir = tmp_path / "load"
    save_dir = tmp_path / "save"
    report_dir = tmp_path / "reports"
    load_dir.mkdir()
    save_dir.mkdir()
    report_dir.mkdir()

    incident_path = load_dir / "loaded-incident.json"
    window.repository.save(window.workspace_snapshot.incident, incident_path)

    window.load_dialog_dir = load_dir
    with patch(
        "fireitmanager.ui.main_window.QFileDialog.getOpenFileName",
        return_value=(str(incident_path), "Incident JSON (*.json)"),
    ) as load_dialog:
        window.load_workspace()
    assert load_dialog.call_args.args[2] == str(load_dir)
    assert window.load_dialog_dir == load_dir

    window.save_dialog_dir = save_dir
    save_as_path = save_dir / "saved-incident.json"
    with patch(
        "fireitmanager.ui.main_window.QFileDialog.getSaveFileName",
        return_value=(str(save_as_path), "Incident JSON (*.json)"),
    ) as save_dialog:
        result = window.save_workspace_as()
    assert result == save_as_path
    assert save_dialog.call_args.args[2] == str(save_dir)
    assert window.save_dialog_dir == save_dir

    window.report_dialog_dir = report_dir
    md_path = report_dir / window.report_path.name
    with patch(
        "fireitmanager.ui.main_window.QFileDialog.getSaveFileName",
        return_value=(str(md_path), "Markdown (*.md)"),
    ) as md_dialog:
        md_result = window.export_incident_summary()
    assert md_result == md_path
    assert md_dialog.call_args.args[2] == str(report_dir / window.report_path.name)
    assert window.report_dialog_dir == report_dir

    window.report_csv_dialog_dir = report_dir
    csv_path = report_dir / window.report_csv_path.name
    with patch(
        "fireitmanager.ui.main_window.QFileDialog.getSaveFileName",
        return_value=(str(csv_path), "CSV (*.csv)"),
    ) as csv_dialog:
        csv_result = window.export_incident_summary_csv()
    assert csv_result == csv_path
    assert csv_dialog.call_args.args[2] == str(report_dir / window.report_csv_path.name)
    assert window.report_csv_dialog_dir == report_dir

    window.report_html_dialog_dir = report_dir
    html_path = report_dir / window.report_html_path.name
    with patch(
        "fireitmanager.ui.main_window.QFileDialog.getSaveFileName",
        return_value=(str(html_path), "HTML (*.html)"),
    ) as html_dialog:
        html_result = window.export_incident_summary_html()
    assert html_result == html_path
    assert html_dialog.call_args.args[2] == str(report_dir / window.report_html_path.name)
    assert window.report_html_dialog_dir == report_dir

    window.close()
    app.quit()
