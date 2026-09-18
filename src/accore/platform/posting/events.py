from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from accore.platform.foundation import Identifier


@dataclass(frozen=True, slots=True)
class DocumentPosted:
    document_identity: Identifier


@dataclass(frozen=True, slots=True)
class DocumentUnposted:
    document_identity: Identifier


@dataclass(frozen=True, slots=True)
class DocumentReposted:
    document_identity: Identifier


class PostingEventPublisher(Protocol):
    def publish(self, event: object) -> None: ...


class NullPostingEventPublisher:
    def publish(self, event: object) -> None:
        return None
