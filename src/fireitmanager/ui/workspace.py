"""Workspace snapshot helpers for the FireIT Manager UI."""

from __future__ import annotations

from dataclasses import dataclass, field

from fireitmanager.models.asset import Asset
from fireitmanager.models.building import Building
from fireitmanager.models.camp import Camp
from fireitmanager.models.cable import Cable
from fireitmanager.models.device import Device
from fireitmanager.models.enums import BuildingType, CableType, DeviceStatus, DeviceType
from fireitmanager.models.incident import Incident
from fireitmanager.models.network import Network
from fireitmanager.models.person import Person


@dataclass(slots=True)
class WorkspaceNode:
    """A node in the incident workspace tree."""

    label: str
    kind: str
    path: str
    description: str
    details: dict[str, str] = field(default_factory=dict)
    children: list["WorkspaceNode"] = field(default_factory=list)
    target: object | None = None


@dataclass(slots=True)
class WorkspaceSnapshot:
    """Structured data used to drive the explorer and properties panels."""

    incident: Incident
    root: WorkspaceNode


def build_workspace_snapshot(incident: Incident) -> WorkspaceSnapshot:
    """Build a workspace snapshot from the current incident object graph."""
    root = WorkspaceNode(
        label="Workspace",
        kind="workspace",
        path="Workspace",
        description="Loaded incident workspace for planning and operations.",
        details={
            "Incident": incident.summary(),
            "Agency": incident.agency,
            "Operational Period": incident.operational_period,
        },
        children=[
            _build_incident_node(incident),
            _build_camps_node(incident),
            _build_networks_node(incident),
            _build_assets_node(incident),
            _build_personnel_node(incident),
        ],
    )
    return WorkspaceSnapshot(incident=incident, root=root)


def _build_incident_node(incident: Incident) -> WorkspaceNode:
    return WorkspaceNode(
        label="Incident",
        kind="incident",
        path="Workspace / Incident",
        description="Incident metadata and operational context.",
        details={
            "Incident Number": incident.incident_number,
            "Agency": incident.agency,
            "Operational Period": incident.operational_period,
            "Camps": str(len(incident.camps)),
            "Personnel": str(len(incident.personnel)),
            "Assets": str(len(incident.assets)),
        },
        target=incident,
    )


def _build_camps_node(incident: Incident) -> WorkspaceNode:
    camp_nodes = [_build_camp_node(camp, index) for index, camp in enumerate(incident.camps, start=1)]
    return WorkspaceNode(
        label="Camps",
        kind="camp-group",
        path="Workspace / Camps",
        description="Camps attached to the active incident.",
        details={"Count": str(len(incident.camps))},
        children=camp_nodes,
    )


def _build_camp_node(camp: Camp, index: int) -> WorkspaceNode:
    camp_path = f"Workspace / Camps / {camp.name}"
    building_nodes = [_build_building_node(building, camp_path) for building in camp.buildings]
    network_nodes = [_build_network_node(network, camp_path) for network in camp.networks]
    return WorkspaceNode(
        label=camp.name,
        kind="camp",
        path=camp_path,
        description="Base camp supporting incident operations.",
        details={
            "Camp Index": str(index),
            "Buildings": str(len(camp.buildings)),
            "Networks": str(len(camp.networks)),
        },
        children=building_nodes + network_nodes,
        target=camp,
    )


def _build_building_node(building: Building, camp_path: str) -> WorkspaceNode:
    building_path = f"{camp_path} / {building.name}"
    device_nodes = [_build_device_node(device, building_path) for device in building.devices]
    location_name = building.location.name if building.location is not None else "Unassigned"
    latitude = (
        f"{building.location.latitude:.4f}"
        if building.location is not None and building.location.latitude is not None
        else "Unknown"
    )
    longitude = (
        f"{building.location.longitude:.4f}"
        if building.location is not None and building.location.longitude is not None
        else "Unknown"
    )
    return WorkspaceNode(
        label=building.name,
        kind="building",
        path=building_path,
        description="Operations and IT staging building.",
        details={
            "Building Type": building.building_type.value,
            "Devices": str(len(building.devices)),
            "Location": location_name,
            "Latitude": latitude,
            "Longitude": longitude,
        },
        children=device_nodes,
        target=building,
    )


def _build_device_node(device: Device, building_path: str) -> WorkspaceNode:
    return WorkspaceNode(
        label=device.hostname,
        kind="device",
        path=f"{building_path} / {device.hostname}",
        description="Device assigned to the selected building.",
        details={
            "Manufacturer": device.manufacturer,
            "Model": device.model,
            "Status": device.status.value,
        },
        target=device,
    )


