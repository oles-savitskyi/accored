from accore.platform.configuration import (
    ConfigurationActivator,
    ConfigurationIdentity,
    ConfigurationLifecycleState,
    ConfigurationLoader,
    ConfigurationValidator,
    ConfigurationVersion,
    MetadataResolver,
    RuntimeConfigurationBinding,
)
from accore.platform.definitions.catalog import CatalogDefinition
from accore.platform.metadata import MetadataCompiler
from accore.platform.runtime.catalog import CatalogRuntime
from accore.platform.runtime.resolution import RuntimeResolver
from standard.definitions.assortment import ASSORTMENT_ID
from standard.definitions.catalogs import standard_catalog_definitions


def test_phase3_standard_configuration_vertical_slice() -> None:
    definitions = standard_catalog_definitions()

    loader = ConfigurationLoader(MetadataCompiler())
    candidate = loader.load(
        definitions,
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(1),
    )

    validator = ConfigurationValidator()
    validator.validate(candidate)

    activator = ConfigurationActivator()
    active = activator.activate(candidate)

    binding = RuntimeConfigurationBinding()
    binding.bind(active)

    context = binding.acquire()

    resolver = RuntimeResolver(MetadataResolver())

    runtime = resolver.resolve(context, ASSORTMENT_ID)

    assert isinstance(runtime, CatalogRuntime)
    assert runtime.metadata.identifier == ASSORTMENT_ID
    assert runtime.metadata.name == "Assortment"


def replace_assortment_definition(
    definitions,
    *,
    name: str,
):
    return [
        (
            CatalogDefinition(
                identifier=definition.require_identifier(),
                name=name,
            )
            if definition.require_identifier() == ASSORTMENT_ID
            else definition
        )
        for definition in definitions
    ]


def test_phase3_configuration_replacement_preserves_context_snapshot() -> None:
    loader = ConfigurationLoader(MetadataCompiler())
    activator = ConfigurationActivator()
    binding = RuntimeConfigurationBinding()

    definitions_v1 = standard_catalog_definitions()

    candidate_v1 = loader.load(
        definitions_v1,
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(1),
    )
    validator = ConfigurationValidator()
    validator.validate(candidate_v1)

    assert candidate_v1.state is ConfigurationLifecycleState.VALIDATED

    active_v1 = activator.activate(candidate_v1)
    binding.bind(active_v1)

    context_v1 = binding.acquire()

    definitions_v2 = replace_assortment_definition(
        standard_catalog_definitions(),
        name="Assortment v2",
    )

    candidate_v2 = loader.load(
        definitions_v2,
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(2),
    )

    validator.validate(candidate_v2)

    assert candidate_v2.state is ConfigurationLifecycleState.VALIDATED

    active_v2 = activator.activate(candidate_v2)
    binding.bind(active_v2)

    context_v2 = binding.acquire()

    resolver = RuntimeResolver(MetadataResolver())

    runtime_v1 = resolver.resolve(context_v1, ASSORTMENT_ID)
    runtime_v2 = resolver.resolve(context_v2, ASSORTMENT_ID)

    assert runtime_v1.metadata.identifier == ASSORTMENT_ID
    assert runtime_v2.metadata.identifier == ASSORTMENT_ID

    assert runtime_v1.metadata.name == "Assortment"
    assert runtime_v2.metadata.name == "Assortment v2"

    assert context_v1.version == ConfigurationVersion(1)
    assert context_v2.version == ConfigurationVersion(2)

    assert context_v1.configuration is active_v1
    assert context_v2.configuration is active_v2

    assert resolver.resolve(context_v1, ASSORTMENT_ID).metadata.name == "Assortment"

    assert resolver.resolve(context_v2, ASSORTMENT_ID).metadata.name == "Assortment v2"
