"""Summary report generation for FireIT Manager."""

from __future__ import annotations

import csv
import html
import io
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


def build_incident_summary_csv(incident: Incident) -> str:
    """Build a deterministic CSV summary for an incident."""
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["Section", "Name", "Details"])
    writer.writerow(
        [
            "Incident",
            incident.summary(),
            f"Agency={incident.agency or 'Unassigned'}; Operational Period={incident.operational_period or 'Unassigned'}",
        ]
    )

    for camp in incident.camps:
        writer.writerow(["Camp", camp.name, f"Buildings={len(camp.buildings)}; Networks={len(camp.networks)}"])
        for building in camp.buildings:
            writer.writerow(
                [
                    "Building",
                    building.name,
                    f"Type={building.building_type.value}; Devices={len(building.devices)}",
                ]
            )
        for network in camp.networks:
            writer.writerow(
                [
                    "Network",
                    network.name,
                    f"Devices={len(network.devices)}; Cables={len(network.cables)}",
                ]
            )

    for asset in incident.assets:
        assigned_person = asset.assigned_person.name if asset.assigned_person is not None else "Unassigned"
        writer.writerow(["Asset", asset.name, f"Status={asset.status.value}; Assigned={assigned_person}"])

    for person in incident.personnel:
        device_names = ", ".join(device.hostname for device in person.assigned_devices) or "None"
        writer.writerow(["Person", person.name, f"Devices={device_names}"])

    return buffer.getvalue()


def write_incident_summary_csv_report(incident: Incident, path: str | Path) -> Path:
    """Write the CSV summary report to disk."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_incident_summary_csv(incident), encoding="utf-8")
    return target


def build_incident_summary_html(incident: Incident) -> str:
    """Build a deterministic HTML summary for an incident."""
    lines: list[str] = [
        "<!doctype html>",
        "<html lang=\"en\">",
        "<head>",
        "<meta charset=\"utf-8\">",
        "<title>FireIT Manager Incident Summary</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; margin: 2rem; color: #0f172a; }",
        "h1, h2, h3 { color: #0f172a; }",
        "section { margin-bottom: 1.5rem; }",
        "table { border-collapse: collapse; width: 100%; margin-top: 0.5rem; }",
        "th, td { border: 1px solid #cbd5e1; padding: 0.5rem; text-align: left; }",
        "th { background: #e2e8f0; }",
        "ul { margin-top: 0.25rem; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>FireIT Manager Incident Summary</h1>",
        f"<p><strong>{html.escape(incident.summary())}</strong></p>",
        "<section>",
        "<h2>Overview</h2>",
        "<table>",
        "<tbody>",
        f"<tr><th>Agency</th><td>{html.escape(incident.agency or 'Unassigned')}</td></tr>",
        f"<tr><th>Operational Period</th><td>{html.escape(incident.operational_period or 'Unassigned')}</td></tr>",
        f"<tr><th>Camps</th><td>{len(incident.camps)}</td></tr>",
        f"<tr><th>Assets</th><td>{len(incident.assets)}</td></tr>",
        f"<tr><th>Personnel</th><td>{len(incident.personnel)}</td></tr>",
        "</tbody>",
        "</table>",
        "</section>",
    ]

    for camp in incident.camps:
        lines.extend(
            [
                "<section>",
                f"<h2>Camp: {html.escape(camp.name)}</h2>",
                "<table>",
                "<tbody>",
                f"<tr><th>Buildings</th><td>{len(camp.buildings)}</td></tr>",
                f"<tr><th>Networks</th><td>{len(camp.networks)}</td></tr>",
                "</tbody>",
                "</table>",
            ]
        )
        if camp.buildings:
            lines.append("<h3>Buildings</h3>")
            lines.append("<ul>")
            for building in camp.buildings:
                lines.append(
                    f"<li>{html.escape(building.name)} [{html.escape(building.building_type.value)}] - Devices: {len(building.devices)}</li>"
                )
            lines.append("</ul>")
        if camp.networks:
            lines.append("<h3>Networks</h3>")
            lines.append("<ul>")
            for network in camp.networks:
                lines.append(
                    f"<li>{html.escape(network.name)} - Devices: {len(network.devices)} - Cables: {len(network.cables)}</li>"
                )
            lines.append("</ul>")
        lines.append("</section>")

    if incident.assets:
        lines.append("<section>")
        lines.append("<h2>Assets</h2>")
        lines.append("<ul>")
        for asset in incident.assets:
            assigned_person = asset.assigned_person.name if asset.assigned_person is not None else "Unassigned"
            lines.append(
                f"<li>{html.escape(asset.name)} ({html.escape(asset.status.value)}) -> {html.escape(assigned_person)}</li>"
            )
        lines.append("</ul>")
        lines.append("</section>")

    if incident.personnel:
        lines.append("<section>")
        lines.append("<h2>Personnel</h2>")
        lines.append("<ul>")
        for person in incident.personnel:
            device_names = ", ".join(device.hostname for device in person.assigned_devices) or "None"
            lines.append(
                f"<li>{html.escape(person.name)} -> {html.escape(device_names)}</li>"
            )
        lines.append("</ul>")
        lines.append("</section>")

    lines.extend(["</body>", "</html>"])
    return "\n".join(lines) + "\n"


def write_incident_summary_html_report(incident: Incident, path: str | Path) -> Path:
    """Write the HTML summary report to disk."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_incident_summary_html(incident), encoding="utf-8")
    return target
