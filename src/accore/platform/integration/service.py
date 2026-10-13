"""Protocol-independent Integration execution service."""

from __future__ import annotations

from typing import Protocol, cast

from accore.platform.foundation.identity import Identifier
from accore.platform.processing.errors import (
    ProcessingDefinitionMismatchError,
    ProcessingExecutionError,
    ProcessingNotFoundError,
)
from accore.platform.security.context import SecurityContext
from accore.platform.security.errors import (
    AuthenticationError,
    AuthorizationDeniedError,
    SecurityConfigurationError,
    SecurityInfrastructureError,
)

from .contract import IntegrationContractIdentity, IntegrationContractKind
from .errors import (
    IntegrationAuthenticationError,
    IntegrationAuthorizationError,
    IntegrationContractValidationError,
    IntegrationError,
    IntegrationExecutionError,
    IntegrationInternalError,
    IntegrationRequestValidationError,
)
from .registry import IntegrationOperationRegistry
from .request import CommandRequest, QueryRequest
from .response import CommandResponse, QueryResponse


class IntegrationService(Protocol):
    """Public entry point for protocol-independent command and query execution."""

    def execute_command[P, R](self, request: CommandRequest[P]) -> CommandResponse[R]:
        """Resolve and execute a command contract."""
        ...

    def execute_query[P, R](self, request: QueryRequest[P]) -> QueryResponse[R]:
        """Resolve and execute a query contract."""
        ...


class DefaultIntegrationService:
    """Execute Integration requests through registered operation bindings.

    The service owns boundary validation and stable error mapping. Business
    execution and authoritative Runtime authorization remain with the binding
    and the Runtime it delegates to.
    """

    def __init__(self, registry: IntegrationOperationRegistry) -> None:
        self._registry = registry

    def execute_command[P, R](self, request: CommandRequest[P]) -> CommandResponse[R]:
        """Execute a command while preserving its request identity."""
        operation_result = self._execute(request, IntegrationContractKind.COMMAND)
        return CommandResponse(
            request_identity=request.request_identity,
            result=cast(R, operation_result),
        )

    def execute_query[P, R](self, request: QueryRequest[P]) -> QueryResponse[R]:
        """Execute a query while preserving its request identity."""
        operation_result = self._execute(request, IntegrationContractKind.QUERY)
        return QueryResponse(
            request_identity=request.request_identity,
            result=cast(R, operation_result),
        )

    def _execute[P](
        self,
        request: CommandRequest[P] | QueryRequest[P],
        expected_kind: IntegrationContractKind,
    ) -> object:
        self._validate_request(request, expected_kind)
        operation = self._registry.resolve(request.contract)

        if operation.contract.identity != request.contract:
            raise IntegrationContractValidationError(
                "Resolved Integration operation does not match the requested contract " "identity."
            )
        if operation.contract.identity.kind is not expected_kind:
            raise IntegrationContractValidationError(
                "Resolved Integration operation is not a " f"{expected_kind.value} contract."
            )

        try:
            return operation.binding.execute(request)
        except IntegrationError:
            raise
        except AuthorizationDeniedError as exc:
            raise IntegrationAuthorizationError(
                "Integration operation was not authorized."
            ) from exc
        except AuthenticationError as exc:
            raise IntegrationAuthenticationError("Integration authentication failed.") from exc
        except (SecurityConfigurationError, SecurityInfrastructureError) as exc:
            raise IntegrationInternalError("Integration security infrastructure failed.") from exc
        except (
            ProcessingDefinitionMismatchError,
            ProcessingExecutionError,
            ProcessingNotFoundError,
        ) as exc:
            raise IntegrationExecutionError("Integration operation execution failed.") from exc
        except Exception as exc:
            # Keep implementation details behind the Integration boundary.
            raise IntegrationInternalError("An internal Integration error occurred.") from exc

    @staticmethod
    def _validate_request[P](
        request: CommandRequest[P] | QueryRequest[P],
        expected_kind: IntegrationContractKind,
    ) -> None:
        if not isinstance(request, (CommandRequest, QueryRequest)):
            raise IntegrationRequestValidationError("Integration request has an unsupported type.")
        if not isinstance(request.contract, IntegrationContractIdentity):
            raise IntegrationRequestValidationError(
                "Integration request has an invalid contract identity."
            )
        if request.contract.kind is not expected_kind:
            raise IntegrationRequestValidationError(
                f"Expected a {expected_kind.value} contract, got " f"{request.contract.kind.value}."
            )
        if not isinstance(request.request_identity, Identifier):
            raise IntegrationRequestValidationError(
                "Integration request identity must be an Identifier."
            )
        if not isinstance(request.security_context, SecurityContext):
            raise IntegrationRequestValidationError(
                "Integration request must include a SecurityContext."
            )
