"""Small JSON/HTTP adapter for the protocol-independent Integration services.

Authentication is deliberately delegated to the hosting application through
``security_context_factory``. The request body is never trusted to establish an
identity or a SecurityContext.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import fields, is_dataclass
from decimal import Decimal
from enum import Enum
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from accore.platform.foundation import Identifier
from accore.platform.security import SecurityContext

from .contract import ContractVersion, IntegrationContractIdentity, IntegrationContractKind
from .errors import (
    IntegrationAuthenticationError,
    IntegrationAuthorizationError,
    IntegrationContractNotFoundError,
    IntegrationContractVersionError,
    IntegrationError,
    IntegrationMalformedRequestError,
    IntegrationRequestValidationError,
)
from .import_export import (
    ExportRequest,
    ImportRequest,
    JsonExportFormatAdapter,
)
from .service import IntegrationService

PayloadDecoder = Callable[[object], object]
SecurityContextFactory = Callable[[BaseHTTPRequestHandler], SecurityContext]


class JsonHttpIntegrationAdapter:
    """Create a standard-library HTTP handler for Integration operations.

    The adapter intentionally exposes only four POST endpoints:
    ``/v1/commands``, ``/v1/queries``, ``/v1/imports`` and ``/v1/exports``.
    Payload decoders are keyed by the complete contract identity, so wire JSON
    cannot select an arbitrary Python type.
    """

    def __init__(
        self,
        *,
        service: IntegrationService,
        import_export_service: object,
        payload_decoders: Mapping[IntegrationContractIdentity, PayloadDecoder],
        security_context_factory: SecurityContextFactory,
        max_request_bytes: int = 1_048_576,
    ) -> None:
        if max_request_bytes <= 0:
            raise ValueError("max_request_bytes must be positive.")
        self._service = service
        self._import_export_service = import_export_service
        self._payload_decoders = dict(payload_decoders)
        self._security_context_factory = security_context_factory
        self._max_request_bytes = max_request_bytes

    def handler_class(self) -> type[BaseHTTPRequestHandler]:
        """Return a handler class bound to this adapter instance."""
        adapter = self

        class IntegrationRequestHandler(BaseHTTPRequestHandler):
            server_version = "AcCoreD-Integration/1"
            sys_version = ""

            def do_POST(self) -> None:
                adapter._handle_post(self)

            def do_GET(self) -> None:
                adapter._write_json(
                    self, HTTPStatus.METHOD_NOT_ALLOWED, {"error": "method_not_allowed"}
                )

            def log_message(self, format: str, *args: object) -> None:
                # The host controls application logging; avoid leaking request data.
                del format, args

        return IntegrationRequestHandler

    def make_server(self, address: tuple[str, int]) -> ThreadingHTTPServer:
        """Create, but do not start, a server using this adapter."""
        return ThreadingHTTPServer(address, self.handler_class())

    def _handle_post(self, handler: BaseHTTPRequestHandler) -> None:
        path = urlsplit(handler.path).path
        if path not in {"/v1/commands", "/v1/queries", "/v1/imports", "/v1/exports"}:
            self._write_json(handler, HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return
        content_type = handler.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            self._write_json(
                handler,
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                {"error": "unsupported_media_type"},
            )
            return
        raw_length = handler.headers.get("Content-Length")
        try:
            length = int(raw_length or "")
        except ValueError:
            self._write_json(handler, HTTPStatus.BAD_REQUEST, {"error": "invalid_content_length"})
            return
        if length < 0:
            self._write_json(handler, HTTPStatus.BAD_REQUEST, {"error": "invalid_content_length"})
            return
        if length > self._max_request_bytes:
            self._write_json(
                handler, HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "request_too_large"}
            )
            return
        try:
            body = json.loads(handler.rfile.read(length).decode("utf-8"))
            envelope = self._validate_envelope(body)
            security_context = self._security_context_factory(handler)
            if not isinstance(security_context, SecurityContext):
                raise IntegrationAuthenticationError(
                    "The host did not establish a SecurityContext."
                )
            identity, request_identity, payload = envelope
            decoder = self._payload_decoders.get(identity)
            if decoder is None:
                raise IntegrationContractNotFoundError(
                    "No payload decoder is registered for this contract."
                )
            logical_payload = decoder(payload)
            if path == "/v1/commands":
                from .request import CommandRequest

                command_result: object = self._service.execute_command(
                    CommandRequest(identity, logical_payload, security_context, request_identity)
                )
                self._write_json(handler, HTTPStatus.OK, _json_value(command_result))
                return
            if path == "/v1/queries":
                from .request import QueryRequest

                query_result: object = self._service.execute_query(
                    QueryRequest(identity, logical_payload, security_context, request_identity)
                )
                self._write_json(handler, HTTPStatus.OK, _json_value(query_result))
                return
            if path == "/v1/imports":
                import_request = ImportRequest(
                    identity, logical_payload, security_context, request_identity
                )
                import_result: object = self._import_export_service.execute_import(  # type: ignore[attr-defined]
                    import_request
                )
                self._write_json(handler, HTTPStatus.OK, _json_value(import_result))
                return
            export_request = ExportRequest(
                identity, logical_payload, security_context, request_identity
            )
            export_result = self._import_export_service.execute_export(  # type: ignore[attr-defined]
                export_request
            )
            encoded = JsonExportFormatAdapter().serialize(export_result)
            self._write_bytes(handler, HTTPStatus.OK, encoded)
        except IntegrationError as exc:
            status = _status_for_error(exc)
            self._write_json(handler, status, {"error": exc.category.value, "message": str(exc)})
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            IntegrationRequestValidationError,
            TypeError,
            ValueError,
        ):
            self._write_json(
                handler,
                HTTPStatus.BAD_REQUEST,
                {"error": "validation", "message": "Invalid Integration request."},
            )
        except Exception:  # noqa: BLE001 — keep unexpected details behind the HTTP boundary.
            # Unexpected exception details must not cross the transport boundary.
            self._write_json(
                handler,
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "internal", "message": "An internal Integration error occurred."},
            )

    def _validate_envelope(
        self, body: object
    ) -> tuple[IntegrationContractIdentity, Identifier, object]:
        if not isinstance(body, dict):
            raise IntegrationMalformedRequestError("Request body must be a JSON object.")
        contract = body.get("contract")
        if not isinstance(contract, dict):
            raise IntegrationMalformedRequestError("Request must include a contract object.")
        try:
            identity = IntegrationContractIdentity(
                namespace=_required_string(contract, "namespace"),
                name=_required_string(contract, "name"),
                version=ContractVersion(
                    _non_negative_int(contract, "major"),
                    _non_negative_int(contract, "minor"),
                ),
                kind=IntegrationContractKind(_required_string(contract, "kind")),
            )
            request_identity_value = body.get("request_identity")
            request_identity = (
                Identifier.from_str(request_identity_value)
                if request_identity_value is not None
                else Identifier.new()
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise IntegrationMalformedRequestError(
                "Request contract identity or request_identity is invalid."
            ) from exc
        if "payload" not in body:
            raise IntegrationMalformedRequestError("Request must include payload.")
        return identity, request_identity, body["payload"]

    @staticmethod
    def _write_json(handler: BaseHTTPRequestHandler, status: HTTPStatus, payload: object) -> None:
        body = json.dumps(
            _json_value(payload),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        JsonHttpIntegrationAdapter._write_bytes(handler, status, body)

    @staticmethod
    def _write_bytes(handler: BaseHTTPRequestHandler, status: HTTPStatus, body: bytes) -> None:
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.send_header("Cache-Control", "no-store")
        handler.end_headers()
        handler.wfile.write(body)


def _required_string(payload: Mapping[str, object], name: str) -> str:
    value = payload.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value


def _non_negative_int(payload: Mapping[str, object], name: str) -> int:
    value = payload.get(name)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer.")
    return value


def _status_for_error(error: IntegrationError) -> HTTPStatus:
    if isinstance(error, IntegrationAuthenticationError):
        return HTTPStatus.UNAUTHORIZED
    if isinstance(error, IntegrationAuthorizationError):
        return HTTPStatus.FORBIDDEN
    if isinstance(error, IntegrationContractNotFoundError):
        return HTTPStatus.NOT_FOUND
    if isinstance(error, IntegrationContractVersionError):
        return HTTPStatus.CONFLICT
    if error.category.value == "validation":
        return HTTPStatus.BAD_REQUEST
    if error.category.value == "conflict":
        return HTTPStatus.CONFLICT
    return HTTPStatus.INTERNAL_SERVER_ERROR


def _json_value(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Identifier):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return _json_value(value.value)
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("JSON object keys must be strings.")
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_value(getattr(value, field.name)) for field in fields(value)}
    raise TypeError(f"Value of type {type(value).__name__} is not JSON serializable.")


__all__ = ["JsonHttpIntegrationAdapter", "PayloadDecoder", "SecurityContextFactory"]
