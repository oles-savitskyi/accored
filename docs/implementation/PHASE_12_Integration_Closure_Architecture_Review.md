# Phase 12 — Integration
## Closure Architecture Review: Standard Goods Receipt Import

**Status:** DECISION ACCEPTED — PROCEED TO PHASE 13 STANDARD MVP  
**Date:** 2026-10-16  
**Scope:** Phase 12 closure decision and the follow-on Standard MVP document lifecycle.

## 1. Decision summary

Phase 12 is closed under an explicitly accepted exception: the Integration infrastructure and Slice 8 import orchestration are implemented, but the repository does not demonstrate a concrete Standard Goods Receipt document runtime and persistence path that can be used by a real host. Do not represent the end-to-end import criterion as demonstrated.

Do **not** expand Slice 8 into a generic document subsystem. Keep the approved `GoodsReceiptDocumentGateway` as the narrow host boundary. Treat the missing out-of-box document lifecycle as a distinct Standard vertical capability, designed and implemented through the project's architecture-first process.

The project owner accepted Option A on 2026-10-16. The resulting decision is:

1. Close Phase 12's Integration infrastructure with an explicit acceptance exception for end-to-end Standard Goods Receipt import.
2. Do not claim that Goods Receipt import works out of the box; Slice 8 provides orchestration over a host-supplied gateway.
3. Carry the minimum Standard Goods Receipt document lifecycle into Phase 13 — Standard MVP if it is required for the MVP.
4. Before implementation, define and approve the minimal architecture for document metadata/runtime resolution, object persistence and retrieval, and the `DocumentStateProvider` path used by Posting.
5. Prove durable draft creation, Posting through `PostingAPI`, and retrieval of the resulting state with an end-to-end test.

This avoids both false closure and an unplanned expansion of Integration into a generic document/persistence framework.

## 2. What the current code establishes

The current source and documentation archives establish these facts:

- `ObjectPersistence` is a protocol exposing create/get/update; no concrete business-object persistence implementation was found in the inspected source archive.
- `PersistentObjectMaterializer` and `PersistentObjectHydrator` map between runtime durable state and persistent representations. They do not supply a storage backend or a complete object lifecycle.
- `RuntimeResolver` resolves `CatalogMetadata` to `CatalogRuntime`. The inspected metadata model defines `CATALOG`, but not a Goods Receipt document metadata type.
- `ObjectCreator` creates an `ObjectInstance` from a resolved runtime object type and context; creation alone does not persist it.
- `DocumentStateProvider` is a protocol. Posting requires it to retrieve the durable document state for the exact `ObjectInstance` being posted.
- `GoodsReceiptPostingHandler` expects a specific `lines` state structure and creates the movement set through the existing Posting flow.
- Slice 8's `GoodsReceiptDocumentGateway` is intentionally host-supplied. The executor delegates draft creation to it and invokes `PostingAPI.post()`; it does not create or persist the document itself.
- The current tests verify orchestration with test doubles. They do not prove a real durable Standard Goods Receipt import-to-Posting path.

These findings mean that implementing only a storage adapter is not yet sufficient: a valid document type must also be representable/resolvable and connected to persistence and Posting's document-state lookup.

## 3. Fit against the approved architecture

The existing Phase 12 Architecture Definition lists import as an acceptance criterion: a minimum supported import scenario must pass contract validation and Runtime execution without direct state manipulation. It also requires an external path to reach the appropriate Runtime boundary.

Slice 8's approved amendment deliberately states that:

- the gateway is a narrow host-supplied capability;
- Integration must not directly create runtime objects or persist state;
- the generic document metadata/runtime framework is not part of Slice 8;
- the original Slice 8 amendment made closure conditional on a real host demonstrating durable creation and the complete import/Posting path; the owner subsequently accepted an explicit exception and moved this end-to-end path to Phase 13.

Therefore, the Slice 8 implementation is consistent with its approved scope, but it does not by itself satisfy the end-to-end import acceptance evidence. The gap is not a defect in the executor; it is an unresolved Standard host/runtime capability.

## 4. Options

### Option A — Close Phase 12 with an explicit acceptance exception

Close the Integration infrastructure work and amend the roadmap/closure record to state that the Standard Goods Receipt import operation is an optional host binding, not an out-of-box capability. Record the real durable import vertical path as a prerequisite for Standard MVP acceptance.

