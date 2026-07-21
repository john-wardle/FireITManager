"""Person model for incident personnel."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fireitmanager.models.device import Device


@dataclass(slots=True)
class Person:
    """Represents a person associated with an incident."""

    name: str
    position: str = ""
    agency: str = ""
    assigned_devices: list[Device] = field(default_factory=list)
    person_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate the person name."""
        if not self.name.strip():
            raise ValueError("Person name cannot be empty")

    def assign_device(self, device: Device) -> None:
        """Assign a device to the person."""
        if device not in self.assigned_devices:
            self.assigned_devices.append(device)
            self.touch()

    def touch(self) -> None:
        """Update the modification timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        """Return a readable representation for debugging."""
        return f"Person(person_id={self.person_id!r}, name={self.name!r})"
