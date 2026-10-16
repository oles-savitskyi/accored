# Phase 12 — Integration
## Slice 8: Standard Goods Receipt Import Execution — Implementation Notes

**Status:** IMPLEMENTED — TARGETED TESTS PASS; HOST INTEGRATION STILL REQUIRED
**Architecture:** `PHASE_12_Integration_Slice_8_Architecture_Amendment.md`
**API Design:** `PHASE_12_Integration_Slice_8_Concrete_API_Design.md`

## Implemented

- Added `GoodsReceiptDocumentGateway`, a narrow host-supplied port whose contract requires durable draft persistence and a document state readable by the configured Posting stack.
- Added `DefaultStandardGoodsReceiptImportExecutor`, which authorizes `IMPORT` and then `POST` against the canonical `GOODS_RECEIPT_DOCUMENT` identity before side effects, creates the draft through the gateway, and invokes `PostingAPI.post()` once.
- Added immutable `StandardGoodsReceiptImportResult` and outcomes `POSTED`, `POSTING_FAILED`, and `POSTING_INDETERMINATE`. Public errors are stable codes; raw Posting exception details are not exposed.
- Added `IMPORT` and `POST` permissions for Standard Administrator and Operator. Standard Auditor receives neither.
- Exported the executor, gateway, outcome/result, and security target from the relevant Standard packages.
- Preserved conditional Goods Receipt import operation registration. The contract is absent unless a host executor is supplied; duplicate registration is rejected by the existing registry.
- Added tests for both authorization gates, gateway failure, each Posting outcome, no retry on unexpected Posting exceptions, result invariants, role permissions, conditional composition, and duplicate registration.

## Validation performed in the artifact workspace

- Targeted executor, Standard role-definition, and Integration composition tests: **19 passed**.
- Python compile check passed for the new executor, modified source modules, and new tests.

The supplied source archive did not include the `ulid-py` runtime dependency and contained an unrelated syntax error in `standard/security/authentication.py`; targeted tests were therefore run with a temporary test-only ULID shim and a temporary correction to that unrelated line. Neither temporary workaround is included in this ZIP. Ruff, Black, and Mypy were not available in the artifact workspace, so those checks were not claimed. The user's repository environment must run the project's normal checks after applying the archive.

## Required before Phase 12 closure

This implementation does **not** include a concrete host `GoodsReceiptDocumentGateway`. The host must supply one that durably persists the initial `lines` state in the form required by `GoodsReceiptPostingHandler`, and prove that the configured `DocumentStateProvider` can retrieve it. A host-level end-to-end test must cover persisted creation, Posting, and the durable result. Indeterminate Posting remains a manual-reconciliation state: the executor never retries and does not claim exactly-once semantics.
