from __future__ import annotations

from fireitmanager.core import validate_incident_workspace
from fireitmanager.ui.workspace import build_demo_workspace_snapshot


def test_demo_workspace_validates_cleanly() -> None:
    snapshot = build_demo_workspace_snapshot()

    assert validate_incident_workspace(snapshot.incident) == []


def test_validation_reports_missing_structure() -> None:
    snapshot = build_demo_workspace_snapshot()
    snapshot.incident.camps[0].buildings.clear()
    snapshot.incident.camps[0].networks.clear()

    issues = validate_incident_workspace(snapshot.incident)

    assert "Camp 'Base Camp' has no buildings." in issues
    assert "Camp 'Base Camp' has no networks." in issues
