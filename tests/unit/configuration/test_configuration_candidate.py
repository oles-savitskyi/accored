import pytest

from accore.platform.configuration import (
    ConfigurationCandidate,
    ConfigurationIdentity,
    ConfigurationLifecycleState,
    ConfigurationVersion,
)
from accore.platform.metadata import MetadataRegistry


def test_configuration_candidate_is_created_in_loaded_state() -> None:
    registry = MetadataRegistry()

    candidate = ConfigurationCandidate(
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(1),
        metadata_registry=registry,
    )

    assert candidate.identity == ConfigurationIdentity("standard")
    assert candidate.version == ConfigurationVersion(1)
    assert candidate.metadata_registry is registry
    assert candidate.state is ConfigurationLifecycleState.LOADED


def test_configuration_candidate_state_is_not_constructor_argument() -> None:
    registry = MetadataRegistry()

    with pytest.raises(TypeError):
        ConfigurationCandidate(
            identity=ConfigurationIdentity("standard"),
            version=ConfigurationVersion(1),
            metadata_registry=registry,
            state=ConfigurationLifecycleState.ACTIVE,
        )


def test_configuration_candidates_have_isolated_registries() -> None:
    registry_a = MetadataRegistry()
    registry_b = MetadataRegistry()

    candidate_a = ConfigurationCandidate(
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(1),
        metadata_registry=registry_a,
    )
    candidate_b = ConfigurationCandidate(
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(2),
        metadata_registry=registry_b,
    )

    assert candidate_a.metadata_registry is not candidate_b.metadata_registry
