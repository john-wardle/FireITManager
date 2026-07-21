"""JSON persistence for FireIT Manager incidents."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from fireitmanager.models.asset import Asset
from fireitmanager.models.building import Building
from fireitmanager.models.cable import Cable
from fireitmanager.models.camp import Camp
from fireitmanager.models.device import Device
from fireitmanager.models.enums import AssetStatus, BuildingType, CableType, DeviceStatus, DeviceType
from fireitmanager.models.incident import Incident
from fireitmanager.models.location import Location
from fireitmanager.models.network import Network
from fireitmanager.models.person import Person


SCHEMA_VERSION = 1


class IncidentRepository:
    """Persist incidents to and from JSON files."""

    def save(self, incident: Incident, path: str | Path) -> Path:
        """Write an incident graph to disk."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as handle:
            json.dump(serialize_incident(incident), handle, indent=2, sort_keys=True)
            handle.write("\n")
        return target

    def load(self, path: str | Path) -> Incident:
        """Load an incident graph from disk."""
        source = Path(path)
        with source.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return deserialize_incident(data)


def serialize_incident(incident: Incident) -> dict[str, Any]:
    """Convert an incident graph into JSON-safe data."""
    return {
        "schema_version": SCHEMA_VERSION,
        "incident": {
            "name": incident.name,
            "incident_number": incident.incident_number,
            "agency": incident.agency,
            "operational_period": incident.operational_period,
            "incident_id": str(incident.incident_id),
            "created_at": _dt_to_str(incident.created_at),
            "updated_at": _dt_to_str(incident.updated_at),
        },
        "camps": [serialize_camp(camp) for camp in incident.camps],
        "personnel": [serialize_person(person) for person in incident.personnel],
        "assets": [serialize_asset(asset) for asset in incident.assets],
    }


def deserialize_incident(data: dict[str, Any]) -> Incident:
    """Rebuild an incident graph from serialized data."""
    incident_data = data["incident"]
    incident = Incident(
        incident_data["name"],
        incident_number=incident_data.get("incident_number", ""),
        agency=incident_data.get("agency", ""),
        operational_period=incident_data.get("operational_period", ""),
        incident_id=_uuid_from_text(incident_data["incident_id"]),
        created_at=_dt_from_text(incident_data["created_at"]),
        updated_at=_dt_from_text(incident_data["updated_at"]),
    )

    person_registry: dict[str, Person] = {}
    device_registry: dict[str, Device] = {}
    person_device_registry: dict[str, list[str]] = {}

    for camp_data in data.get("camps", []):
        camp = Camp(
            camp_data["name"],
            camp_id=_uuid_from_text(camp_data["camp_id"]),
            created_at=_dt_from_text(camp_data["created_at"]),
            updated_at=_dt_from_text(camp_data["updated_at"]),
        )
        incident.add_camp(camp)
        _restore_camp(camp, camp_data, device_registry)

    for person_data in data.get("personnel", []):
        person = Person(
            person_data["name"],
            position=person_data.get("position", ""),
            agency=person_data.get("agency", ""),
            person_id=_uuid_from_text(person_data["person_id"]),
            created_at=_dt_from_text(person_data["created_at"]),
            updated_at=_dt_from_text(person_data["updated_at"]),
        )
        incident.personnel.append(person)
        person_registry[person_data["person_id"]] = person
        person_device_registry[person_data["person_id"]] = list(
            person_data.get("assigned_device_ids", [])
        )

    for asset_data in data.get("assets", []):
        asset = Asset(
            asset_data["name"],
            owner=asset_data.get("owner", ""),
            acquisition_type=asset_data.get("acquisition_type", ""),
            barcode=asset_data.get("barcode", ""),
            status=AssetStatus(asset_data.get("status", AssetStatus.AVAILABLE.value)),
            asset_id=_uuid_from_text(asset_data["asset_id"]),
            created_at=_dt_from_text(asset_data["created_at"]),
            updated_at=_dt_from_text(asset_data["updated_at"]),
        )
        assigned_person_id = asset_data.get("assigned_person_id")
        if assigned_person_id and assigned_person_id in person_registry:
            asset.assigned_person = person_registry[assigned_person_id]
        incident.assets.append(asset)

    for person_id, device_ids in person_device_registry.items():
        person = person_registry.get(person_id)
        if person is None:
            continue
        for device_id in device_ids:
            device = device_registry.get(device_id)
            if device is not None and device not in person.assigned_devices:
                person.assigned_devices.append(device)

    incident.created_at = _dt_from_text(incident_data["created_at"])
    incident.updated_at = _dt_from_text(incident_data["updated_at"])
    return incident


