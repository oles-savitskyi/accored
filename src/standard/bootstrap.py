from __future__ import annotations

from accore.platform.configuration import (
    ConfigurationActivator,
    ConfigurationIdentity,
    ConfigurationLoader,
    ConfigurationValidator,
    ConfigurationVersion,
    MetadataResolver,
    RuntimeConfigurationBinding,
    RuntimeConfigurationContext,
)
from accore.platform.metadata import MetadataCompiler
from accore.platform.runtime.resolution import RuntimeResolver
from standard.definitions.catalogs import standard_catalog_definitions


class StandardConfigurationBootstrap:
    """Bootstrap the Standard Configuration runtime context."""

    def initialize(self) -> tuple[RuntimeConfigurationContext, RuntimeResolver]:
        """Initialize the Standard Configuration runtime context."""
        loader = ConfigurationLoader(MetadataCompiler())
        candidate = loader.load(
            standard_catalog_definitions(),
            identity=ConfigurationIdentity("standard"),
            version=ConfigurationVersion(1),
        )

        validator = ConfigurationValidator()
        validator.validate(candidate)

        active = ConfigurationActivator().activate(candidate)

        binding = RuntimeConfigurationBinding()
        binding.bind(active)

        context = binding.acquire()
        resolver = RuntimeResolver(MetadataResolver())

        return context, resolver
