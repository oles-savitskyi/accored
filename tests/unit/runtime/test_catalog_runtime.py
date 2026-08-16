def test_catalog_runtime_exposes_metadata() -> None: ...


def test_catalog_runtime_is_immutable() -> None: ...


import pytest

from accore.platform.definitions import (
    AttributeDefinition,
    AttributeType,
    CatalogDefinition,
)
from accore.platform.foundation import Identifier
from accore.platform.metadata import MetadataCompiler
from accore.platform.runtime import CatalogRuntime, MetadataLookupError


def test_attribute_unknown_name_raises_metadata_lookup_error() -> None:
    runtime = make_runtime()

    with pytest.raises(
        MetadataLookupError,
        match="Attribute 'unknown' does not exist in catalog 'Assortment'",
    ):
        runtime.attribute("unknown")


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
            AttributeDefinition(
                name="unit",
                attribute_type=AttributeType.REFERENCE,
                reference_target="MeasureUnits",
            ),
        ),
    )

    metadata = MetadataCompiler().compile(definition)

    return CatalogRuntime(metadata=metadata)


def test_metadata_identity() -> None:
    runtime = make_runtime()

    assert runtime.metadata_identity() == runtime.metadata.identifier


def test_attributes_returns_metadata_collection() -> None:
    runtime = make_runtime()

    attributes = runtime.attributes()

    assert len(attributes) == 2
    assert attributes[0].name == "code"
    assert attributes[1].name == "unit"


def test_attribute_returns_attribute_metadata() -> None:
    runtime = make_runtime()

    attribute = runtime.attribute("unit")

    assert attribute.name == "unit"
    assert attribute.attribute_type is AttributeType.REFERENCE
    assert attribute.reference_target == "MeasureUnits"


def test_system_fields_returns_metadata_collection() -> None:
    runtime = make_runtime()

    system_fields = runtime.system_fields()

    assert len(system_fields) > 0
