from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SystemFieldType(str, Enum):
    """Supported platform system field types."""

    ULID = "ulid"
    STRING = "string"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    INTEGER = "integer"


@dataclass(frozen=True, slots=True)
class SystemFieldMetadata:
    """Immutable metadata describing a platform system field."""

    name: str
    field_type: SystemFieldType
    nullable: bool
    required: bool
