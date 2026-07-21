from __future__ import annotations

from fireitmanager.reports import build_incident_summary_report, write_incident_summary_report
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
