from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProcessingIdentity:
    """Immutable identity of a Processing definition."""

    value: str


@dataclass(frozen=True, slots=True)
class ProcessingDefinition:
    """Immutable declarative definition of a Processing."""

    identity: ProcessingIdentity
    name: str
    description: str
