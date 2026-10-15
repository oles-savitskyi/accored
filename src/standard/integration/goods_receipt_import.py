"""Standard Goods Receipt import orchestration over Security and Posting."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from accore.platform.foundation import Identifier
from accore.platform.object import ObjectInstance
from accore.platform.posting import PostingAPI
from accore.platform.security import (
    AuthorizationRequest,
    AuthorizationService,
    SecurityContext,
    SecurityOperation,
)
from standard.security.definitions import GOODS_RECEIPT_DOCUMENT

from .definitions import StandardGoodsReceiptImportPayload


class GoodsReceiptDocumentGateway(Protocol):
    """Host-supplied port for creating and durably persisting a draft receipt."""

    def create_draft(
        self,
        payload: StandardGoodsReceiptImportPayload,
        request_identity: Identifier,
    ) -> ObjectInstance:
        """Persist the initial document state before returning the instance."""
        ...


class StandardGoodsReceiptImportOutcome(StrEnum):
    POSTED = "posted"
    POSTING_FAILED = "posting_failed"
    POSTING_INDETERMINATE = "posting_indeterminate"


@dataclass(frozen=True, slots=True)
class StandardGoodsReceiptImportResult:
    """Stable result of the import-and-post orchestration."""

    request_identity: Identifier
    document_identity: Identifier
    outcome: StandardGoodsReceiptImportOutcome
    error_code: str | None = None

    def __post_init__(self) -> None:
        if self.outcome is StandardGoodsReceiptImportOutcome.POSTED:
            if self.error_code is not None:
                raise ValueError("A posted Goods Receipt result must not have an error code.")
        elif not isinstance(self.error_code, str) or not self.error_code.strip():
            raise ValueError("A non-successful Goods Receipt result requires an error code.")


class DefaultStandardGoodsReceiptImportExecutor:
    """Authorize, persist a draft, and invoke Posting exactly once."""

    def __init__(
        self,
        *,
        authorization: AuthorizationService,
        document_gateway: GoodsReceiptDocumentGateway,
        posting_api: PostingAPI,
    ) -> None:
        self._authorization = authorization
        self._document_gateway = document_gateway
        self._posting_api = posting_api

    def execute(
        self,
        payload: StandardGoodsReceiptImportPayload,
        security_context: SecurityContext,
        request_identity: Identifier,
    ) -> StandardGoodsReceiptImportResult:
        if not isinstance(payload, StandardGoodsReceiptImportPayload):
            raise TypeError("Goods Receipt import payload has an unsupported type.")
        if not isinstance(security_context, SecurityContext):
            raise TypeError("Goods Receipt import requires a SecurityContext.")
        if not isinstance(request_identity, Identifier):
            raise TypeError("Goods Receipt import request identity must be an Identifier.")

        self._authorization.require(
            AuthorizationRequest(
                context=security_context,
                target=GOODS_RECEIPT_DOCUMENT,
                operation=SecurityOperation.IMPORT,
            )
        )
        self._authorization.require(
            AuthorizationRequest(
                context=security_context,
                target=GOODS_RECEIPT_DOCUMENT,
                operation=SecurityOperation.POST,
            )
        )

        document = self._document_gateway.create_draft(payload, request_identity)
        posting_result = self._posting_api.post(document)
        if posting_result.is_success:
            outcome = StandardGoodsReceiptImportOutcome.POSTED
            error_code = None
        elif posting_result.is_failure:
            outcome = StandardGoodsReceiptImportOutcome.POSTING_FAILED
            error_code = "posting_failed"
        elif posting_result.is_indeterminate:
            outcome = StandardGoodsReceiptImportOutcome.POSTING_INDETERMINATE
            error_code = "posting_indeterminate"
        else:
            # Defensive guard if a non-conforming Posting implementation is injected.
            raise TypeError("Posting API returned an unsupported result outcome.")

        return StandardGoodsReceiptImportResult(
            request_identity=request_identity,
            document_identity=document.identity,
            outcome=outcome,
            error_code=error_code,
        )


__all__ = [
    "GOODS_RECEIPT_DOCUMENT",
    "DefaultStandardGoodsReceiptImportExecutor",
    "GoodsReceiptDocumentGateway",
    "StandardGoodsReceiptImportOutcome",
    "StandardGoodsReceiptImportResult",
]
