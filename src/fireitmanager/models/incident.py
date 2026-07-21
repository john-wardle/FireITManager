"""Incident model for FireIT Manager."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fireitmanager.models.asset import Asset
from fireitmanager.models.camp import Camp
from fireitmanager.models.device import Device
from fireitmanager.models.person import Person


@dataclass(slots=True)
class Incident:
    """Represents a wildfire incident or operational event."""

    name: str
    incident_number: str = ""
    agency: str = ""
    operational_period: str = ""
    camps: list[Camp] = field(default_factory=list)
    personnel: list[Person] = field(default_factory=list)
    assets: list[Asset] = field(default_factory=list)
    incident_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate the incident name and ensure it is not blank."""
        if not self.name.strip():
            raise ValueError("Incident name cannot be empty")

    def add_camp(self, camp: Camp) -> None:
        """Attach a camp to this incident."""
        if camp not in self.camps:
            self.camps.append(camp)
            self.touch()

    def remove_camp(self, camp: Camp) -> None:
        """Detach a camp from this incident."""
        if camp in self.camps:
            self.camps.remove(camp)
            self.touch()

    def find_device(self, hostname: str) -> Device | None:
        """Locate a device by hostname across all associated camps."""
        for camp in self.camps:
            for building in camp.buildings:
                for device in building.devices:
                    if device.hostname.lower() == hostname.lower():
                        return device
        return None

    def summary(self) -> str:
        """Return a readable summary string for the incident."""
        return f"{self.name} ({self.incident_number or 'no-number'})"

    def touch(self) -> None:
        """Update the modification timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        """Return a readable representation for debugging."""
        return f"Incident(incident_id={self.incident_id!r}, name={self.name!r})"
