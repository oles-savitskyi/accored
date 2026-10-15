from __future__ import annotations

import json
from dataclasses import dataclass
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from accore.platform.foundation import Identifier
from accore.platform.integration import (
    BoundIntegrationOperation,
    ContractVersion,
    DefaultImportExportService,
    DefaultIntegrationService,
    InMemoryIntegrationOperationRegistry,
    IntegrationContractIdentity,
    IntegrationContractKind,
    JsonHttpIntegrationAdapter,
)
from accore.platform.security import SecurityContext


@dataclass(frozen=True)
class Contract:
    identity: IntegrationContractIdentity
    description: str = "Test command"


class Binding:
    def __init__(self) -> None:
        self.request = None

    def execute(self, request: object) -> object:
        self.request = request
        return {"accepted": request.payload, "principal": request.security_context.principal}


@pytest.fixture
def http_service():
    identity = IntegrationContractIdentity(
        "test", "echo", ContractVersion(1, 0), IntegrationContractKind.COMMAND
    )
    binding = Binding()
    registry = InMemoryIntegrationOperationRegistry()
    registry.register(BoundIntegrationOperation(Contract(identity), binding))
    service = DefaultIntegrationService(registry)
    import_export = DefaultImportExportService(registry)
    trusted_context = SecurityContext(principal=None, session=None)
    adapter = JsonHttpIntegrationAdapter(
        service=service,
        import_export_service=import_export,
        payload_decoders={identity: lambda payload: payload},
        security_context_factory=lambda handler: trusted_context,
    )
    server = adapter.make_server(("127.0.0.1", 0))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, identity, binding, trusted_context
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_adapter_executes_command_and_uses_host_security_context(http_service) -> None:
    server, identity, binding, trusted_context = http_service
    body = {
        "contract": {
            "namespace": identity.namespace,
            "name": identity.name,
            "major": 1,
            "minor": 0,
            "kind": "command",
        },
        "request_identity": str(Identifier.new()),
        "payload": {"value": 42},
        "security_context": {"principal": "untrusted-client-value"},
    }
    request = Request(
        f"http://127.0.0.1:{server.server_port}/v1/commands",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=3) as response:
        result = json.loads(response.read())

    assert result["result"]["accepted"] == {"value": 42}
    assert binding.request.security_context is trusted_context
    assert binding.request.security_context.principal is None


def test_http_adapter_rejects_unknown_route_with_json_error(http_service) -> None:
    server, _, _, _ = http_service
    request = Request(
        f"http://127.0.0.1:{server.server_port}/unknown",
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with pytest.raises(HTTPError) as error:
        urlopen(request, timeout=3)

    assert error.value.code == 404
    assert json.loads(error.value.read()) == {"error": "not_found"}


def test_http_adapter_rejects_invalid_contract_identity(http_service) -> None:
    server, _, _, _ = http_service
    request = Request(
        f"http://127.0.0.1:{server.server_port}/v1/commands",
        data=(
            b'{"contract":{"namespace":"test","name":"echo","major":-1,"minor":0,'
            b'"kind":"command"},"payload":{}}'
        ),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with pytest.raises(HTTPError) as error:
        urlopen(request, timeout=3)

    assert error.value.code == 400
    assert json.loads(error.value.read())["error"] == "validation"


def test_http_adapter_enforces_request_size_limit() -> None:
    identity = IntegrationContractIdentity(
        "test", "echo", ContractVersion(1, 0), IntegrationContractKind.COMMAND
    )
    registry = InMemoryIntegrationOperationRegistry()
    registry.register(BoundIntegrationOperation(Contract(identity), Binding()))
    adapter = JsonHttpIntegrationAdapter(
        service=DefaultIntegrationService(registry),
        import_export_service=DefaultImportExportService(registry),
        payload_decoders={identity: lambda payload: payload},
        security_context_factory=lambda handler: SecurityContext(principal=None, session=None),
        max_request_bytes=8,
    )
    server = adapter.make_server(("127.0.0.1", 0))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = Request(
            f"http://127.0.0.1:{server.server_port}/v1/commands",
            data=b'{"payload":{}}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(HTTPError) as error:
            urlopen(request, timeout=3)
        assert error.value.code == 413
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
