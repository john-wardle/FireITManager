"""Building model for incident camp infrastructure."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fireitmanager.models.device import Device
from fireitmanager.models.enums import BuildingType
from fireitmanager.models.location import Location


@dataclass(slots=True)
class Building:
    """Represents a physical building or shelter within a camp."""

    name: str
    building_type: BuildingType = BuildingType.OTHER
    location: Location | None = None
    devices: list[Device] = field(default_factory=list)
    building_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate the building name."""
        if not self.name.strip():
            raise ValueError("Building name cannot be empty")

    def add_device(self, device: Device) -> None:
        """Attach a device to this building."""
        if device not in self.devices:
            self.devices.append(device)
            device.assigned_building = self
            device.touch()
            self.touch()

    def remove_device(self, device: Device) -> None:
        """Detach a device from this building."""
        if device in self.devices:
            self.devices.remove(device)
            device.assigned_building = None
            device.touch()
            self.touch()

    def touch(self) -> None:
        """Update the modification timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        """Return a readable representation for debugging."""
        return f"Building(building_id={self.building_id!r}, name={self.name!r})"
