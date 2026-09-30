from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PostingOperationIdentity:
    """Immutable identity of one logical Posting lifecycle operation."""

    value: str


class PostingOperationIdentityFactory(Protocol):
    """Create a fresh identity for one logical Posting lifecycle operation."""

    def new(self) -> PostingOperationIdentity: ...


class DefaultPostingOperationIdentityFactory:
    """Generate opaque Posting operation identities."""

    def new(self) -> PostingOperationIdentity:
        from accore.platform.foundation import Identifier

        return PostingOperationIdentity(str(Identifier.new()))


class PostingParticipantOperationIdentityFactory(Protocol):
    """Derive deterministic child identities from a Posting operation identity."""

    def derive(
        self,
        posting_identity: PostingOperationIdentity,
        participant_name: str,
        operation_type: str,
    ) -> str: ...


class DefaultPostingParticipantOperationIdentityFactory:
    """Derive stable opaque participant operation identities."""

    def derive(
        self,
        posting_identity: PostingOperationIdentity,
        participant_name: str,
        operation_type: str,
    ) -> str:
        payload = f"{posting_identity.value}|{participant_name}|{operation_type}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = [
    "DefaultPostingOperationIdentityFactory",
    "DefaultPostingParticipantOperationIdentityFactory",
    "PostingOperationIdentity",
    "PostingOperationIdentityFactory",
    "PostingParticipantOperationIdentityFactory",
]
