from __future__ import annotations

from fireitmanager.reports import (
    build_incident_summary_csv,
    build_incident_summary_html,
    build_incident_summary_report,
    write_incident_summary_csv_report,
    write_incident_summary_html_report,
    write_incident_summary_report,
)
from fireitmanager.ui.workspace import build_demo_workspace_snapshot


def test_incident_summary_report_contains_core_sections(tmp_path) -> None:
    snapshot = build_demo_workspace_snapshot()

    report_text = build_incident_summary_report(snapshot.incident)

    assert "# FireIT Manager Incident Summary" in report_text
    assert "Pine Gulch Incident (CA-INC-2026-041)" in report_text
    assert "- Camps: 1" in report_text
    assert "### Camp: Base Camp" in report_text
    assert "### Assets" in report_text
    assert "### Personnel" in report_text

    report_path = tmp_path / "incident-summary.md"
    written_path = write_incident_summary_report(snapshot.incident, report_path)

    assert written_path == report_path
    assert report_path.exists()
    assert report_path.read_text(encoding="utf-8") == report_text

    csv_text = build_incident_summary_csv(snapshot.incident)
    assert "Section,Name,Details" in csv_text
    assert "Network,Camp LAN,Devices=2; Cables=1" in csv_text

    csv_path = tmp_path / "incident-summary.csv"
    written_csv_path = write_incident_summary_csv_report(snapshot.incident, csv_path)
    assert written_csv_path == csv_path
    assert csv_path.exists()
    assert csv_path.read_text(encoding="utf-8") == csv_text

    html_text = build_incident_summary_html(snapshot.incident)
    assert "<title>FireIT Manager Incident Summary</title>" in html_text
    assert "<h2>Camp: Base Camp</h2>" in html_text
    assert "Camp LAN - Devices: 2 - Cables: 1" in html_text

    html_path = tmp_path / "incident-summary.html"
    written_html_path = write_incident_summary_html_report(snapshot.incident, html_path)
    assert written_html_path == html_path
    assert html_path.exists()
    assert html_path.read_text(encoding="utf-8") == html_text
