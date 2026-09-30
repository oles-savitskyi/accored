from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Protocol

from accore.platform.foundation import Identifier

from .operations import ValuationOperationIdentity

_ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


@dataclass(frozen=True, slots=True)
class ValuationPreparationContext:
    """Immutable context identifying one valuation preparation attempt."""

    operation_identity: ValuationOperationIdentity
    replacement_document_identity: Identifier | None = None


class ValuationPreparationIdentityFactory(Protocol):
    """Create deterministic identities for preparation-local references."""

    def planned_layer_reference(
        self,
        operation_identity: ValuationOperationIdentity,
        source_movement_identity: Identifier,
    ) -> Identifier: ...

    def consumption_request(
        self,
        operation_identity: ValuationOperationIdentity,
        source_identity: Identifier,
    ) -> Identifier: ...


class DefaultValuationPreparationIdentityFactory:
    """Derive stable identities from one valuation operation and source identity."""

    def planned_layer_reference(
        self,
        operation_identity: ValuationOperationIdentity,
        source_movement_identity: Identifier,
    ) -> Identifier:
        return _deterministic_identifier(
            operation_identity.value,
            "planned-layer-reference",
            str(source_movement_identity),
        )

    def consumption_request(
        self,
        operation_identity: ValuationOperationIdentity,
        source_identity: Identifier,
    ) -> Identifier:
        return _deterministic_identifier(
            operation_identity.value,
            "consumption-request",
            str(source_identity),
        )


def _deterministic_identifier(*parts: str) -> Identifier:
    payload = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).digest()[:16]
    return Identifier.from_str(_encode_ulid(digest))


def _encode_ulid(value: bytes) -> str:
    if len(value) != 16:
        raise ValueError("ULID encoding requires exactly 16 bytes.")

    number = int.from_bytes(value, byteorder="big")
    characters = ["0"] * 26
    for index in range(25, -1, -1):
        characters[index] = _ULID_ALPHABET[number & 0x1F]
        number >>= 5
    return "".join(characters)


__all__ = [
    "DefaultValuationPreparationIdentityFactory",
    "ValuationPreparationContext",
    "ValuationPreparationIdentityFactory",
]
