# Phase 12 — Integration
## Slice 8: Standard Goods Receipt Import Execution — Concrete API Design

**Status:** FINAL — APPROVED FOR IMPLEMENTATION
**Architecture:** `PHASE_12_Integration_Slice_8_Architecture_Amendment.md` (approved 2026-10-15)
**Baseline implementation commit:** `b02d6fb feat(integration): add HTTP adapter and standard import export contracts`

---

## 1. Scope

Define the concrete Standard orchestration API that connects the existing Goods Receipt import binding to existing Security and Posting APIs, with a host-supplied gateway for durable document creation.

This design deliberately does not define a generic document runtime or a concrete persistence backend. The executor can be implemented against a protocol and tested in isolation; production availability still requires a compliant gateway from the host.

### In scope

- `GoodsReceiptDocumentGateway` protocol;
- typed import outcome/result;
- executor dependencies and orchestration order;
- explicit Standard `IMPORT`/`POST` permissions for Administrator and Operator;
- conditional operation registration;
- tests for authorization, gateway and Posting outcomes.

### Out of scope

- generic document metadata/runtime;
- concrete persistence implementation not present in the current project;
- changing `PostingAPI` to expose operation identities;
- automatic retry, exactly-once behavior, or automated recovery;
- direct register movement creation by Integration or the executor.

## 2. Existing public API to reuse

The implementation must reuse these current types:

- `StandardGoodsReceiptImportPayload` and `StandardGoodsReceiptImportLine`;
- `SecurityContext`, `AuthorizationService`, `AuthorizationRequest`, `AuthorizationDeniedError`, `SecurityObjectIdentity`, `SecurityOperation`;
- `ObjectInstance`;
- `PostingAPI` and `PostingResult` / `PostingOutcome`;
- `Identifier`;
- `BoundIntegrationOperation`, `IntegrationOperation`, and `STANDARD_GOODS_RECEIPT_IMPORT_CONTRACT`.

No parallel authorization evaluator or posting interface is introduced.

## 3. Contract and identities

Add the following Standard security target in `standard.security.definitions`:

```python
GOODS_RECEIPT_DOCUMENT = SecurityObjectIdentity(
    object_type="document",
    object_code="goods-receipt",
)
```

Add two explicit permissions in `_build_roles()`:

```python
goods_receipt_import = _permission(
    GOODS_RECEIPT_DOCUMENT,
    SecurityOperation.IMPORT,
)
goods_receipt_post = _permission(
    GOODS_RECEIPT_DOCUMENT,
    SecurityOperation.POST,
)
```

Attach both permissions to Standard Administrator and Standard Operator. Do not attach either permission to Standard Auditor. Do not add role-code comparisons in the executor; `AuthorizationService` remains authoritative.

## 4. Gateway port

Add the protocol in `standard.integration.goods_receipt_import` or a similarly focused module:

```python
from typing import Protocol

from accore.platform.foundation import Identifier
from accore.platform.object import ObjectInstance

from .definitions import StandardGoodsReceiptImportPayload


class GoodsReceiptDocumentGateway(Protocol):
    def create_draft(
        self,
        payload: StandardGoodsReceiptImportPayload,
        request_identity: Identifier,
    ) -> ObjectInstance:
        """Create and durably persist a draft receipt before returning."""
        ...
```

### Gateway contract

`create_draft()` must:

1. Create a `RuntimeObjectType`/`ObjectContext`-compatible `ObjectInstance` with the Standard Goods Receipt document type identity expected by the configured Posting handler resolver.
2. Map every validated payload line into the durable `lines` field using `CollectionValue` of `StructuredValue`, with fields `product`, `warehouse`, and `quantity` (`Decimal`).
3. Persist the object and initial durable state before returning.
4. Ensure the configured `DocumentStateProvider` can retrieve that exact state for the returned instance.
5. Use the host's configured persistence/runtime context and raise a documented gateway/application exception if durable creation cannot be confirmed.
6. Never post the document and never create register movements.

A gateway that only returns an in-memory object does not satisfy the contract. Tests may use a fake gateway, but those tests do not prove host persistence readiness.

## 5. Result model

Create a domain outcome enum:

