from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from accore.platform.foundation import Identifier
from accore.platform.metadata import PublishedMetadataView
from accore.platform.object import ObjectInstance
from accore.platform.runtime.durable_state import RuntimeDurableState

from .identity import PostingOperationIdentity


class DocumentStateProvider(Protocol):
    def get(self, document: ObjectInstance) -> RuntimeDurableState: ...


@dataclass(frozen=True, slots=True)
class PostingPreparationContext:
    """Immutable context for one Posting preparation attempt."""

    operation_identity: PostingOperationIdentity
    replacement_document_identity: Identifier | None = None


@dataclass(frozen=True, slots=True)
class PostingServices:
    document_state: DocumentStateProvider


class PostingClock(Protocol):
    def now(self) -> datetime: ...


@dataclass(frozen=True, slots=True)
class PostingContext:
    document: ObjectInstance
    metadata: PublishedMetadataView
    services: PostingServices
    clock: PostingClock
