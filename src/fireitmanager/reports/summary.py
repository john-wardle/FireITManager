"""Summary report generation for FireIT Manager."""

from __future__ import annotations

from pathlib import Path

from fireitmanager.models.incident import Incident


def build_incident_summary_report(incident: Incident) -> str:
    """Build a deterministic markdown summary for an incident."""
    lines: list[str] = [
        "# FireIT Manager Incident Summary",
        "",
        f"## {incident.summary()}",
        f"- Agency: {incident.agency or 'Unassigned'}",
        f"- Operational Period: {incident.operational_period or 'Unassigned'}",
        f"- Camps: {len(incident.camps)}",
        f"- Assets: {len(incident.assets)}",
        f"- Personnel: {len(incident.personnel)}",
        "",
    ]

    for camp in incident.camps:
        lines.extend(
            [
                f"### Camp: {camp.name}",
                f"- Buildings: {len(camp.buildings)}",
                f"- Networks: {len(camp.networks)}",
            ]
        )
        for building in camp.buildings:
            lines.append(
                f"  - Building: {building.name} [{building.building_type.value}]"
            )
            lines.append(f"    - Devices: {len(building.devices)}")
        for network in camp.networks:
            lines.append(f"  - Network: {network.name}")
            lines.append(f"    - Devices: {len(network.devices)}")
            lines.append(f"    - Cables: {len(network.cables)}")
        lines.append("")

    if incident.assets:
        lines.append("### Assets")
        for asset in incident.assets:
            assigned_person = (
                asset.assigned_person.name if asset.assigned_person is not None else "Unassigned"
            )
            lines.append(f"- {asset.name} ({asset.status.value}) -> {assigned_person}")
        lines.append("")

    if incident.personnel:
        lines.append("### Personnel")
        for person in incident.personnel:
            device_names = ", ".join(device.hostname for device in person.assigned_devices) or "None"
            lines.append(f"- {person.name} -> {device_names}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_incident_summary_report(incident: Incident, path: str | Path) -> Path:
    """Write the summary report to disk."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_incident_summary_report(incident), encoding="utf-8")
    return target
