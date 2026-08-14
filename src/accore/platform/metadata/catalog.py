from __future__ import annotations

from dataclasses import dataclass

from accore.platform.foundation import Identifier
from accore.platform.metadata.attribute import AttributeMetadata
from accore.platform.metadata.base import Metadata, MetadataType


@dataclass(frozen=True, slots=True)
class CatalogMetadata(Metadata):
    """Runtime-independent metadata representation of a catalog."""

    attributes: tuple[AttributeMetadata, ...] = ()

    def __init__(
        self,
        identifier: Identifier,
        name: str,
        source_definition_id: Identifier,
        normalized_content: tuple[tuple[str, str], ...] = (),
        attributes: tuple[AttributeMetadata, ...] = (),
    ) -> None:
        super().__init__(
            identifier=identifier,
            metadata_type=MetadataType.CATALOG,
            name=name,
            source_definition_id=source_definition_id,
            normalized_content=normalized_content,
        )
        object.__setattr__(self, "attributes", attributes)
