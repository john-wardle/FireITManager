"""Enumerations for FireIT Manager domain models."""

from __future__ import annotations

from enum import Enum


class DeviceType(str, Enum):
    """Supported device categories."""

    ROUTER = "router"
    SWITCH = "switch"
    ACCESS_POINT = "access_point"
    SERVER = "server"
    WORKSTATION = "workstation"
    PHONE = "phone"
    OTHER = "other"


class BuildingType(str, Enum):
    """Supported building categories."""

    COMMAND_POST = "command_post"
    OPERATIONS = "operations"
    LODGING = "lodging"
    STORAGE = "storage"
    MEDICAL = "medical"
    OTHER = "other"


class CableType(str, Enum):
    """Supported cable categories."""

    COPPER = "copper"
    FIBER = "fiber"
    WIRELESS = "wireless"
    OTHER = "other"


class AssetStatus(str, Enum):
    """Lifecycle status values for assets."""

    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"
    LOST = "lost"


class DeviceStatus(str, Enum):
    """Operational status values for devices."""

    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"
