from __future__ import annotations

from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationIdentity,
    ConfigurationVersion,
    MetadataResolver,
    RuntimeConfigurationContext,
)
from accore.platform.metadata import MetadataCompiler, MetadataRegistry
from accore.platform.runtime.resolution import RuntimeResolver
from standard.definitions.catalogs import standard_catalog_definitions


class StandardConfigurationBootstrap:
    """Bootstrap the Standard Configuration runtime context."""

    def initialize(self) -> tuple[RuntimeConfigurationContext, RuntimeResolver]:
        """Initialize the Standard Configuration runtime context."""
        registry = MetadataRegistry()
        compiler = MetadataCompiler()

        for definition in standard_catalog_definitions():
            metadata = compiler.compile(definition)
            registry.register(metadata)

        configuration = ActiveConfiguration(
            identity=ConfigurationIdentity("standard"),
            version=ConfigurationVersion(1),
            published_metadata=registry.publish(),
        )

        context = RuntimeConfigurationContext(configuration)
        resolver = RuntimeResolver(MetadataResolver())

        return context, resolver
