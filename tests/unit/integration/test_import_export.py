from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, dataclass
from decimal import Decimal

import pytest

from accore.platform.foundation.identity import Identifier
from accore.platform.integration import (
    BoundIntegrationOperation,
    ContractVersion,
    DefaultImportExportService,
    ExportRequest,
    ExportResult,
    ImportRequest,
    ImportResult,
    InMemoryIntegrationOperationRegistry,
    IntegrationContractIdentity,
    IntegrationContractKind,
    IntegrationContractValidationError,
    IntegrationMalformedRequestError,
    IntegrationRequestValidationError,
    JsonExportFormatAdapter,
    JsonImportFormatAdapter,
)
from accore.platform.security.context import SecurityContext


@dataclass(frozen=True, slots=True)
class ExampleImportContract:
    identity: IntegrationContractIdentity
    description: str = "Import test payload"

    def validate(self, payload: object) -> None:
        if not isinstance(payload, dict) or "name" not in payload:
            raise ValueError("payload requires a name")


@dataclass(frozen=True, slots=True)
class ExampleExportContract:
    identity: IntegrationContractIdentity
    description: str = "Export test payload"

    def validate(self, payload: object) -> None:
        if not isinstance(payload, dict) or "selection" not in payload:
            raise ValueError("payload requires a selection")


class ExampleBinding:
    def __init__(self, result: object = None) -> None:
        self.result = result
        self.received_request: object | None = None
        self.calls = 0

    def execute(self, request: object) -> object:
        self.calls += 1
        self.received_request = request
        return self.result


def make_identity(kind: IntegrationContractKind) -> IntegrationContractIdentity:
    return IntegrationContractIdentity(
        namespace="tests",
        name="example",
        version=ContractVersion(1, 0),
        kind=kind,
    )


def make_service(
    kind: IntegrationContractKind,
    binding: ExampleBinding,
) -> DefaultImportExportService:
    registry = InMemoryIntegrationOperationRegistry()
    contract = (
        ExampleImportContract(make_identity(kind))
        if kind is IntegrationContractKind.IMPORT
        else ExampleExportContract(make_identity(kind))
    )
    registry.register(
        BoundIntegrationOperation(contract=contract, binding=binding)  # type: ignore[arg-type]
    )
    return DefaultImportExportService(registry)


def make_request_identity() -> Identifier:
    return Identifier.new()


def make_security_context() -> SecurityContext:
    return SecurityContext(principal=None, session=None)


def test_import_request_validates_contract_and_binding_receives_request() -> None:
    binding = ExampleBinding(result={"imported": 2})
    service = make_service(IntegrationContractKind.IMPORT, binding)
    request = ImportRequest(
        contract=make_identity(IntegrationContractKind.IMPORT),
        payload={"name": "sample"},
        security_context=make_security_context(),
        request_identity=make_request_identity(),
    )

    result = service.execute_import(request)

    assert result == ImportResult(request.request_identity, {"imported": 2})
    assert binding.received_request is request
    assert binding.calls == 1


def test_import_rejects_wrong_contract_kind_before_binding() -> None:
    binding = ExampleBinding()
    service = make_service(IntegrationContractKind.EXPORT, binding)
    request = ImportRequest(
        contract=make_identity(IntegrationContractKind.EXPORT),
        payload={"name": "sample"},
        security_context=make_security_context(),
        request_identity=make_request_identity(),
    )

    with pytest.raises(IntegrationRequestValidationError, match="Expected an import"):
        service.execute_import(request)  # type: ignore[arg-type]
    assert binding.calls == 0


def test_import_preserves_explicit_result_metadata() -> None:
    request_identity = make_request_identity()
    import_result = ImportResult(request_identity, {"accepted": 1}, {"source": "json"})
    binding = ExampleBinding(result=import_result)
    service = make_service(IntegrationContractKind.IMPORT, binding)
    request = ImportRequest(
        contract=make_identity(IntegrationContractKind.IMPORT),
        payload={"name": "sample"},
        security_context=make_security_context(),
        request_identity=request_identity,
    )

    result = service.execute_import(request)

    assert result is import_result
    assert result.metadata == {"source": "json"}


def test_import_rejects_result_correlated_to_another_request() -> None:
    binding = ExampleBinding(result=ImportResult(make_request_identity(), {"accepted": 1}))
    service = make_service(IntegrationContractKind.IMPORT, binding)
    request = ImportRequest(
        contract=make_identity(IntegrationContractKind.IMPORT),
        payload={"name": "sample"},
        security_context=make_security_context(),
        request_identity=make_request_identity(),
    )

    with pytest.raises(IntegrationContractValidationError, match="does not match"):
        service.execute_import(request)


