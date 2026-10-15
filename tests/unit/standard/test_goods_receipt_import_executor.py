from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from types import SimpleNamespace
from typing import cast

import pytest

from accore.platform.foundation import Identifier
from accore.platform.object import ObjectInstance
from accore.platform.posting import PostingResult
from accore.platform.security import (
    AuthorizationDecision,
    AuthorizationDeniedError,
    AuthorizationDenyReason,
    AuthorizationOutcome,
    AuthorizationRequest,
    SecurityContext,
    SecurityOperation,
)
from standard.integration import (
    GOODS_RECEIPT_DOCUMENT,
    DefaultStandardGoodsReceiptImportExecutor,
    StandardGoodsReceiptImportLine,
    StandardGoodsReceiptImportOutcome,
    StandardGoodsReceiptImportPayload,
)


@dataclass
class FakeAuthorization:
    deny_operation: SecurityOperation | None = None
    requests: list[AuthorizationRequest] = field(default_factory=list)

    def require(self, request: AuthorizationRequest) -> None:
        self.requests.append(request)
        if request.operation is self.deny_operation:
            raise AuthorizationDeniedError(
                AuthorizationDecision(
                    outcome=AuthorizationOutcome.DENY,
                    reason=AuthorizationDenyReason.MISSING_PERMISSION,
                )
            )

    def authorize(self, request: AuthorizationRequest) -> object:
        raise NotImplementedError


@dataclass
class FakeGateway:
    document: ObjectInstance
    error: Exception | None = None
    calls: list[tuple[StandardGoodsReceiptImportPayload, Identifier]] = field(default_factory=list)

    def create_draft(
        self, payload: StandardGoodsReceiptImportPayload, request_identity: Identifier
    ) -> ObjectInstance:
        self.calls.append((payload, request_identity))
        if self.error is not None:
            raise self.error
        return self.document


@dataclass
class FakePostingAPI:
    result: PostingResult
    error: Exception | None = None
    calls: list[ObjectInstance] = field(default_factory=list)

    def post(self, document: ObjectInstance) -> PostingResult:
        self.calls.append(document)
        if self.error is not None:
            raise self.error
        return self.result

    def unpost(self, document: ObjectInstance) -> PostingResult:
        raise NotImplementedError

    def repost(self, document: ObjectInstance) -> PostingResult:
        raise NotImplementedError

    def recover(self, operation_identity: object) -> PostingResult:
        raise NotImplementedError


def make_fixture(
    *,
    deny_operation: SecurityOperation | None = None,
    gateway_error: Exception | None = None,
    posting_result: PostingResult | None = None,
) -> tuple[
    DefaultStandardGoodsReceiptImportExecutor,
    FakeAuthorization,
    FakeGateway,
    FakePostingAPI,
    StandardGoodsReceiptImportPayload,
    SecurityContext,
    Identifier,
    ObjectInstance,
]:
    document_identity = Identifier.new()
    document = cast(ObjectInstance, SimpleNamespace(identity=document_identity))
    authorization = FakeAuthorization(deny_operation=deny_operation)
    gateway = FakeGateway(document=document, error=gateway_error)
    posting = FakePostingAPI(result=posting_result or PostingResult.success())
    executor = DefaultStandardGoodsReceiptImportExecutor(
        authorization=authorization,  # type: ignore[arg-type]
        document_gateway=gateway,
        posting_api=posting,
    )
    payload = StandardGoodsReceiptImportPayload(
        lines=(StandardGoodsReceiptImportLine("product-1", "warehouse-1", Decimal(2)),)
    )
    context = SecurityContext(principal=None, session=None)
    request_identity = Identifier.new()
    return executor, authorization, gateway, posting, payload, context, request_identity, document


