from dataclasses import FrozenInstanceError

import pytest

from accore.platform.foundation.identity import Identifier
from accore.platform.integration import (
    CommandRequest,
    CommandResponse,
    ContractVersion,
    IntegrationContractIdentity,
    IntegrationContractKind,
    IntegrationError,
    IntegrationErrorCategory,
    IntegrationRequestValidationError,
    QueryRequest,
    QueryResponse,
)
from accore.platform.security.context import SecurityContext


def make_identity(
    kind: IntegrationContractKind = IntegrationContractKind.COMMAND,
) -> IntegrationContractIdentity:
    return IntegrationContractIdentity(
        namespace="standard.inventory",
        name="rebuild",
        version=ContractVersion(1, 0),
        kind=kind,
    )


def test_contract_version_accepts_zero_and_positive_components() -> None:
    assert ContractVersion(0, 0) == ContractVersion(0, 0)
    assert ContractVersion(2, 3).major == 2


@pytest.mark.parametrize("major,minor", [(-1, 0), (0, -1)])
def test_contract_version_rejects_negative_components(major: int, minor: int) -> None:
    with pytest.raises(ValueError):
        ContractVersion(major, minor)


def test_contract_identity_rejects_blank_namespace_and_name() -> None:
    with pytest.raises(ValueError, match="namespace"):
        IntegrationContractIdentity(
            "  ", "op", ContractVersion(1, 0), IntegrationContractKind.COMMAND
        )
    with pytest.raises(ValueError, match="name"):
        IntegrationContractIdentity(
            "standard", "  ", ContractVersion(1, 0), IntegrationContractKind.COMMAND
        )


def test_contract_identity_preserves_dataset_as_distinct_kind() -> None:
    identity = make_identity(IntegrationContractKind.DATASET)

    assert identity.kind is IntegrationContractKind.DATASET
    assert identity != make_identity(IntegrationContractKind.QUERY)


def test_command_and_query_requests_are_immutable_and_keep_context() -> None:
    identity = make_identity()
    request_identity = Identifier.new()
    context = SecurityContext(principal=None, session=None)
    command = CommandRequest(identity, {"force": True}, context, request_identity)
    query = QueryRequest(identity, {"limit": 10}, context, request_identity)

    assert command.contract == identity
    assert command.security_context is context
    assert query.payload == {"limit": 10}
    with pytest.raises(FrozenInstanceError):
        command.request_identity = Identifier.new()  # type: ignore[misc]


def test_responses_preserve_request_identity_and_result() -> None:
    request_identity = Identifier.new()
    command = CommandResponse(request_identity, "done")
    query = QueryResponse(request_identity, (1, 2, 3))

    assert command.request_identity == request_identity
    assert command.result == "done"
    assert query.result == (1, 2, 3)


def test_integration_errors_have_stable_category_and_base_type() -> None:
    error = IntegrationRequestValidationError("invalid payload")

    assert isinstance(error, IntegrationError)
    assert error.category is IntegrationErrorCategory.VALIDATION
    assert str(error) == "invalid payload"
