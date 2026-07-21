"""Workspace validation helpers for FireIT Manager."""

from __future__ import annotations

from fireitmanager.models.incident import Incident


def validate_incident_workspace(incident: Incident) -> list[str]:
    """Return a list of structural issues found in an incident workspace."""
    issues: list[str] = []

    if not incident.name.strip():
        issues.append("Incident name is missing.")

    if not incident.camps:
        issues.append("At least one camp is required.")

    for camp in incident.camps:
        if not camp.buildings:
            issues.append(f"Camp '{camp.name}' has no buildings.")
        if not camp.networks:
            issues.append(f"Camp '{camp.name}' has no networks.")

        for building in camp.buildings:
            if not building.devices:
                issues.append(f"Building '{building.name}' has no devices.")

        for network in camp.networks:
            if not network.devices:
                issues.append(f"Network '{network.name}' has no devices.")

    known_persons = {person.name.lower() for person in incident.personnel}
    known_device_hostnames = {
        device.hostname.lower()
        for camp in incident.camps
        for building in camp.buildings
        for device in building.devices
    }

    for asset in incident.assets:
        if asset.assigned_person is not None and asset.assigned_person.name.lower() not in known_persons:
            issues.append(f"Asset '{asset.name}' references an unknown person.")

    for person in incident.personnel:
        for device in person.assigned_devices:
            if device.hostname.lower() not in known_device_hostnames:
                issues.append(f"Person '{person.name}' references an unknown device '{device.hostname}'.")

    return issues
