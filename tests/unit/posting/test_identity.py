from accore.platform.posting import (
    DefaultPostingOperationIdentityFactory,
    DefaultPostingParticipantOperationIdentityFactory,
    PostingOperationIdentity,
)


def test_default_posting_operation_identity_factory_creates_fresh_identity() -> None:
    factory = DefaultPostingOperationIdentityFactory()

    first = factory.new()
    second = factory.new()

    assert first != second
    assert first.value
    assert second.value


def test_participant_operation_identity_factory_is_deterministic() -> None:
    factory = DefaultPostingParticipantOperationIdentityFactory()
    posting_identity = PostingOperationIdentity("posting-1")

    first = factory.derive(posting_identity, "valuation", "establish")
    second = factory.derive(posting_identity, "valuation", "establish")

    assert first == second


def test_participant_operation_identity_factory_separates_operation_dimensions() -> None:
    factory = DefaultPostingParticipantOperationIdentityFactory()
    posting_identity = PostingOperationIdentity("posting-1")

    establish = factory.derive(posting_identity, "valuation", "establish")
    remove = factory.derive(posting_identity, "valuation", "remove")
    register = factory.derive(posting_identity, "register", "establish")

    assert len({establish, remove, register}) == 3
