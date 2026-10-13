"""Protocol-independent Integration domain contracts for AcCoreD."""

from .contract import (
    ContractVersion,
    IntegrationContract,
    IntegrationContractIdentity,
    IntegrationContractKind,
)
from .errors import (
    IntegrationAuthenticationError,
    IntegrationAuthorizationError,
    IntegrationConflictError,
    IntegrationContractNotFoundError,
    IntegrationContractValidationError,
    IntegrationContractVersionError,
    IntegrationError,
    IntegrationErrorCategory,
    IntegrationExecutionError,
    IntegrationInternalError,
    IntegrationMalformedRequestError,
    IntegrationRequestValidationError,
)
from .registry import BoundIntegrationOperation, InMemoryIntegrationOperationRegistry
from .request import CommandRequest, QueryRequest
from .response import CommandResponse, QueryResponse
from .service import DefaultIntegrationService, IntegrationService

__all__ = [
    "BoundIntegrationOperation",
    "CommandRequest",
    "CommandResponse",
    "ContractVersion",
    "DefaultIntegrationService",
    "InMemoryIntegrationOperationRegistry",
    "IntegrationAuthenticationError",
    "IntegrationAuthorizationError",
    "IntegrationConflictError",
    "IntegrationContract",
    "IntegrationContractIdentity",
    "IntegrationContractKind",
    "IntegrationContractNotFoundError",
    "IntegrationContractValidationError",
    "IntegrationContractVersionError",
    "IntegrationError",
    "IntegrationErrorCategory",
    "IntegrationExecutionError",
    "IntegrationInternalError",
    "IntegrationMalformedRequestError",
    "IntegrationRequestValidationError",
    "IntegrationService",
    "QueryRequest",
    "QueryResponse",
]
