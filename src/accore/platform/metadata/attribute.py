from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from accore.platform.definitions.attribute import AttributeType


@dataclass(frozen=True, slots=True)
class AttributeMetadata:
    """Immutable runtime-independent metadata of a business attribute."""

    name: str
    attribute_type: AttributeType
    nullable: bool = True
    default_value: Any = None
    description: str = ""
    reference_target: str | None = None
