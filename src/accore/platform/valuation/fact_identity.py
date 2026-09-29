from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from accore.platform.foundation import Identifier

from .facts import ValuationFactIdentityFactory, ValuationFactType
from .operations import ValuationOperationIdentity

_ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _canonicalize(value: object) -> object:
    if isinstance(value, Identifier):
        return {"__type__": "Identifier", "value": str(value)}
    if isinstance(value, Decimal):
        return {"__type__": "Decimal", "value": str(value)}
    if isinstance(value, (datetime, date)):
        return {"__type__": type(value).__qualname__, "value": value.isoformat()}
    if isinstance(value, Enum):
        return {"__type__": type(value).__qualname__, "value": value.value}
    if is_dataclass(value):
        return {
            "__type__": type(value).__qualname__,
            **{field.name: _canonicalize(getattr(value, field.name)) for field in fields(value)},
        }
    if isinstance(value, tuple):
        return [_canonicalize(item) for item in value]
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise TypeError(f"Unsupported value for valuation fact identity: {type(value)!r}")


def _encode_ulid(value: bytes) -> str:
    if len(value) != 16:
        raise ValueError("ULID encoding requires exactly 16 bytes.")

    number = int.from_bytes(value, byteorder="big")
    characters = ["0"] * 26
    for index in range(25, -1, -1):
        characters[index] = _ULID_ALPHABET[number & 0x1F]
        number >>= 5
    return "".join(characters)


class DefaultValuationFactIdentityFactory(ValuationFactIdentityFactory):
    """Derive stable ULID-backed identities from operation and fact semantics."""

    def for_operation_fact(
        self,
        operation_identity: ValuationOperationIdentity,
        fact_kind: ValuationFactType,
        semantic_key: tuple[object, ...],
    ) -> Identifier:
        payload = {
            "operation_identity": operation_identity.value,
            "fact_kind": fact_kind.value,
            "semantic_key": semantic_key,
        }
        serialized = json.dumps(
            _canonicalize(payload),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(serialized.encode("utf-8")).digest()[:16]
        return Identifier.from_str(_encode_ulid(digest))
