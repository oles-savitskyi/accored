# Phase 12 — Integration
## Slice 8: Standard Goods Receipt Import Execution — Architecture Amendment

**Status:** FINAL — APPROVED FOR CONCRETE API DESIGN
**Baseline implementation commit:** `b02d6fb feat(integration): add HTTP adapter and standard import export contracts`
**Scope:** Standard Goods Receipt Import execution through existing Security and Posting boundaries
**Decision record:** Owner decisions confirmed 2026-10-15

---

## 1. Purpose

Slice 7 introduced the Standard Goods Receipt import contract and binding, but the binding delegates to a host-supplied `StandardGoodsReceiptImportExecutor`. This amendment fixes the minimum safe implementation boundary for that executor. It does not claim that a production-ready document runtime or persistence adapter already exists.

The objective is to implement the orchestration logic without letting Integration own object persistence, bypass authorization, or create register movements directly.

## 2. Confirmed architecture decisions

The project owner approved these decisions:

1. **Document creation boundary:** use a narrow `GoodsReceiptDocumentGateway` supplied by the host. Do not introduce a generic document metadata/runtime subsystem as an incidental Integration change.
2. **Standard MVP permissions:** Standard Administrator and Standard Operator receive explicit Goods Receipt `IMPORT` and `POST` permissions. Standard Auditor receives neither.
3. **Indeterminate posting:** preserve the created document and return `POSTING_INDETERMINATE`; never retry automatically. Do not claim exactly-once behavior or automated recovery.

These decisions are binding for Slice 8 implementation.

## 3. Evidence from the current implementation

The inspected source establishes these boundaries:

- `GoodsReceiptPostingHandler` reads `RuntimeDurableState` through `PostingContext.services.document_state`, validates the `lines` collection, and produces a `MovementSet`.
- `PostingAPI.post(ObjectInstance)` delegates to `PostingEngine`; the engine resolves the handler, validates movements, and delegates posting lifecycle changes to the configured result coordinator.
- `PostingServices` requires a `DocumentStateProvider` capable of returning the durable state for the same `ObjectInstance` being posted.
- `ObjectCreator` creates an `ObjectInstance` from a resolved `RuntimeObjectType` and `ObjectContext`; it does not persist it.
- `ObjectPersistence`, `PersistentObjectMaterializer`, and `PersistentObjectHydrator` define persistence boundaries, but the inspected source archive has no concrete `ObjectPersistence` implementation.
- `RuntimeResolver` resolves `CatalogMetadata` to `CatalogRuntime`; the inspected `MetadataType` defines only `CATALOG`.
- Standard metadata definitions describe catalogs, not a Goods Receipt document type. The posting handler exists, but a Standard document metadata/runtime composition is not present in the inspected source.
- Standard security roles currently define inventory rebuild, inventory balance reporting, and security administration permissions. Explicit Goods Receipt import/post permissions must be added.
- `PostingEngine` creates an internal `PostingOperationIdentity` for each `post()` call and `recover()` accepts an operation identity, but `PostingAPI.post()` returns only `PostingResult`. The executor therefore cannot correlate an indeterminate result to that operation using the current API alone.

These are capability gaps, not reasons to simulate a successful import.

## 4. Responsibility split

```text
Integration ImportRequest
        |
        v
StandardGoodsReceiptImportBinding
        |
        v
StandardGoodsReceiptImportExecutor (Standard application orchestration)
        |-- AuthorizationService (IMPORT and POST checks)
        |-- GoodsReceiptDocumentGateway (create and durably persist draft)
        |-- PostingAPI (post the exact persisted ObjectInstance)
        |
        v
StandardGoodsReceiptImportResult
```

### 4.1 Integration layer

Integration is responsible for contract resolution, request identity propagation, payload validation, and transport-independent invocation. It must not create runtime objects, persist document state, evaluate permissions itself, or write register movements.

### 4.2 Standard executor

The executor orchestrates one import request. It must:

1. Receive the already validated `StandardGoodsReceiptImportPayload`, trusted `SecurityContext`, and request identity.
2. Require `IMPORT` and `POST` authorization before creating a document or causing any business side effect.
3. Call the gateway to create and durably persist a draft Goods Receipt whose `lines` state can be retrieved by the configured `DocumentStateProvider` for the exact returned `ObjectInstance`.
4. Call `PostingAPI.post(document)` on that exact instance. It must not call `GoodsReceiptPostingHandler` directly or construct movements itself.
5. Return an explicit domain result that includes the document identity and posting outcome.
6. Preserve the created document on posting failure or indeterminate outcome. It must not delete the document or automatically retry posting.

### 4.3 Goods Receipt document gateway

The host-supplied `GoodsReceiptDocumentGateway` creates a valid Standard Goods Receipt `ObjectInstance`, durably persists the complete initial document state, and ensures the configured `DocumentStateProvider` can read that state for the exact returned instance.