def test_import_denial_prevents_gateway_and_posting() -> None:
    executor, authorization, gateway, posting, payload, context, request_id, _ = make_fixture(
        deny_operation=SecurityOperation.IMPORT
    )

    with pytest.raises(AuthorizationDeniedError):
        executor.execute(payload, context, request_id)

    assert [request.operation for request in authorization.requests] == [SecurityOperation.IMPORT]
    assert gateway.calls == []
    assert posting.calls == []


def test_post_denial_prevents_gateway_and_posting() -> None:
    executor, authorization, gateway, posting, payload, context, request_id, _ = make_fixture(
        deny_operation=SecurityOperation.POST
    )

    with pytest.raises(AuthorizationDeniedError):
        executor.execute(payload, context, request_id)

    assert [request.operation for request in authorization.requests] == [
        SecurityOperation.IMPORT,
        SecurityOperation.POST,
    ]
    assert gateway.calls == []
    assert posting.calls == []


def test_authorization_targets_goods_receipt_document_in_order() -> None:
    executor, authorization, _, _, payload, context, request_id, _ = make_fixture()

    executor.execute(payload, context, request_id)

    assert [(request.target, request.operation) for request in authorization.requests] == [
        (GOODS_RECEIPT_DOCUMENT, SecurityOperation.IMPORT),
        (GOODS_RECEIPT_DOCUMENT, SecurityOperation.POST),
    ]
    assert all(request.context is context for request in authorization.requests)


def test_gateway_error_does_not_call_posting() -> None:
    executor, _, gateway, posting, payload, context, request_id, _ = make_fixture(
        gateway_error=RuntimeError("persistence unavailable")
    )

    with pytest.raises(RuntimeError, match="persistence unavailable"):
        executor.execute(payload, context, request_id)

    assert len(gateway.calls) == 1
    assert posting.calls == []


@pytest.mark.parametrize(
    ("posting_result", "expected_outcome", "expected_error"),
    [
        (PostingResult.success(), StandardGoodsReceiptImportOutcome.POSTED, None),
        (
            PostingResult.failure(RuntimeError("internal details")),
            StandardGoodsReceiptImportOutcome.POSTING_FAILED,
            "posting_failed",
        ),
        (
            PostingResult.indeterminate(RuntimeError("internal details")),
            StandardGoodsReceiptImportOutcome.POSTING_INDETERMINATE,
            "posting_indeterminate",
        ),
    ],
)
def test_posting_result_maps_to_stable_outcome_without_retry(
    posting_result: PostingResult,
    expected_outcome: StandardGoodsReceiptImportOutcome,
    expected_error: str | None,
) -> None:
    executor, _, gateway, posting, payload, context, request_id, document = make_fixture(
        posting_result=posting_result
    )

    result = executor.execute(payload, context, request_id)

    assert result.request_identity is request_id
    assert result.document_identity == document.identity
    assert result.outcome is expected_outcome
    assert result.error_code == expected_error
    assert len(gateway.calls) == 1
    assert posting.calls == [document]


def test_unexpected_posting_exception_is_not_retried() -> None:
    executor, _, gateway, posting, payload, context, request_id, _ = make_fixture()
    posting.error = RuntimeError("unexpected posting exception")

    with pytest.raises(RuntimeError, match="unexpected posting exception"):
        executor.execute(payload, context, request_id)

    assert len(gateway.calls) == 1
    assert len(posting.calls) == 1


def test_result_enforces_error_code_invariants() -> None:
    from standard.integration import StandardGoodsReceiptImportResult

    request_id = Identifier.new()
    document_id = Identifier.new()
    with pytest.raises(ValueError):
        StandardGoodsReceiptImportResult(
            request_identity=request_id,
            document_identity=document_id,
            outcome=StandardGoodsReceiptImportOutcome.POSTED,
            error_code="should-not-be-present",
        )
    with pytest.raises(ValueError):
        StandardGoodsReceiptImportResult(
            request_identity=request_id,
            document_identity=document_id,
            outcome=StandardGoodsReceiptImportOutcome.POSTING_FAILED,
        )
