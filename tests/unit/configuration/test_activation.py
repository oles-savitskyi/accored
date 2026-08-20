import pytest

from accore.platform.configuration import (
    ConfigurationActivator,
    ConfigurationCandidate,
    ConfigurationIdentity,
    ConfigurationLifecycleState,
    ConfigurationVersion,
)
from accore.platform.metadata.registry import MetadataRegistry


def make_candidate(
    state: ConfigurationLifecycleState = ConfigurationLifecycleState.LOADED,
) -> ConfigurationCandidate:
    candidate = ConfigurationCandidate(
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(1),
        metadata_registry=MetadataRegistry(),
    )

    if state is ConfigurationLifecycleState.VALIDATED:
        candidate.mark_validated()

    return candidate


def test_activation_creates_active_configuration() -> None:
    activator = ConfigurationActivator()
    candidate = make_candidate(state=ConfigurationLifecycleState.VALIDATED)

    active = activator.activate(candidate)

    assert active.identity == candidate.identity
    assert active.version == candidate.version
    assert active.metadata_registry is candidate.metadata_registry


def test_activation_is_stateless() -> None:
    activator = ConfigurationActivator()

    first_candidate = make_candidate(
        state=ConfigurationLifecycleState.VALIDATED,
    )
    second_candidate = make_candidate(
        state=ConfigurationLifecycleState.VALIDATED,
    )

    first = activator.activate(first_candidate)
    second = activator.activate(second_candidate)

    assert first is not second
    assert first.identity == first_candidate.identity
    assert second.identity == second_candidate.identity


def test_activation_rejects_non_validated_candidate() -> None:
    activator = ConfigurationActivator()
    candidate = make_candidate(state=ConfigurationLifecycleState.LOADED)

    with pytest.raises(ValueError, match="VALIDATED"):
        activator.activate(candidate)


def test_activation_does_not_mutate_candidate() -> None:
    activator = ConfigurationActivator()
    candidate = make_candidate(state=ConfigurationLifecycleState.VALIDATED)

    identity = candidate.identity
    version = candidate.version
    registry = candidate.metadata_registry
    state = candidate.state

    activator.activate(candidate)

    assert candidate.identity is identity
    assert candidate.version is version
    assert candidate.metadata_registry is registry
    assert candidate.state is state


def test_activator_does_not_retain_active_configuration() -> None:
    activator = ConfigurationActivator()

    assert not hasattr(activator, "_active_configuration")