The gateway must use the host's configured runtime context and a document type identity resolvable by the configured Posting handler resolver. It must not create register movements or perform posting itself.

The gateway is an explicit host capability. The executor can be implemented and tested against the port, but Standard Goods Receipt Import must not be registered as available in a deployment unless a compliant gateway and the remaining required services are supplied.

## 5. Authorization policy

The executor uses the existing `AuthorizationService`; it must not implement a second permission evaluator.

The protected target is:

```python
SecurityObjectIdentity(
    object_type="document",
    object_code="goods-receipt",
)
```

Before gateway invocation, the executor must require both:

- `AuthorizationRequest(context=security_context, target=GOODS_RECEIPT_DOCUMENT, operation=SecurityOperation.IMPORT)`
- `AuthorizationRequest(context=security_context, target=GOODS_RECEIPT_DOCUMENT, operation=SecurityOperation.POST)`

Standard role definitions must grant these permissions explicitly:

| Standard role | IMPORT | POST |
|---|---:|---:|
| Administrator | Allow | Allow |
| Operator | Allow | Allow |
| Auditor | Deny (no permission) | Deny (no permission) |

The policy is expressed as role permissions, not hard-coded role-name checks. Authorization is checked before document creation. `PostingAPI` does not implicitly enforce this Security policy.

## 6. Result and failure semantics

The Standard domain result must distinguish:

- `POSTED` — only when `PostingResult.is_success` is true;
- `POSTING_FAILED` — when `PostingResult.is_failure` is true;
- `POSTING_INDETERMINATE` — when `PostingResult.is_indeterminate` is true.

Every outcome after document creation includes the persisted document identity. The `ImportRequest.request_identity` is a correlation identifier, not an idempotency key or proof of exactly-once processing.

| Condition | Required behavior |
|---|---|
| Authorization denied | Propagate the existing authorization error; gateway and Posting are not called |
| Invalid payload | Reject through existing contract validation; no side effects |
| Gateway fails before returning a document | Propagate a stable application failure; Posting is not called |
| Posting succeeds | Return `POSTED` with document identity |
| Posting returns definite failure | Return `POSTING_FAILED` with document identity; preserve document |
| Posting returns indeterminate | Return `POSTING_INDETERMINATE` with document identity; preserve document; no automatic retry |

The adapter/transport must not translate `POSTING_FAILED` or `POSTING_INDETERMINATE` into a domain success. Transport-level success merely means the request was parsed and handled; clients must inspect the explicit domain outcome. The API Design must settle the exact serialization of these domain outcomes.

## 7. Persistence, retry, and transaction boundaries

The inspected platform does not demonstrate an atomic transaction spanning object persistence and Posting's register/valuation lifecycle. Slice 8 must not claim atomicity across those boundaries.

The gateway must durably persist the draft and initial `lines` state before Posting. If Posting fails or is indeterminate, the document remains available for diagnosis and reconciliation. The executor must not promise exactly-once processing: the request identity is for correlation and there is no durable import idempotency store in Phase 12.

A client must not automatically resubmit after an unknown outcome. Manual reconciliation is required. Automated recovery is out of scope because the operation identity generated inside Posting is not returned by `PostingAPI.post()`.

## 8. Scope and implementation boundary

Slice 8 will:

- implement the Standard executor, result model, authorization checks, and Standard role permissions;
- define the host-supplied gateway protocol;
- register the import operation only when a compliant executor is explicitly supplied;
- test orchestration using test doubles for the gateway, authorization service, and Posting API;
- keep the full Phase 12 closure conditional until a real host gateway demonstrates durable creation and a complete import/post path.

Slice 8 will not:

- add a generic document metadata/runtime framework;
- add a concrete persistence backend without an approved host implementation and storage contract;
- bypass `GoodsReceiptPostingHandler`, `PostingAPI`, Posting lifecycle coordination, or existing Security authorization;
- add automatic retry, exactly-once guarantees, or automated recovery for indeterminate posting.

## 9. Acceptance criteria

- Unauthorized requests create no document and make no Posting call.
- Both IMPORT and POST permissions are required before side effects.
- Administrator and Operator have the explicit permissions; Auditor does not.
- Gateway returns an `ObjectInstance` whose durable `lines` state is retrievable by Posting's configured `DocumentStateProvider`.
- Posting is invoked only through `PostingAPI` and receives the exact instance returned by the gateway.
- `POSTED` is returned only for `PostingResult.is_success`.
- Failure and indeterminate results retain document identity and are never represented as success.
- No automatic retry or document deletion follows a posting failure/indeterminate result.
- Standard composition does not expose the import operation unless the executor and compliant gateway dependencies are supplied.
- Full Phase 12 closure remains conditional until a real host can execute and validate the durable end-to-end path.

## 10. Follow-on status

Architecture decisions for Slice 8 are approved. Proceed to Concrete API Design review before implementing code. Implementation/test completion alone does not close the host persistence prerequisite.
