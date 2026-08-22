from accore.platform.runtime.resolution import RuntimeResolver
from standard.bootstrap import StandardConfigurationBootstrap
from standard.definitions.catalogs import standard_catalog_definitions


def test_standard_bootstrap_registers_all_standard_catalogs() -> None:
    bootstrap = StandardConfigurationBootstrap()

    context, resolver = bootstrap.initialize()

    definitions = standard_catalog_definitions()

    assert isinstance(resolver, RuntimeResolver)

    for definition in definitions:
        identifier = definition.require_identifier()
        runtime = resolver.resolve(context, identifier)

        metadata = runtime.metadata

        assert metadata.identifier == identifier
        assert metadata.source_definition_id == identifier
        assert metadata.name == definition.name


def test_standard_bootstrap_is_deterministic() -> None:
    first_context, first_resolver = StandardConfigurationBootstrap().initialize()
    second_context, second_resolver = StandardConfigurationBootstrap().initialize()

    definitions = standard_catalog_definitions()

    for definition in definitions:
        identifier = definition.require_identifier()
        first_runtime = first_resolver.resolve(first_context, identifier)
        second_runtime = second_resolver.resolve(second_context, identifier)

        first = first_runtime.metadata
        second = second_runtime.metadata

        assert first == second
