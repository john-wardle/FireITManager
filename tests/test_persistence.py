from __future__ import annotations

from fireitmanager.persistence import IncidentRepository
from fireitmanager.ui.workspace import build_demo_workspace_snapshot


def test_incident_repository_round_trips_full_workspace(tmp_path) -> None:
    snapshot = build_demo_workspace_snapshot()
    repository = IncidentRepository()
    path = tmp_path / "incident.json"

    repository.save(snapshot.incident, path)
    loaded = repository.load(path)

    assert loaded.name == snapshot.incident.name
    assert loaded.incident_number == snapshot.incident.incident_number
    assert len(loaded.camps) == 1
    assert len(loaded.personnel) == 1
    assert len(loaded.assets) == 1

    camp = loaded.camps[0]
    assert camp.name == "Base Camp"
    assert len(camp.buildings) == 1
    assert len(camp.networks) == 1

    building = camp.buildings[0]
    assert building.name == "IT Staging"
    assert building.location is None
    assert len(building.devices) == 2

    network = camp.networks[0]
    assert network.name == "Camp LAN"
    assert len(network.devices) == 2
    assert len(network.cables) == 1
    assert network.devices[0] is building.devices[0]
    assert network.devices[1] is building.devices[1]
    assert network.cables[0].source_device is building.devices[0]
    assert network.cables[0].destination_device is building.devices[1]
