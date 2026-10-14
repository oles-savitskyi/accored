from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from accore.platform.security.object import SecurityObjectIdentity
from accore.platform.security.operation import SecurityOperation


@dataclass(frozen=True, slots=True)
class ContractVersion:
    """Semantic version of an externally published Integration contract."""

    major: int
    minor: int

    def __post_init__(self) -> None:
        if self.major < 0:
            raise ValueError("Contract major version must be non-negative.")
        if self.minor < 0:
            raise ValueError("Contract minor version must be non-negative.")


@dataclass(frozen=True, slots=True)
class IntegrationSecurityRequirement:
    """Authorization semantics declared by an Integration capability."""

    target: SecurityObjectIdentity
    operation: SecurityOperation


class IntegrationContractKind(StrEnum):
    """Kinds of externally published Integration capabilities."""

    COMMAND = "command"
    QUERY = "query"
    DATASET = "dataset"
    EVENT = "event"
    IMPORT = "import"
    EXPORT = "export"


@dataclass(frozen=True, slots=True)
class IntegrationContractIdentity:
    """Stable identity for an Integration contract and its version."""

    namespace: str
    name: str
    version: ContractVersion
    kind: IntegrationContractKind

    def __post_init__(self) -> None:
        if not self.namespace.strip():
            raise ValueError("Contract namespace must be non-empty.")
        if not self.name.strip():
            raise ValueError("Contract name must be non-empty.")
        if not isinstance(self.version, ContractVersion):
            raise TypeError("Contract version must be a ContractVersion.")
        if not isinstance(self.kind, IntegrationContractKind):
            raise TypeError("Contract kind must be an IntegrationContractKind.")


class IntegrationContract(Protocol):
    """Descriptive contract metadata, independent of its executable binding."""

    @property
    def identity(self) -> IntegrationContractIdentity:
        """Return the stable identity of this contract."""
        ...

    @property
    def description(self) -> str:
        """Return a human-readable description of the capability."""
        ...