```python
from enum import StrEnum


class StandardGoodsReceiptImportOutcome(StrEnum):
    POSTED = "posted"
    POSTING_FAILED = "posting_failed"
    POSTING_INDETERMINATE = "posting_indeterminate"
```

Create an immutable result:

```python
from dataclasses import dataclass
from accore.platform.foundation import Identifier


@dataclass(frozen=True, slots=True)
class StandardGoodsReceiptImportResult:
    request_identity: Identifier
    document_identity: Identifier
    outcome: StandardGoodsReceiptImportOutcome
    error_code: str | None = None
```

Rules:

- `request_identity` is correlation only; it does not imply deduplication or idempotency.
- `document_identity` is always present for a returned result because a result is only returned after the gateway successfully returns a persisted document.
- `error_code` is a stable, non-sensitive category for `POSTING_FAILED` or `POSTING_INDETERMINATE`; do not put raw exception text into the public result.
- `POSTED` must have `error_code is None`.
- `POSTING_FAILED` and `POSTING_INDETERMINATE` must have a non-empty `error_code`.
- Authorization and gateway failures before a document is returned are raised through the existing application error boundary, not converted to a result that falsely implies a document exists.

Suggested stable codes:
- `posting_failed` for a definite `PostingOutcome.FAILURE`;
- `posting_indeterminate` for `PostingOutcome.INDETERMINATE`.

The implementation may add validation in `__post_init__` to enforce these invariants.

## 6. Executor API and algorithm

Implement a concrete executor in `standard.integration.goods_receipt_import`:

```python
from accore.platform.foundation import Identifier
from accore.platform.posting import PostingAPI
from accore.platform.security import (
    AuthorizationRequest,
    AuthorizationService,
    SecurityContext,
    SecurityObjectIdentity,
    SecurityOperation,
)


class DefaultStandardGoodsReceiptImportExecutor:
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
        ...
```

The method body must follow this order:

1. Validate input types defensively if consistent with existing Standard binding conventions. The contract decoder remains the primary public payload validation boundary.
2. Call `authorization.require()` for `GOODS_RECEIPT_DOCUMENT` + `IMPORT`.
3. Call `authorization.require()` for `GOODS_RECEIPT_DOCUMENT` + `POST`.
4. Call `document_gateway.create_draft(payload, request_identity)`.
5. Call `posting_api.post(document)` exactly once.
6. Map `PostingResult`:
   - `is_success` → `POSTED`, no error code;
   - `is_failure` → `POSTING_FAILED`, `error_code="posting_failed"`;
   - `is_indeterminate` → `POSTING_INDETERMINATE`, `error_code="posting_indeterminate"`.
7. Return the result with request identity and `document.identity`.

Do not catch authorization exceptions and turn them into success/failure domain results. Do not automatically retry `post()`. Do not delete the document on failure or indeterminate outcome. Do not expose `PostingResult.error` text to an external client.

If an unexpected exception escapes `PostingAPI.post()` rather than being represented as a `PostingResult`, do not retry; let the existing application/transport error boundary handle it. The document has already been created, so diagnostics must retain the request identity and document identity through host logs or telemetry where available. Do not pretend this case is safely reconciled.

## 7. Composition

Update `compose_standard_integration()` with an optional keyword-only executor parameter, or retain the current `additional_operations` extension point if it is clearer and less disruptive.

Preferred minimal change:

```python
def compose_standard_integration(
    *,
    processing_runtime: ProcessingRuntime,
    runtime_configuration: RuntimeConfigurationContext,
    report_runtime: ReportRuntime,
    additional_operations: tuple[IntegrationOperation, ...] = (),
    goods_receipt_import_executor: StandardGoodsReceiptImportExecutor | None = None,
) -> StandardIntegrationComposition:
    ...
```

When `goods_receipt_import_executor is None`, do not register `STANDARD_GOODS_RECEIPT_IMPORT_CONTRACT`.

When supplied, register:

```python
BoundIntegrationOperation(
    contract=STANDARD_GOODS_RECEIPT_IMPORT_CONTRACT,
    binding=StandardGoodsReceiptImportBinding(goods_receipt_import_executor),
)
```

The operation is only as deployable as the supplied executor's gateway. Do not install an in-memory or test-only gateway as a default.

