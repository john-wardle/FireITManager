"""Cable model for representing connectivity between devices."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fireitmanager.models.device import Device
from fireitmanager.models.enums import CableType


@dataclass(slots=True)
class Cable:
    """Represents a physical or logical connection between devices."""

    cable_type: CableType = CableType.OTHER
    source_device: Device | None = None
    destination_device: Device | None = None
    length: float | None = None
    notes: str = ""
    cable_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate the cable definition."""
        if self.source_device is None and self.destination_device is None:
            raise ValueError("Cable must connect at least one device")

    def touch(self) -> None:
        """Update the modification timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        """Return a readable representation for debugging."""
        return f"Cable(cable_id={self.cable_id!r}, cable_type={self.cable_type!r})"
