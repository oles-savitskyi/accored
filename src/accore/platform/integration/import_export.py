"""Contract-driven import and export models and format adapters."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from typing import Protocol, cast

from accore.platform.foundation.identity import Identifier
from accore.platform.security.context import SecurityContext

from .contract import IntegrationContract, IntegrationContractIdentity, IntegrationContractKind
from .errors import (
    IntegrationContractValidationError,
    IntegrationMalformedRequestError,
    IntegrationRequestValidationError,
)
from .registry import IntegrationOperationRegistry


class ImportContract(IntegrationContract, Protocol):
    """Contract describing the logical payload accepted by an import operation."""

    def validate(self, payload: object) -> None:
        """Validate the logical import payload against this contract."""
        ...


class ExportContract(IntegrationContract, Protocol):
    """Contract describing the request accepted by an export operation."""

    def validate(self, payload: object) -> None:
        """Validate the logical export request against this contract."""
        ...


@dataclass(frozen=True, slots=True)
class ImportRequest[P]:
    """Validated-boundary request carrying a logical import payload."""

    contract: IntegrationContractIdentity
    payload: P
    security_context: SecurityContext
    request_identity: Identifier


@dataclass(frozen=True, slots=True)
class ImportResult[R]:
    """Import operation result correlated with its originating request."""

    request_identity: Identifier
    result: R
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_metadata(self.metadata)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class ExportRequest[P]:
    """Request describing the logical content to retrieve for export."""

    contract: IntegrationContractIdentity
    payload: P
    security_context: SecurityContext
    request_identity: Identifier


@dataclass(frozen=True, slots=True)
class ExportResult[T]:
    """Logical export content before physical serialization."""

    request_identity: Identifier
    content: T
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_metadata(self.metadata)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class ImportFormatAdapter(Protocol):
    """Translate a physical input representation into a logical payload."""

    @property
    def format_name(self) -> str:
        """Return the stable name of the physical format."""
        ...

    def deserialize(self, content: bytes) -> object:
        """Parse bytes into a logical payload without executing business logic."""
        ...


class ExportFormatAdapter(Protocol):
    """Translate a logical export result into a physical representation."""

    @property
    def format_name(self) -> str:
        """Return the stable name of the physical format."""
        ...

    def serialize(self, result: ExportResult[object]) -> bytes:
        """Serialize a logical export result into bytes."""
        ...


@dataclass(frozen=True, slots=True)
class JsonImportFormatAdapter:
    """Minimal UTF-8 JSON import adapter."""

    @property
    def format_name(self) -> str:
        return "json"

    def deserialize(self, content: bytes) -> object:
        if not isinstance(content, bytes):
            raise TypeError("JSON import content must be bytes.")
        try:
            text = content.decode("utf-8")
            return json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise IntegrationMalformedRequestError(
                "Import content is not valid UTF-8 JSON."
            ) from exc


@dataclass(frozen=True, slots=True)
class JsonExportFormatAdapter:
    """Minimal UTF-8 JSON export adapter for JSON-compatible platform values."""

    @property
    def format_name(self) -> str:
        return "json"

    def serialize(self, result: ExportResult[object]) -> bytes:
        if not isinstance(result, ExportResult):
            raise TypeError("JSON export requires an ExportResult.")
        document = {
            "request_identity": str(result.request_identity),
            "content": _to_json_compatible(result.content),
            "metadata": dict(result.metadata),
        }
        return json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")


class ImportExportService(Protocol):
    """Execute registered import/export operations independently of file format."""

    def execute_import[P, R](self, request: ImportRequest[P]) -> ImportResult[R]:
        """Validate and execute an import request."""
        ...

    def execute_export[P, R](self, request: ExportRequest[P]) -> ExportResult[R]:
        """Validate and execute an export request."""
        ...


class DefaultImportExportService:
    """Resolve import/export contracts and invoke their existing operation bindings."""

    def __init__(self, registry: IntegrationOperationRegistry) -> None:
        self._registry = registry

    def execute_import[P, R](self, request: ImportRequest[P]) -> ImportResult[R]:
        self._validate_request(
            request.contract,
            request.request_identity,
            request.security_context,
            IntegrationContractKind.IMPORT,
        )
        operation = self._registry.resolve(request.contract)
        contract = self._validate_resolved_contract(operation.contract, request.contract, "import")
        self._validate_payload(contract, request.payload, "import")
        result = operation.binding.execute(request)
        if isinstance(result, ImportResult):
            if result.request_identity != request.request_identity:
                raise IntegrationContractValidationError(
                    "Import result request identity does not match the originating request."
                )
            return cast(ImportResult[R], result)
        return ImportResult(request_identity=request.request_identity, result=cast(R, result))

    def execute_export[P, R](self, request: ExportRequest[P]) -> ExportResult[R]:
        self._validate_request(
            request.contract,
            request.request_identity,
            request.security_context,
            IntegrationContractKind.EXPORT,
        )
        operation = self._registry.resolve(request.contract)
        contract = self._validate_resolved_contract(operation.contract, request.contract, "export")
        self._validate_payload(contract, request.payload, "export")
        result = operation.binding.execute(request)
        if isinstance(result, ExportResult):
            if result.request_identity != request.request_identity:
                raise IntegrationContractValidationError(
                    "Export result request identity does not match the originating request."
                )
            return result
        return ExportResult(request_identity=request.request_identity, content=cast(R, result))

    @staticmethod
    def _validate_request(
        contract_identity: IntegrationContractIdentity,
        request_identity: Identifier,
        security_context: SecurityContext,
        expected_kind: IntegrationContractKind,
    ) -> None:
        if not isinstance(contract_identity, IntegrationContractIdentity):
            raise IntegrationRequestValidationError("Request has an invalid contract identity.")
        if contract_identity.kind is not expected_kind:
            raise IntegrationRequestValidationError(
                f"Expected an {expected_kind.value} contract, got {contract_identity.kind.value}."
            )
        if not isinstance(request_identity, Identifier):
            raise IntegrationRequestValidationError("Request identity must be an Identifier.")
        if not isinstance(security_context, SecurityContext):
            raise IntegrationRequestValidationError("Request must include a SecurityContext.")

    @staticmethod
    def _validate_payload(
        contract: ImportContract | ExportContract, payload: object, label: str
    ) -> None:
        try:
            contract.validate(payload)
        except (TypeError, ValueError) as exc:
            raise IntegrationContractValidationError(
                f"{label.capitalize()} payload failed contract validation."
            ) from exc

    @staticmethod
    def _validate_resolved_contract(
        contract: IntegrationContract,
        requested_identity: IntegrationContractIdentity,
        label: str,
    ) -> ImportContract | ExportContract:
        if contract.identity != requested_identity:
            raise IntegrationContractValidationError(
                "Resolved Integration operation does not match the requested contract identity."
            )
        if not callable(getattr(contract, "validate", None)):
            raise IntegrationContractValidationError(
                f"Resolved {label} contract must provide validate(payload)."
            )
        if contract.identity.kind not in {
            IntegrationContractKind.IMPORT,
            IntegrationContractKind.EXPORT,
        }:
            raise IntegrationContractValidationError(
                f"Resolved contract is not an {label} contract."
            )
        return cast(ImportContract | ExportContract, contract)


def _validate_metadata(metadata: Mapping[str, str]) -> None:
    if not isinstance(metadata, Mapping):
        raise TypeError("Result metadata must be a mapping of strings to strings.")
    if any(
        not isinstance(key, str) or not isinstance(value, str) for key, value in metadata.items()
    ):
        raise TypeError("Result metadata keys and values must be strings.")


def _to_json_compatible(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Identifier):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Enum):
        return _to_json_compatible(value.value)
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("JSON export mappings must have string keys.")
        return {key: _to_json_compatible(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_to_json_compatible(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _to_json_compatible(getattr(value, item.name)) for item in fields(value)}
    raise TypeError(f"Value of type {type(value).__name__} is not supported by JSON export.")
