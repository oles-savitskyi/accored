from __future__ import annotations

from accore.platform.definitions import (
    AttributeDefinition,
    AttributeType,
    CatalogDefinition,
)
from accore.platform.foundation import Identifier
from accore.platform.metadata import MetadataCompiler
from accore.platform.object import ObjectInstance
from accore.platform.runtime import CatalogRuntime


def make_runtime(name: str = "Assortment") -> CatalogRuntime:
    definition = CatalogDefinition(
        identifier=Identifier.new(),
        name=name,
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

    return CatalogRuntime(metadata=metadata)


def test_object_instance_preserves_identity() -> None:
    identity = Identifier.new()
    object_type = make_runtime()

    instance = ObjectInstance(
        identity=identity,
        object_type=object_type,
    )

    assert instance.identity == identity


def test_object_instance_preserves_object_type() -> None:
    object_type = make_runtime()

    instance = ObjectInstance(
        identity=Identifier.new(),
        object_type=object_type,
    )

    assert instance.object_type is object_type


def test_object_instances_of_same_type_can_have_different_identities() -> None:
    object_type = make_runtime()

    first = ObjectInstance(
        identity=Identifier.new(),
        object_type=object_type,
    )
    second = ObjectInstance(
        identity=Identifier.new(),
        object_type=object_type,
    )

    assert first != second
    assert first.object_type is second.object_type


def test_object_instances_with_same_identity_are_equal() -> None:
    identity = Identifier.new()

    first = ObjectInstance(
        identity=identity,
        object_type=make_runtime("Assortment"),
    )
    second = ObjectInstance(
        identity=identity,
        object_type=make_runtime("Employees"),
    )

    assert first == second


def test_object_instance_equality_is_based_on_identity() -> None:
    identity = Identifier.new()

    first = ObjectInstance(
        identity=identity,
        object_type=make_runtime("Assortment"),
    )
    second = ObjectInstance(
        identity=Identifier.from_str(str(identity)),
        object_type=make_runtime("Employees"),
    )

    assert first == second


def test_object_instance_is_not_equal_to_other_types() -> None:
    instance = ObjectInstance(
        identity=Identifier.new(),
        object_type=make_runtime(),
    )

    assert instance != object()