def test_import_contract_validation_precedes_binding() -> None:
    binding = ExampleBinding()
    service = make_service(IntegrationContractKind.IMPORT, binding)
    request = ImportRequest(
        contract=make_identity(IntegrationContractKind.IMPORT),
        payload={"missing": "name"},
        security_context=make_security_context(),
        request_identity=make_request_identity(),
    )

    with pytest.raises(IntegrationContractValidationError, match="failed contract validation"):
        service.execute_import(request)
    assert binding.calls == 0


def test_export_returns_typed_result_and_preserves_request_identity() -> None:
    binding = ExampleBinding(result={"rows": [{"sku": "A-1"}]})
    service = make_service(IntegrationContractKind.EXPORT, binding)
    request = ExportRequest(
        contract=make_identity(IntegrationContractKind.EXPORT),
        payload={"selection": "inventory"},
        security_context=make_security_context(),
        request_identity=make_request_identity(),
    )

    result = service.execute_export(request)

    assert result == ExportResult(request.request_identity, {"rows": [{"sku": "A-1"}]})
    assert binding.received_request is request
    assert binding.calls == 1


def test_export_preserves_explicit_result_metadata() -> None:
    request_identity = make_request_identity()
    export_result = ExportResult(
        request_identity,
        {"rows": []},
        {"count": "0"},
    )
    binding = ExampleBinding(result=export_result)
    service = make_service(IntegrationContractKind.EXPORT, binding)
    request = ExportRequest(
        contract=make_identity(IntegrationContractKind.EXPORT),
        payload={"selection": "inventory"},
        security_context=make_security_context(),
        request_identity=request_identity,
    )

    result = service.execute_export(request)

    assert result.metadata == {"count": "0"}
    with pytest.raises(TypeError):
        result.metadata["count"] = "1"  # type: ignore[index]


def test_export_rejects_result_correlated_to_another_request() -> None:
    binding = ExampleBinding(result=ExportResult(make_request_identity(), {"rows": []}))
    service = make_service(IntegrationContractKind.EXPORT, binding)
    request = ExportRequest(
        contract=make_identity(IntegrationContractKind.EXPORT),
        payload={"selection": "inventory"},
        security_context=make_security_context(),
        request_identity=make_request_identity(),
    )

    with pytest.raises(IntegrationContractValidationError, match="does not match"):
        service.execute_export(request)


def test_result_metadata_is_defensively_copied_and_immutable() -> None:
    metadata = {"source": "unit-test"}
    result = ImportResult(make_request_identity(), "ok", metadata)
    metadata["source"] = "mutated"

    assert result.metadata["source"] == "unit-test"
    with pytest.raises(TypeError):
        result.metadata["new"] = "value"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        result.result = "changed"  # type: ignore[misc]


def test_result_metadata_requires_string_keys_and_values() -> None:
    with pytest.raises(TypeError, match="strings"):
        ExportResult(make_request_identity(), "ok", {"count": 1})  # type: ignore[dict-item]


def test_json_import_deserializes_utf8_json() -> None:
    adapter = JsonImportFormatAdapter()

    assert adapter.format_name == "json"
    assert adapter.deserialize('{"name":"Продукт","active":true}'.encode()) == {
        "name": "Продукт",
        "active": True,
    }


@pytest.mark.parametrize("content", [b"{bad json", b"\xff\xfe"])
def test_json_import_rejects_malformed_input(content: bytes) -> None:
    with pytest.raises(IntegrationMalformedRequestError, match="UTF-8 JSON"):
        JsonImportFormatAdapter().deserialize(content)


def test_json_import_rejects_non_bytes() -> None:
    with pytest.raises(TypeError, match="must be bytes"):
        JsonImportFormatAdapter().deserialize("{}")  # type: ignore[arg-type]


def test_json_export_serializes_result_envelope_deterministically() -> None:
    adapter = JsonExportFormatAdapter()
    request_identity = make_request_identity()
    result = ExportResult(
        request_identity=request_identity,
        content={"amount": Decimal("12.50"), "items": ["A", "B"]},
        metadata={"format": "json"},
    )

    serialized = adapter.serialize(result)

    assert json.loads(serialized) == {
        "request_identity": str(request_identity),
        "content": {"amount": "12.50", "items": ["A", "B"]},
        "metadata": {"format": "json"},
    }
    assert serialized == adapter.serialize(result)


def test_json_export_rejects_unsupported_values() -> None:
    result = ExportResult(make_request_identity(), object())

    with pytest.raises(TypeError, match="not supported"):
        JsonExportFormatAdapter().serialize(result)


def test_json_export_requires_export_result() -> None:
    with pytest.raises(TypeError, match="ExportResult"):
        JsonExportFormatAdapter().serialize({"content": []})  # type: ignore[arg-type]
