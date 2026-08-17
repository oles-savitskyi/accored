from __future__ import annotations

from collections.abc import Sequence

from accore.platform.configuration.candidate import ConfigurationCandidate
from accore.platform.configuration.identity import (
    ConfigurationIdentity,
    ConfigurationVersion,
)
from accore.platform.definitions import Definition
from accore.platform.metadata.compiler import MetadataCompiler
from accore.platform.metadata.registry import MetadataRegistry


class ConfigurationLoader:
    """Load configuration definitions into an isolated candidate."""

    def __init__(self, compiler: MetadataCompiler) -> None:
        self._compiler = compiler

    def load(
        self,
        definitions: Sequence[Definition],
        *,
        identity: ConfigurationIdentity,
        version: ConfigurationVersion,
    ) -> ConfigurationCandidate:
        """Compile definitions and return a loaded configuration candidate."""
        registry = MetadataRegistry()

        for definition in definitions:
            metadata = self._compiler.compile(definition)
            registry.register(metadata)

        return ConfigurationCandidate(
            identity=identity,
            version=version,
            metadata_registry=registry,
        )
