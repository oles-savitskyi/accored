from accore.platform.metadata import MetadataRegistry
from accore.platform.runtime.resolution import RuntimeResolver
from standard.bootstrap import StandardConfigurationBootstrap
from standard.definitions.catalogs import standard_catalog_definitions


def test_standard_configuration_bootstrap_exposes_initialize_contract() -> None:
    bootstrap = StandardConfigurationBootstrap()

    assert hasattr(bootstrap, "initialize")


def test_standard_configuration_bootstrap_creates_runtime_components() -> None:
    bootstrap = StandardConfigurationBootstrap()

    registry, resolver = bootstrap.initialize()

    assert isinstance(registry, MetadataRegistry)
    assert isinstance(resolver, RuntimeResolver)


def test_standard_configuration_bootstrap_registers_standard_catalogs() -> None:
    bootstrap = StandardConfigurationBootstrap()

    registry, _ = bootstrap.initialize()

    definitions = standard_catalog_definitions()

    for definition in definitions:
        identifier = definition.require_identifier()

        assert registry.contains(identifier)

        metadata = registry.get(identifier)

        assert metadata.name == definition.name
