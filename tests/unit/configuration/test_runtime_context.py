from __future__ import annotations

import pytest

from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationIdentity,
    ConfigurationVersion,
    RuntimeConfigurationBinding,
    RuntimeConfigurationBindingError,
    RuntimeConfigurationContext,
)
from accore.platform.metadata import MetadataRegistry


def make_configuration(
    identity: str = "standard",
    version: int = 1,
) -> ActiveConfiguration:
    registry = MetadataRegistry()
    return ActiveConfiguration(
        identity=ConfigurationIdentity(identity),
        version=ConfigurationVersion(version),
        published_metadata=registry.publish(),
    )


def test_acquire_returns_runtime_configuration_context() -> None:
    binding = RuntimeConfigurationBinding()
    configuration = make_configuration()

    binding.bind(configuration)

    context = binding.acquire()

    assert isinstance(context, RuntimeConfigurationContext)


def test_context_captures_configuration() -> None:
    binding = RuntimeConfigurationBinding()
    configuration = make_configuration()

    binding.bind(configuration)

    context = binding.acquire()

    assert context.configuration is configuration


def test_context_exposes_configuration_identity() -> None:
    binding = RuntimeConfigurationBinding()
    configuration = make_configuration(identity="standard")

    binding.bind(configuration)

    context = binding.acquire()

    assert context.identity == configuration.identity


def test_context_exposes_configuration_version() -> None:
    binding = RuntimeConfigurationBinding()
    configuration = make_configuration(version=2)

    binding.bind(configuration)

    context = binding.acquire()

    assert context.version == configuration.version


def test_acquire_fails_when_binding_is_unbound() -> None:
    binding = RuntimeConfigurationBinding()

    with pytest.raises(RuntimeConfigurationBindingError):
        binding.acquire()


def test_context_is_snapshot_of_configuration() -> None:
    binding = RuntimeConfigurationBinding()
    first = make_configuration(version=1)
    second = make_configuration(version=2)

    binding.bind(first)
    context = binding.acquire()

    binding.bind(second)

    assert context.configuration is first
    assert context.version == ConfigurationVersion(1)


def test_new_context_observes_replacement() -> None:
    binding = RuntimeConfigurationBinding()
    first = make_configuration(version=1)
    second = make_configuration(version=2)

    binding.bind(first)
    first_context = binding.acquire()

    binding.bind(second)
    second_context = binding.acquire()

    assert first_context.configuration is first
    assert second_context.configuration is second


def test_context_is_immutable() -> None:
    binding = RuntimeConfigurationBinding()
    configuration = make_configuration()

    binding.bind(configuration)
    context = binding.acquire()

    with pytest.raises((AttributeError, TypeError)):
        context.configuration = make_configuration(version=2)  # type: ignore[misc]
