from __future__ import annotations

from accore.platform.definitions import (
    AttributeDefinition,
    AttributeType,
    CatalogDefinition,
)
from accore.platform.foundation import Identifier
from accore.platform.metadata import MetadataCompiler
from accore.platform.runtime import CatalogRuntime, RuntimeObjectType


def make_runtime() -> CatalogRuntime:
    definition = CatalogDefinition(
        identifier=Identifier.new(),
        name="Assortment",
        attributes=(
            AttributeDefinition(
                name="code",
                attribute_type=AttributeType.STRING,
                nullable=False,
                default_value="",
            ),
        ),
    )

    metadata = MetadataCompiler().compile(definition)

    return CatalogRuntime(metadata)


def test_catalog_runtime_implements_runtime_object_type() -> None:
    runtime = make_runtime()

    assert isinstance(runtime, RuntimeObjectType)


def test_runtime_object_type_exposes_metadata_identity() -> None:
    runtime = make_runtime()

    assert runtime.metadata_identity() == runtime.metadata.identifier


def test_runtime_object_type_is_structural_protocol() -> None:
    class FakeRuntimeObject:
        def metadata_identity(self) -> Identifier:
            return Identifier.new()

    runtime = FakeRuntimeObject()

    assert isinstance(runtime, RuntimeObjectType)
