from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from accore.platform.foundation import Identifier


class MetadataType(str, Enum):
    """Supported metadata types."""

    CATALOG = "catalog"


@dataclass(frozen=True, slots=True)
class Metadata:
    """Immutable runtime-independent representation of configuration metadata."""

    identifier: Identifier
    metadata_type: MetadataType
    name: str
    source_definition_id: Identifier
    normalized_content: tuple[tuple[str, str], ...] = ()
