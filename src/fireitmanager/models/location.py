"""Location model for describing physical placement information."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4


@dataclass(slots=True)
class Location:
    """Represents a physical location for a building or asset."""

    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation_ft: Optional[float] = None
    notes: str = ""
    location_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate the supplied location values."""
        if not self.name.strip():
            raise ValueError("Location name cannot be empty")

    def touch(self) -> None:
        """Update the modification timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        """Return a readable representation for debugging."""
        return f"Location(location_id={self.location_id!r}, name={self.name!r})"