Avoid duplicate registration if the same contract is also supplied through `additional_operations`; existing registry conflict behavior should remain authoritative and deterministic. The implementation should document which conflict path is expected rather than silently replacing an existing operation.

## 8. Error and outcome mapping

| Situation | Executor behavior | Public meaning |
|---|---|---|
| Missing principal / inactive user / missing permission | Existing authorization error raised before gateway | Request not authorized |
| Gateway cannot persist draft | Raise documented gateway/application error; no Posting call | Import did not reach posting; document creation status follows gateway contract |
| Posting returns SUCCESS | Return `POSTED` | Document posting succeeded |
| Posting returns FAILURE | Return `POSTING_FAILED`; keep document | Posting failed; reconcile/fix before any deliberate new attempt |
| Posting returns INDETERMINATE | Return `POSTING_INDETERMINATE`; keep document; no retry | Posting state unknown; manual reconciliation required |
| Unexpected exception after gateway returns | No automatic retry; error boundary records correlation and document identity if possible | Outcome may require manual reconciliation |

Transport status codes are not specified in this slice's domain API. The JSON/HTTP adapter must not erase the explicit outcome if it serializes the result.

## 9. Test design

Add focused tests, preferably under `tests/unit/standard/test_goods_receipt_import_executor.py` and update Standard security/composition tests.

### Executor tests

1. Import permission denied → gateway not called; Posting not called.
2. POST permission denied after IMPORT allowed → gateway not called; Posting not called.
3. Gateway raises before returning → Posting not called.
4. Posting success → `POSTED`, correct request/document identities, one gateway call, one Posting call.
5. Posting definite failure → `POSTING_FAILED`, stable error code, document identity retained, no retry.
6. Posting indeterminate → `POSTING_INDETERMINATE`, stable error code, document identity retained, no retry.
7. Authorization requests target the exact `GOODS_RECEIPT_DOCUMENT` and operations IMPORT then POST.
8. `SecurityContext` is used as supplied; payload cannot override principal or request identity.
9. Posting receives the exact `ObjectInstance` returned by gateway.
10. A result never reports `POSTED` for failure/indeterminate `PostingResult`.

### Security tests

1. Administrator has Goods Receipt IMPORT and POST.
2. Operator has Goods Receipt IMPORT and POST.
3. Auditor has neither permission.
4. Existing permissions remain unchanged.

### Composition tests

1. No executor → Goods Receipt import contract is absent from the Standard registry.
2. Executor supplied → contract resolves to `StandardGoodsReceiptImportBinding`.
3. Duplicate contract registration is rejected by existing registry conflict handling.

### Test limitation

Fake gateway tests prove orchestration behavior only. They do not prove that a production host can create and durably persist a valid Goods Receipt or that Posting's `DocumentStateProvider` reads the persisted `lines` state. That requires a separate host-level integration test using the concrete gateway and configured Posting stack.

## 10. Files expected to change

Implementation is expected to touch only these areas unless tests reveal a necessary additional dependency:

- `src/standard/security/definitions.py`
- `src/standard/integration/definitions.py` (only if result/gateway/executor public exports are placed here; prefer a focused module)
- `src/standard/integration/goods_receipt_import.py` (new)
- `src/standard/integration/__init__.py`
- `src/standard/integration/composition.py`
- `src/standard/integration/operations.py` (only if required to keep binding typed/consistent)
- `tests/unit/standard/test_goods_receipt_import_executor.py` (new)
- `tests/unit/standard/test_security_definitions.py` or existing equivalent
- `tests/unit/standard/test_integration_composition.py`
- `docs/implementation/PHASE_12_Integration_Slice_8_Architecture_Amendment.md`
- `docs/implementation/PHASE_12_Integration_Slice_8_Concrete_API_Design.md`

Do not modify the HTTP adapter unless a test demonstrates a real contract serialization defect.

## 11. Implementation gate

Proceed to code only after this Concrete API Design is reviewed and approved. Once approved, implementation should be delivered as a ZIP containing only new/changed AcCoreD files with full repository-relative paths, no `__pycache__`, and no git patch. The final Phase 12 closure record must remain conditional until a real host gateway passes the durable end-to-end integration test.
