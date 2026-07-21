"""Camp model representing an operational camp within an incident."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fireitmanager.models.building import Building
from fireitmanager.models.network import Network


@dataclass(slots=True)
class Camp:
    """Represents a camp associated with an incident."""

    name: str
    buildings: list[Building] = field(default_factory=list)
    networks: list[Network] = field(default_factory=list)
    camp_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate the camp name."""
        if not self.name.strip():
            raise ValueError("Camp name cannot be empty")

    def add_building(self, building: Building) -> None:
        """Attach a building to the camp."""
        if building not in self.buildings:
            self.buildings.append(building)
            self.touch()

    def add_network(self, network: Network) -> None:
        """Attach a network to the camp."""
        if network not in self.networks:
            self.networks.append(network)
            self.touch()

    def touch(self) -> None:
        """Update the modification timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        """Return a readable representation for debugging."""
        return f"Camp(camp_id={self.camp_id!r}, name={self.name!r})"
