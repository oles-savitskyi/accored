from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationIdentity,
    ConfigurationVersion,
    MetadataResolver,
    RuntimeConfigurationContext,
)
from accore.platform.definitions import (
    AttributeDefinition,
    AttributeType,
    CatalogDefinition,
)
from accore.platform.foundation import Identifier
from accore.platform.metadata import MetadataCompiler, MetadataRegistry
from accore.platform.runtime import CatalogRuntime, RuntimeResolver


def test_phase2_definition_to_runtime_vertical_slice() -> None:
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
    compiler = MetadataCompiler()
    metadata = compiler.compile(definition)
    registry = MetadataRegistry()
    registry.register(metadata)

    configuration = ActiveConfiguration(
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(1),
        published_metadata=registry.publish(),
    )
    context = RuntimeConfigurationContext(configuration)
    resolver = RuntimeResolver(MetadataResolver())

    runtime = resolver.resolve(context, definition.identifier)

    assert isinstance(runtime, CatalogRuntime)
