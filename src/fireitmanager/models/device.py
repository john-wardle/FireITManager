"""Device model for incident infrastructure."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fireitmanager.models.enums import DeviceStatus, DeviceType


@dataclass(slots=True)
class Device:
    """Represents a networked or support device in the incident environment."""

    hostname: str
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    ip_address: str | None = None
    mac_address: str | None = None
    device_type: DeviceType = DeviceType.OTHER
    status: DeviceStatus = DeviceStatus.UNKNOWN
    assigned_building: Building | None = None
    device_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate essential device fields."""
        if not self.hostname.strip():
            raise ValueError("Device hostname cannot be empty")

    def touch(self) -> None:
        """Update the modification timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        """Return a readable representation for debugging."""
        return f"Device(device_id={self.device_id!r}, hostname={self.hostname!r})"