def _build_networks_node(incident: Incident) -> WorkspaceNode:
    children: list[WorkspaceNode] = []
    for camp in incident.camps:
        for network in camp.networks:
            children.append(_build_network_node(network, f"Workspace / Camps / {camp.name}"))
    return WorkspaceNode(
        label="Network",
        kind="network-group",
        path="Workspace / Network",
        description="Connectivity and network infrastructure objects.",
        details={"Count": str(len(children))},
        children=children,
    )


def _build_network_node(network: Network, camp_path: str) -> WorkspaceNode:
    network_path = f"{camp_path} / Network / {network.name}"
    cable_nodes = [
        WorkspaceNode(
            label=f"Cable {index}",
            kind="cable",
            path=f"{network_path} / Cable {index}",
            description="Connection between network devices.",
            details={
                "Cable Type": cable.cable_type.value,
                "Length": f"{cable.length:.1f} ft" if cable.length is not None else "Unknown",
                "Source": cable.source_device.hostname if cable.source_device else "Unassigned",
                "Destination": (
                    cable.destination_device.hostname if cable.destination_device else "Unassigned"
                ),
            },
            target=cable,
        )
        for index, cable in enumerate(network.cables, start=1)
    ]
    return WorkspaceNode(
        label=network.name,
        kind="network",
        path=network_path,
        description="The active camp LAN supporting the IT staging area.",
        details={
            "Devices": str(len(network.devices)),
            "Cables": str(len(network.cables)),
        },
        children=cable_nodes,
        target=network,
    )


def _build_assets_node(incident: Incident) -> WorkspaceNode:
    return WorkspaceNode(
        label="Inventory",
        kind="asset-group",
        path="Workspace / Inventory",
        description="Tracked operational resources and equipment.",
        details={"Count": str(len(incident.assets))},
        children=[
            WorkspaceNode(
                label=asset.name,
                kind="asset",
                path=f"Workspace / Inventory / {asset.name}",
                description="Tracked operational asset.",
                details={
                    "Owner": asset.owner,
                    "Acquisition Type": asset.acquisition_type,
                    "Status": asset.status.value,
                    "Assigned Person": (
                        asset.assigned_person.name if asset.assigned_person is not None else "Unassigned"
                    ),
                },
                target=asset,
            )
            for asset in incident.assets
        ],
    )


def _build_personnel_node(incident: Incident) -> WorkspaceNode:
    return WorkspaceNode(
        label="Personnel",
        kind="personnel-group",
        path="Workspace / Personnel",
        description="Assigned support personnel for the incident.",
        details={"Count": str(len(incident.personnel))},
        children=[
            WorkspaceNode(
                label=person.name,
                kind="person",
                path=f"Workspace / Personnel / {person.name}",
                description="Incident personnel member.",
                details={
                    "Position": person.position,
                    "Agency": person.agency,
                    "Assigned Devices": str(len(person.assigned_devices)),
                },
                target=person,
            )
            for person in incident.personnel
        ],
    )


def build_demo_workspace_snapshot() -> WorkspaceSnapshot:
    """Create a representative incident workspace for the shell UI."""
    incident = Incident(
        "Pine Gulch Incident",
        incident_number="CA-INC-2026-041",
        agency="USFS",
        operational_period="Operational Period 1",
    )

    camp = Camp("Base Camp")
    building = Building("IT Staging", building_type=BuildingType.COMMAND_POST)
    router = Device(
        "it-router-01",
        manufacturer="Cisco",
        model="ISR 4331",
        device_type=DeviceType.ROUTER,
        status=DeviceStatus.ONLINE,
    )
    workstation = Device(
        "it-workstation-01",
        manufacturer="Dell",
        model="Latitude 5440",
        device_type=DeviceType.WORKSTATION,
        status=DeviceStatus.ONLINE,
    )
    building.add_device(router)
    building.add_device(workstation)
    camp.add_building(building)

    network = Network("Camp LAN")
    network.add_device(router)
    network.add_device(workstation)
    network.add_cable(Cable(CableType.COPPER, router, workstation, length=25.0))
    camp.add_network(network)

    asset = Asset("Generator 1", owner="Logistics", acquisition_type="Assigned")
    person = Person("Alex Morgan", position="IT Support", agency="State")
    incident.add_camp(camp)
    incident.assets.append(asset)
    incident.personnel.append(person)
    return build_workspace_snapshot(incident)