def serialize_camp(camp: Camp) -> dict[str, Any]:
    """Serialize a camp and its nested structure."""
    return {
        "name": camp.name,
        "camp_id": str(camp.camp_id),
        "created_at": _dt_to_str(camp.created_at),
        "updated_at": _dt_to_str(camp.updated_at),
        "buildings": [serialize_building(building) for building in camp.buildings],
        "networks": [serialize_network(network) for network in camp.networks],
    }


def serialize_building(building: Building) -> dict[str, Any]:
    """Serialize a building and its nested devices."""
    return {
        "name": building.name,
        "building_type": building.building_type.value,
        "building_id": str(building.building_id),
        "created_at": _dt_to_str(building.created_at),
        "updated_at": _dt_to_str(building.updated_at),
        "location": serialize_location(building.location) if building.location is not None else None,
        "devices": [serialize_device(device, building.building_id) for device in building.devices],
    }


def serialize_location(location: Location) -> dict[str, Any]:
    """Serialize a location record."""
    return {
        "name": location.name,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "elevation_ft": location.elevation_ft,
        "notes": location.notes,
        "location_id": str(location.location_id),
        "created_at": _dt_to_str(location.created_at),
        "updated_at": _dt_to_str(location.updated_at),
    }


def serialize_device(device: Device, building_id: UUID | None = None) -> dict[str, Any]:
    """Serialize a device record."""
    return {
        "hostname": device.hostname,
        "manufacturer": device.manufacturer,
        "model": device.model,
        "serial_number": device.serial_number,
        "ip_address": device.ip_address,
        "mac_address": device.mac_address,
        "device_type": device.device_type.value,
        "status": device.status.value,
        "device_id": str(device.device_id),
        "assigned_building_id": str(building_id) if building_id is not None else None,
        "created_at": _dt_to_str(device.created_at),
        "updated_at": _dt_to_str(device.updated_at),
    }


def serialize_network(network: Network) -> dict[str, Any]:
    """Serialize a network record."""
    return {
        "name": network.name,
        "network_id": str(network.network_id),
        "created_at": _dt_to_str(network.created_at),
        "updated_at": _dt_to_str(network.updated_at),
        "device_ids": [str(device.device_id) for device in network.devices],
        "cables": [serialize_cable(cable) for cable in network.cables],
    }


def serialize_cable(cable: Cable) -> dict[str, Any]:
    """Serialize a cable record."""
    return {
        "cable_type": cable.cable_type.value,
        "source_device_id": str(cable.source_device.device_id) if cable.source_device else None,
        "destination_device_id": (
            str(cable.destination_device.device_id) if cable.destination_device else None
        ),
        "length": cable.length,
        "notes": cable.notes,
        "cable_id": str(cable.cable_id),
        "created_at": _dt_to_str(cable.created_at),
        "updated_at": _dt_to_str(cable.updated_at),
    }


def serialize_asset(asset: Asset) -> dict[str, Any]:
    """Serialize an asset record."""
    return {
        "name": asset.name,
        "owner": asset.owner,
        "acquisition_type": asset.acquisition_type,
        "barcode": asset.barcode,
        "status": asset.status.value,
        "assigned_person_id": str(asset.assigned_person.person_id) if asset.assigned_person else None,
        "asset_id": str(asset.asset_id),
        "created_at": _dt_to_str(asset.created_at),
        "updated_at": _dt_to_str(asset.updated_at),
    }


