"""Asset model for incident resources and equipment."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fireitmanager.models.enums import AssetStatus
from fireitmanager.models.person import Person


@dataclass(slots=True)
class Asset:
    """Represents an operational asset such as a generator, vehicle, or tool."""

    name: str
    owner: str = ""
    acquisition_type: str = ""
    barcode: str = ""
    status: AssetStatus = AssetStatus.AVAILABLE
    assigned_person: Person | None = None
    asset_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate the asset name."""
        if not self.name.strip():
            raise ValueError("Asset name cannot be empty")

    def assign_person(self, person: Person) -> None:
        """Assign an owner or responsible person to the asset."""
        self.assigned_person = person
        self.touch()

    def touch(self) -> None:
        """Update the modification timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        """Return a readable representation for debugging."""
        return f"Asset(asset_id={self.asset_id!r}, name={self.name!r})"
