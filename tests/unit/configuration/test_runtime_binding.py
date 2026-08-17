from __future__ import annotations

import pytest

from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationIdentity,
    ConfigurationVersion,
    RuntimeConfigurationBinding,
)
from accore.platform.configuration.runtime_binding import (
    RuntimeConfigurationBindingError,
)
from accore.platform.metadata import MetadataRegistry


def make_configuration(
    identity: str = "standard",
    version: int = 1,
) -> ActiveConfiguration:
    return ActiveConfiguration(
        identity=ConfigurationIdentity(identity),
        version=ConfigurationVersion(version),
        metadata_registry=MetadataRegistry(),
    )


def test_initial_state_is_unbound() -> None:
    binding = RuntimeConfigurationBinding()

    with pytest.raises(RuntimeConfigurationBindingError):
        binding.get()


def test_first_binding_succeeds() -> None:
    binding = RuntimeConfigurationBinding()
    configuration = make_configuration()

    binding.bind(configuration)

    assert binding.get() is configuration


def test_identity_is_preserved() -> None:
    binding = RuntimeConfigurationBinding()
    configuration = make_configuration(identity="standard")

    binding.bind(configuration)

    assert binding.get().identity == configuration.identity


def test_version_is_preserved() -> None:
    binding = RuntimeConfigurationBinding()
    configuration = make_configuration(version=2)

    binding.bind(configuration)

    assert binding.get().version == configuration.version


def test_metadata_registry_is_preserved() -> None:
    binding = RuntimeConfigurationBinding()
    configuration = make_configuration()

    binding.bind(configuration)

    assert binding.get().metadata_registry is configuration.metadata_registry


def test_replacement_succeeds() -> None:
    binding = RuntimeConfigurationBinding()
    first = make_configuration(identity="standard", version=1)
    second = make_configuration(identity="standard", version=2)

    binding.bind(first)
    binding.bind(second)

    assert binding.get() is second


def test_previous_configuration_remains_unchanged() -> None:
    binding = RuntimeConfigurationBinding()
    first = make_configuration(identity="standard", version=1)
    second = make_configuration(identity="standard", version=2)

    binding.bind(first)
    binding.bind(second)

    assert first.identity == ConfigurationIdentity("standard")
    assert first.version == ConfigurationVersion(1)


def test_new_configuration_remains_unchanged() -> None:
    binding = RuntimeConfigurationBinding()
    configuration = make_configuration()

    binding.bind(configuration)

    assert binding.get() is configuration


def test_binding_does_not_activate_configuration() -> None:
    binding = RuntimeConfigurationBinding()
    configuration = make_configuration()

    binding.bind(configuration)

    assert binding.get() is configuration
