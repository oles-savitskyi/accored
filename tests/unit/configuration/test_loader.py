from __future__ import annotations

import pytest

from accore.platform.configuration import (
    ConfigurationCandidate,
    ConfigurationIdentity,
    ConfigurationLifecycleState,
    ConfigurationLoader,
    ConfigurationVersion,
)
from accore.platform.definitions import CatalogDefinition
from accore.platform.foundation import DefinitionError, Identifier
from accore.platform.metadata import MetadataCompiler


def make_identity() -> ConfigurationIdentity:
    return ConfigurationIdentity("standard")


def make_version() -> ConfigurationVersion:
    return ConfigurationVersion(1)


def make_catalog(name: str) -> CatalogDefinition:
    return CatalogDefinition(
        identifier=Identifier.new(),
        name=name,
    )


def test_load_empty_definitions_returns_loaded_candidate() -> None:
    loader = ConfigurationLoader(MetadataCompiler())

    candidate = loader.load(
        [],
        identity=make_identity(),
        version=make_version(),
    )

    assert isinstance(candidate, ConfigurationCandidate)
    assert candidate.state is ConfigurationLifecycleState.LOADED
    assert candidate.identity == make_identity()
    assert candidate.version == make_version()


def test_load_compiles_and_registers_definition() -> None:
    loader = ConfigurationLoader(MetadataCompiler())
    definition = make_catalog("Products")

    candidate = loader.load(
        [definition],
        identity=make_identity(),
        version=make_version(),
    )

    metadata = candidate.metadata_registry.get(definition.require_identifier())

    assert metadata.name == "Products"
    assert metadata.source_definition_id == definition.require_identifier()


def test_load_registers_multiple_definitions() -> None:
    loader = ConfigurationLoader(MetadataCompiler())
    first = make_catalog("Products")
    second = make_catalog("Customers")

    candidate = loader.load(
        [first, second],
        identity=make_identity(),
        version=make_version(),
    )

    assert candidate.metadata_registry.contains(first.require_identifier())
    assert candidate.metadata_registry.contains(second.require_identifier())


def test_each_load_creates_an_isolated_registry() -> None:
    loader = ConfigurationLoader(MetadataCompiler())
    definition = make_catalog("Products")

    first = loader.load(
        [definition],
        identity=make_identity(),
        version=make_version(),
    )
    second = loader.load(
        [],
        identity=make_identity(),
        version=make_version(),
    )

    assert first.metadata_registry is not second.metadata_registry
    assert first.metadata_registry.contains(definition.require_identifier())
    assert not second.metadata_registry.contains(definition.require_identifier())


def test_compilation_failure_does_not_return_candidate() -> None:
    loader = ConfigurationLoader(MetadataCompiler())

    invalid_definition = CatalogDefinition(
        identifier=None,
        name="Products",
    )

    with pytest.raises(DefinitionError):
        loader.load(
            [invalid_definition],
            identity=make_identity(),
            version=make_version(),
        )


def test_duplicate_metadata_identity_fails_loading() -> None:
    loader = ConfigurationLoader(MetadataCompiler())
    identifier = Identifier.new()

    first = CatalogDefinition(
        identifier=identifier,
        name="Products",
    )
    second = CatalogDefinition(
        identifier=identifier,
        name="Products Duplicate",
    )

    with pytest.raises(KeyError):
        loader.load(
            [first, second],
            identity=make_identity(),
            version=make_version(),
        )


def test_successful_load_does_not_activate_candidate() -> None:
    loader = ConfigurationLoader(MetadataCompiler())

    candidate = loader.load(
        [make_catalog("Products")],
        identity=make_identity(),
        version=make_version(),
    )

    assert candidate.state is ConfigurationLifecycleState.LOADED
