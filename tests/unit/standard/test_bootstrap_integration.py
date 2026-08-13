from accore.platform.metadata import MetadataRegistry
from accore.platform.runtime.resolution import RuntimeResolver
from standard.bootstrap import StandardConfigurationBootstrap
from standard.definitions.catalogs import standard_catalog_definitions


def test_standard_bootstrap_registers_all_standard_catalogs() -> None:
    bootstrap = StandardConfigurationBootstrap()

    registry, resolver = bootstrap.initialize()

    definitions = standard_catalog_definitions()

    assert isinstance(registry, MetadataRegistry)
    assert isinstance(resolver, RuntimeResolver)

    for definition in definitions:
        identifier = definition.require_identifier()

        assert registry.contains(identifier)

        metadata = registry.get(identifier)

        assert metadata.identifier == identifier
        assert metadata.source_definition_id == identifier
        assert metadata.name == definition.name


def test_standard_bootstrap_metadata_matches_definitions() -> None:
    registry, _ = StandardConfigurationBootstrap().initialize()

    definitions = standard_catalog_definitions()

    for definition in definitions:
        identifier = definition.require_identifier()

        assert registry.contains(identifier)

    assert len(definitions) > 0


def test_standard_bootstrap_is_deterministic() -> None:
    first_registry, _ = StandardConfigurationBootstrap().initialize()
    second_registry, _ = StandardConfigurationBootstrap().initialize()

    definitions = standard_catalog_definitions()

    for definition in definitions:
        identifier = definition.require_identifier()

        first = first_registry.get(identifier)
        second = second_registry.get(identifier)

        assert first == second
