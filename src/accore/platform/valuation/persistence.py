from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from accore.platform.foundation import Identifier

from .facts import ValuationFact
from .key import ValuationKey
from .operations import ValuationOperationIdentity, ValuationOperationRecord
from .results import CostBalance, CostMovement


class ValuationOperationPersistence(Protocol):
    """Append-only persistence boundary for authoritative valuation operations."""

    def append(
        self,
        operation: ValuationOperationRecord,
    ) -> None:
        """Append an operation, idempotently accepting an identical existing record."""
        ...

    def find(
        self,
        identity: ValuationOperationIdentity,
    ) -> ValuationOperationRecord | None:
        """Return the authoritative operation record, if it exists."""
        ...

    def find_by_document(
        self,
        document_identity: Identifier,
    ) -> tuple[ValuationOperationRecord, ...]:
        """Return authoritative operations associated with a document."""
        ...

    def enumerate(
        self,
    ) -> tuple[ValuationOperationRecord, ...]:
        """Return all authoritative operation records."""
        ...


class ValuationFactPersistence(Protocol):
    """Semantic persistence boundary for authoritative valuation facts."""

    def append(
        self,
        facts: Sequence[ValuationFact],
    ) -> None:
        """Append immutable valuation facts idempotently by fact identity."""
        ...

    def find(
        self,
        identity: Identifier,
    ) -> ValuationFact | None:
        """Return the authoritative valuation fact, if it exists."""
        ...

    def find_by_source_document(
        self,
        document_identity: Identifier,
    ) -> tuple[ValuationFact, ...]:
        """Return valuation facts associated with a source document."""
        ...

    def find_by_source_movement(
        self,
        movement_identity: Identifier,
    ) -> tuple[ValuationFact, ...]:
        """Return valuation facts associated with a source movement."""
        ...

    def find_by_valuation_key(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[ValuationFact, ...]:
        """Return valuation facts associated with a valuation key."""
        ...

    def enumerate(
        self,
    ) -> tuple[ValuationFact, ...]:
        """Return all authoritative valuation facts."""
        ...


class ValuationResultPersistence(Protocol):
    """Semantic persistence boundary for derived valuation results."""

    def append_movements(
        self,
        movements: Sequence[CostMovement],
    ) -> None:
        """Append derived cost movements."""
        ...

    def replace_balance(
        self,
        balance: CostBalance,
    ) -> None:
        """Replace the materialized balance for a valuation key."""
        ...

    def find_movement(
        self,
        identity: Identifier,
    ) -> CostMovement | None:
        """Return one derived cost movement by deterministic identity."""
        ...

    def find_movements(
        self,
        valuation_key: ValuationKey,
    ) -> tuple[CostMovement, ...]:
        """Return derived cost movements for a valuation key."""
        ...

    def enumerate_movements(
        self,
    ) -> tuple[CostMovement, ...]:
        """Return all derived cost movements."""
        ...

    def reconcile_movements(
        self,
        movements: Sequence[CostMovement],
    ) -> None:
        """Replace the complete derived movement projection."""
        ...

    def find_balance(
        self,
        valuation_key: ValuationKey,
    ) -> CostBalance | None:
        """Return the materialized balance for a valuation key, if present."""
        ...

    def enumerate_balances(
        self,
    ) -> tuple[CostBalance, ...]:
        """Return all materialized valuation balances."""
        ...
