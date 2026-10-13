from __future__ import annotations

from dataclasses import dataclass

import pytest

from accore.platform.foundation.identity import Identifier
from accore.platform.integration import (
    BoundIntegrationOperation,
    CommandRequest,
    ContractVersion,
    DefaultIntegrationService,
    InMemoryIntegrationOperationRegistry,
    IntegrationAuthenticationError,
    IntegrationAuthorizationError,
    IntegrationContractIdentity,
    IntegrationContractKind,
    IntegrationErrorCategory,
    IntegrationExecutionError,
    IntegrationInternalError,
    IntegrationRequestValidationError,
    QueryRequest,
)
from accore.platform.processing.errors import ProcessingNotFoundError
from accore.platform.security.authorization import (
    AuthorizationDecision,
    AuthorizationDenyReason,
    AuthorizationOutcome,
)
from accore.platform.security.context import SecurityContext
from accore.platform.security.errors import (
    AuthenticationFailedError,
    AuthorizationDeniedError,
)


@dataclass(frozen=True, slots=True)
class ExampleContract:
    identity: IntegrationContractIdentity
    description: str = "Example operation"


class ExampleBinding:
    def __init__(self, result: object = "ok", failure: Exception | None = None) -> None:
        self.result = result
        self.failure = failure
        self.received_request: object | None = None
        self.calls = 0

    def execute(self, request: object) -> object:
        self.calls += 1
        self.received_request = request
        if self.failure is not None:
            raise self.failure
        return self.result


def make_identity(
    kind: IntegrationContractKind = IntegrationContractKind.COMMAND,
) -> IntegrationContractIdentity:
    return IntegrationContractIdentity(
        namespace="standard.inventory",
        name="rebuild",
        version=ContractVersion(1, 0),
        kind=kind,
    )


def make_request(
    kind: IntegrationContractKind = IntegrationContractKind.COMMAND,
) -> CommandRequest[object] | QueryRequest[object]:
    request_type = CommandRequest if kind is IntegrationContractKind.COMMAND else QueryRequest
    return request_type(
        contract=make_identity(kind),
        payload={"input": 1},
        security_context=SecurityContext(principal=None, session=None),
        request_identity=Identifier.new(),
    )


def make_service(
    kind: IntegrationContractKind = IntegrationContractKind.COMMAND,
    binding: ExampleBinding | None = None,
) -> tuple[DefaultIntegrationService, ExampleBinding]:
    operation_binding = binding or ExampleBinding()
    registry = InMemoryIntegrationOperationRegistry()
    registry.register(
        BoundIntegrationOperation(
            contract=ExampleContract(make_identity(kind)),  # type: ignore[arg-type]
            binding=operation_binding,
        )
    )
    return DefaultIntegrationService(registry), operation_binding


def test_execute_command_preserves_request_identity_and_passes_full_request() -> None:
    service, binding = make_service()
    request = make_request()

    response = service.execute_command(request)  # type: ignore[arg-type]

    assert response.request_identity is request.request_identity
    assert response.result == "ok"
    assert binding.received_request is request
    assert binding.calls == 1


def test_execute_query_returns_query_response_and_preserves_identity() -> None:
    service, binding = make_service(IntegrationContractKind.QUERY)
    request = make_request(IntegrationContractKind.QUERY)

    response = service.execute_query(request)  # type: ignore[arg-type]

    assert response.request_identity is request.request_identity
    assert response.result == "ok"
    assert binding.received_request is request


def test_command_rejects_query_contract_before_registry_execution() -> None:
    service, binding = make_service(IntegrationContractKind.QUERY)
    request = make_request(IntegrationContractKind.QUERY)

    with pytest.raises(IntegrationRequestValidationError, match="Expected a command"):
        service.execute_command(request)  # type: ignore[arg-type]

    assert binding.calls == 0


def test_query_rejects_command_contract_before_registry_execution() -> None:
    service, binding = make_service()
    request = make_request()

    with pytest.raises(IntegrationRequestValidationError, match="Expected a query"):
        service.execute_query(request)  # type: ignore[arg-type]

    assert binding.calls == 0


@pytest.mark.parametrize(
    ("failure", "error_type", "category"),
    [
        (
            AuthorizationDeniedError(
                AuthorizationDecision(
                    AuthorizationOutcome.DENY,
                    AuthorizationDenyReason.MISSING_PERMISSION,
                )
            ),
            IntegrationAuthorizationError,
            IntegrationErrorCategory.AUTHORIZATION,
        ),
        (
            AuthenticationFailedError("private credential detail"),
            IntegrationAuthenticationError,
            IntegrationErrorCategory.AUTHENTICATION,
        ),
        (
            ProcessingNotFoundError("private processing detail"),
            IntegrationExecutionError,
            IntegrationErrorCategory.EXECUTION,
        ),
        (
            RuntimeError("private internal detail"),
            IntegrationInternalError,
            IntegrationErrorCategory.INTERNAL,
        ),
    ],
)
def test_known_and_unexpected_failures_are_mapped_to_stable_errors(
    failure: Exception,
    error_type: type[Exception],
    category: IntegrationErrorCategory,
) -> None:
    service, _ = make_service(binding=ExampleBinding(failure=failure))

    with pytest.raises(error_type) as captured:
        service.execute_command(make_request())  # type: ignore[arg-type]

    assert captured.value.category is category
    assert str(failure) not in str(captured.value)


def test_integration_errors_from_binding_are_preserved() -> None:
    from accore.platform.integration import IntegrationAuthorizationError

    failure = IntegrationAuthorizationError("already mapped")
    service, _ = make_service(binding=ExampleBinding(failure=failure))

    with pytest.raises(IntegrationAuthorizationError) as captured:
        service.execute_command(make_request())  # type: ignore[arg-type]

    assert captured.value is failure
