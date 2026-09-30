# WP-8 Slice 10.7 implementation archive

Implemented:
- durable ESTABLISH intent registration before Repost REMOVE
- PostingResultParticipant/Coordinator prepare_establish and recover contracts
- ValuationPostingCoordinator deterministic ESTABLISH registration and REMOVE -> ESTABLISH recovery
- PostingEngine.recover / PostingAPI.recover
- idempotent ESTABLISH operation construction reuse
- focused unit coverage for registration, ordering, and recovery

Validation in the build environment:
- pytest focused Posting + Valuation suites: 159 passed
- ruff check src tests: PASS
- black --check src tests: PASS (237 files unchanged)
- git diff --check: PASS

The full suite could not be used as the final gate in this archive environment because its Python runtime is 3.13 while the project baseline is Python 3.14; unrelated pre-existing dataclass/zero-argument-super failures occur under that mismatch. Run the project's normal Python 3.14 gate after applying the archive.
