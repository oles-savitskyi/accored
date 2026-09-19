from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from accore.platform.foundation import Identifier
from accore.platform.registers.movement import Movement


class RegisterFactPersistence(Protocol):
    """Persistence boundary for authoritative Register Movement facts."""

    def append(self, movements: Sequence[Movement]) -> None:
        """Persist accepted Movement facts."""

    def find_by_source_document(
        self,
        register_identity: Identifier,
        source_document_identity: Identifier,
    ) -> tuple[Movement, ...]:
        """Return persisted movements for a Register and source document."""

    def remove(self, movement_identities: Sequence[Identifier]) -> None:
        """Remove persisted Movement facts by semantic Movement identity."""

    def enumerate(
        self,
        register_identity: Identifier,
    ) -> tuple[Movement, ...]:
        """Return all persisted Movement facts for a Register."""
