"""Network model representing a collection of connected devices and cables."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fireitmanager.models.cable import Cable
from fireitmanager.models.device import Device


@dataclass(slots=True)
class Network:
    """Represents a network grouping for incident infrastructure."""

    name: str
    devices: list[Device] = field(default_factory=list)
    cables: list[Cable] = field(default_factory=list)
    network_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate the network name."""
        if not self.name.strip():
            raise ValueError("Network name cannot be empty")

    def add_device(self, device: Device) -> None:
        """Add a device to the network."""
        if device not in self.devices:
            self.devices.append(device)
            self.touch()

    def add_cable(self, cable: Cable) -> None:
        """Add a cable to the network."""
        if cable not in self.cables:
            self.cables.append(cable)
            self.touch()

    def touch(self) -> None:
        """Update the modification timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        """Return a readable representation for debugging."""
        return f"Network(network_id={self.network_id!r}, name={self.name!r})"