**Advantages:** preserves the approved Slice 8 boundary; avoids widening Phase 12; allows the next phase to focus on a complete business lifecycle.

**Risks:** this is a deliberate exception to the current Phase 12 acceptance criteria, which include a working minimum import scenario. The roadmap and closure document must not imply that this criterion was demonstrated.

### Option B — Keep Phase 12 open and add a narrowly scoped vertical capability

Approve a separate architecture amendment and design for the minimum Goods Receipt document lifecycle, then implement the runtime/metadata and persistence pieces needed by the host gateway and prove the full path before closing Phase 12.

**Advantages:** Phase 12 can close against its current acceptance criteria without an exception.

**Risks:** broadens Phase 12 beyond the existing Integration-only boundary and may require platform changes to metadata/runtime and persistence contracts. It should not be treated as a small adapter-only implementation.

### Option C — Add a generic document runtime/persistence framework now

Build general-purpose document metadata, runtime resolution and persistence infrastructure as part of Phase 12.

**Recommendation:** reject. This is wider than the demonstrated need, conflicts with the approved Slice 8 decision not to introduce a generic document subsystem incidentally, and creates architecture before the MVP document requirements are settled.

## 5. Decision applied

The project owner accepted **Option A** on 2026-10-16. The applied boundary is:

- Phase 12 is closed for Integration infrastructure with an explicit exception for the unproven end-to-end Standard Goods Receipt import path;
- Goods Receipt import is not operational out of the box based on the current evidence;
- the minimum real document lifecycle is a prerequisite for the complete Standard MVP vertical scenario and must be designed and implemented in Phase 13;
- no generic document runtime/persistence framework is authorized by this decision. Any extension must be justified in the approved architecture.

This decision intentionally accepts an exception to the original Phase 12 import acceptance evidence. It does not permit claiming successful durable import based solely on unit tests with a fake gateway.

## 6. Minimum scope for the follow-on vertical slice

The follow-on design should answer these questions before implementation:

1. **Document identity and metadata:** how is the Standard Goods Receipt document type identified and resolved without incorrectly treating it as a catalog?
2. **Runtime representation:** which existing object/runtime contracts can be reused, and what is the smallest justified extension for a document type?
3. **Persistence:** which concrete storage implementation owns create/get/update and how are durable state and document identity materialized/hydrated?
4. **Posting state lookup:** how does the configured `DocumentStateProvider` retrieve the persisted `lines` state for the exact object returned by the gateway?
5. **Lifecycle/result durability:** how is the final document/posting state observed after `PostingAPI.post()`, including definite failure and indeterminate outcome?
6. **Composition:** how are the runtime, persistence adapter, gateway and Posting services composed by the Standard host?
7. **End-to-end proof:** can a test create a Goods Receipt through the supported host boundary, read its durable state, post through `PostingAPI`, and verify the durable outcome without bypassing Runtime, Security, or Posting?

Do not add automatic retries or exactly-once guarantees as part of this scope. Preserve Slice 8's approved indeterminate-outcome semantics.

## 7. Closure evidence required

Before claiming the Standard Goods Receipt import is end-to-end complete, require all of the following:

- a concrete host `GoodsReceiptDocumentGateway`, not a test double;
- document type resolution and runtime composition for Goods Receipt;
- durable persistence of the initial document state;
- successful `DocumentStateProvider` retrieval of that state;
- Posting invoked only through `PostingAPI` on the exact persisted instance;
- an end-to-end test covering successful Posting and at least the defined failure/indeterminate behavior;
- current full test suite, Ruff, Black, Mypy, and `git diff --check` results from the user's repository;
- updated roadmap and closure record that distinguish completed infrastructure from any accepted scope exception.

## 8. Owner decision recorded

**Accepted decision: Option A — Proceed to Standard MVP.**

The project owner accepted the explicit Phase 12 import-acceptance exception on 2026-10-16. Phase 12 is closed for Integration infrastructure, while the real Standard Goods Receipt document lifecycle remains a Phase 13 prerequisite for the complete MVP vertical scenario. This is not a claim that end-to-end durable import has passed.

The roadmap and `PHASE_12_Integration_Validation_and_Closure.md` have been updated to record this decision. Before implementation of the follow-on capability, prepare the Architecture Definition / Scope, obtain review/approval, and then prepare and approve the Concrete API Design.
