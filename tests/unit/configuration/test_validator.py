from accore.platform.configuration import (
    ConfigurationCandidate,
    ConfigurationIdentity,
    ConfigurationLifecycleState,
    ConfigurationValidator,
    ConfigurationVersion,
)
from accore.platform.definitions import CatalogDefinition
from accore.platform.foundation import Identifier
from accore.platform.metadata import MetadataCompiler, MetadataRegistry


def make_candidate() -> ConfigurationCandidate:
    registry = MetadataRegistry()

    definition = CatalogDefinition(
        identifier=Identifier.new(),
        name="Products",
    )

    metadata = MetadataCompiler().compile(definition)
    registry.register(metadata)

    return ConfigurationCandidate(
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(1),
        metadata_registry=registry,
    )


def test_valid_candidate_transitions_to_validated() -> None:
    candidate = make_candidate()

    ConfigurationValidator().validate(candidate)

    assert candidate.state is ConfigurationLifecycleState.VALIDATED


def test_empty_candidate_can_be_validated() -> None:
    candidate = ConfigurationCandidate(
        identity=ConfigurationIdentity("standard"),
        version=ConfigurationVersion(1),
        metadata_registry=MetadataRegistry(),
    )

    ConfigurationValidator().validate(candidate)

    assert candidate.state is ConfigurationLifecycleState.VALIDATED


def test_validation_is_idempotent() -> None:
    candidate = make_candidate()
    validator = ConfigurationValidator()

    validator.validate(candidate)
    validator.validate(candidate)

    assert candidate.state is ConfigurationLifecycleState.VALIDATED
