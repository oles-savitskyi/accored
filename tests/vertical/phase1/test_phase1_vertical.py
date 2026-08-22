from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationIdentity,
    ConfigurationVersion,
    MetadataResolver,
    RuntimeConfigurationContext,
)
from accore.platform.metadata import MetadataCompiler, MetadataRegistry
from accore.platform.runtime.catalog import CatalogRuntime
from accore.platform.runtime.resolution import RuntimeResolver
from standard.definitions.assortment import (
    ASSORTMENT_ID,
    AssortmentDefinition,
)


def test_phase1_vertical_slice() -> None:
    # 1. Definition
    definition = AssortmentDefinition()

    # 2. Validation
    definition.validate()

    # 3. Compilation
    compiler = MetadataCompiler()
    metadata = compiler.compile(definition)

    # 4. Registration
    registry = MetadataRegistry()
    registry.register(metadata)

    # 5. Definition no longer required
    del definition

    # 6. Runtime resolution
    configuration = ActiveConfiguration(
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(1),
        metadata_registry=registry,
    )
    context = RuntimeConfigurationContext(configuration)
    resolver = RuntimeResolver(MetadataResolver())

    runtime = resolver.resolve(context, ASSORTMENT_ID)
    # 7. Runtime contract
    assert isinstance(runtime, CatalogRuntime)

    # 8. Runtime exposes metadata
    assert runtime.metadata.identifier == ASSORTMENT_ID
    assert runtime.metadata.name == "Assortment"