def serialize_person(person: Person) -> dict[str, Any]:
    """Serialize a person record."""
    return {
        "name": person.name,
        "position": person.position,
        "agency": person.agency,
        "assigned_device_ids": [str(device.device_id) for device in person.assigned_devices],
        "person_id": str(person.person_id),
        "created_at": _dt_to_str(person.created_at),
        "updated_at": _dt_to_str(person.updated_at),
    }


def _restore_camp(camp: Camp, camp_data: dict[str, Any], device_registry: dict[str, Device]) -> None:
    """Restore a camp's nested buildings and networks."""
    for building_data in camp_data.get("buildings", []):
        building = Building(
            building_data["name"],
            building_type=BuildingType(building_data.get("building_type", BuildingType.OTHER.value)),
            location=_restore_location(building_data.get("location")),
            building_id=_uuid_from_text(building_data["building_id"]),
            created_at=_dt_from_text(building_data["created_at"]),
            updated_at=_dt_from_text(building_data["updated_at"]),
        )
        camp.add_building(building)
        for device_data in building_data.get("devices", []):
            device = _restore_device(device_data)
            building.add_device(device)
            device_registry[device_data["device_id"]] = device

    for network_data in camp_data.get("networks", []):
        network = Network(
            network_data["name"],
            network_id=_uuid_from_text(network_data["network_id"]),
            created_at=_dt_from_text(network_data["created_at"]),
            updated_at=_dt_from_text(network_data["updated_at"]),
        )
        for device_id in network_data.get("device_ids", []):
            device = device_registry.get(device_id)
            if device is not None:
                network.add_device(device)
        for cable_data in network_data.get("cables", []):
            cable = _restore_cable(cable_data, device_registry)
            network.add_cable(cable)
        camp.add_network(network)

    camp.created_at = _dt_from_text(camp_data["created_at"])
    camp.updated_at = _dt_from_text(camp_data["updated_at"])


def _restore_location(location_data: dict[str, Any] | None) -> Location | None:
    if location_data is None:
        return None
    return Location(
        location_data["name"],
        latitude=location_data.get("latitude"),
        longitude=location_data.get("longitude"),
        elevation_ft=location_data.get("elevation_ft"),
        notes=location_data.get("notes", ""),
        location_id=_uuid_from_text(location_data["location_id"]),
        created_at=_dt_from_text(location_data["created_at"]),
        updated_at=_dt_from_text(location_data["updated_at"]),
    )


def _restore_device(device_data: dict[str, Any]) -> Device:
    return Device(
        device_data["hostname"],
        manufacturer=device_data.get("manufacturer", ""),
        model=device_data.get("model", ""),
        serial_number=device_data.get("serial_number", ""),
        ip_address=device_data.get("ip_address"),
        mac_address=device_data.get("mac_address"),
        device_type=DeviceType(device_data.get("device_type", DeviceType.OTHER.value)),
        status=DeviceStatus(device_data.get("status", DeviceStatus.UNKNOWN.value)),
        device_id=_uuid_from_text(device_data["device_id"]),
        created_at=_dt_from_text(device_data["created_at"]),
        updated_at=_dt_from_text(device_data["updated_at"]),
    )


def _restore_cable(cable_data: dict[str, Any], device_registry: dict[str, Device]) -> Cable:
    source = device_registry.get(cable_data.get("source_device_id"))
    destination = device_registry.get(cable_data.get("destination_device_id"))
    return Cable(
        cable_type=CableType(cable_data.get("cable_type", CableType.OTHER.value)),
        source_device=source,
        destination_device=destination,
        length=cable_data.get("length"),
        notes=cable_data.get("notes", ""),
        cable_id=_uuid_from_text(cable_data["cable_id"]),
        created_at=_dt_from_text(cable_data["created_at"]),
        updated_at=_dt_from_text(cable_data["updated_at"]),
    )


def _dt_to_str(value: datetime) -> str:
    return value.isoformat()


def _dt_from_text(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _uuid_from_text(value: str) -> UUID:
    return UUID(value)
