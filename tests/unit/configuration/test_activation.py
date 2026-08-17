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


def test_initial_state_is_empty() -> None:
    activator = ConfigurationActivator()

    assert activator.current() is None


def test_successful_first_activation() -> None:
    activator = ConfigurationActivator()
    candidate = make_candidate(state=ConfigurationLifecycleState.VALIDATED)

    active = activator.activate(candidate)

    assert active is activator.current()


def test_activation_preserves_identity() -> None:
    activator = ConfigurationActivator()
    candidate = make_candidate(state=ConfigurationLifecycleState.VALIDATED)

    active = activator.activate(candidate)

    assert active.identity == candidate.identity


def test_activation_preserves_version() -> None:
    activator = ConfigurationActivator()
    candidate = make_candidate(state=ConfigurationLifecycleState.VALIDATED)

    active = activator.activate(candidate)

    assert active.version == candidate.version


def test_activation_preserves_metadata_registry() -> None:
    activator = ConfigurationActivator()
    candidate = make_candidate(state=ConfigurationLifecycleState.VALIDATED)

    active = activator.activate(candidate)

    assert active.metadata_registry is candidate.metadata_registry


def test_activation_replaces_previous_configuration() -> None:
    activator = ConfigurationActivator()

    first = make_candidate(state=ConfigurationLifecycleState.VALIDATED)
    second = make_candidate(state=ConfigurationLifecycleState.VALIDATED)

    first_active = activator.activate(first)
    second_active = activator.activate(second)

    assert activator.current() is second_active
    assert activator.current() is not first_active


def test_loaded_candidate_cannot_be_activated() -> None:
    activator = ConfigurationActivator()
    candidate = make_candidate(state=ConfigurationLifecycleState.LOADED)

    with pytest.raises(ValueError, match="VALIDATED"):
        activator.activate(candidate)

    assert activator.current() is None


def test_failed_activation_preserves_previous_configuration() -> None:
    activator = ConfigurationActivator()

    valid = make_candidate(state=ConfigurationLifecycleState.VALIDATED)
    invalid = make_candidate(state=ConfigurationLifecycleState.LOADED)

    active = activator.activate(valid)

    with pytest.raises(ValueError):
        activator.activate(invalid)

    assert activator.current() is active


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
