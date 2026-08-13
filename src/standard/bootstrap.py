from __future__ import annotations

from accore.platform.metadata import MetadataCompiler, MetadataRegistry
from accore.platform.runtime.resolution import RuntimeResolver
from standard.definitions.catalogs import standard_catalog_definitions


class StandardConfigurationBootstrap:
    """Bootstrap the Standard Configuration runtime context."""

    def initialize(self) -> tuple[MetadataRegistry, RuntimeResolver]:
        """Initialize the Standard Configuration runtime context."""
        registry = MetadataRegistry()
        compiler = MetadataCompiler()

        for definition in standard_catalog_definitions():
            metadata = compiler.compile(definition)
            registry.register(metadata)

        resolver = RuntimeResolver(registry)

        return registry, resolver
