from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class ValuationKey:
    """Immutable semantic key owned by the Valuation subsystem."""

    dimensions: Mapping[str, str]

    def __post_init__(self) -> None:
        normalized = tuple(sorted(self.dimensions.items(), key=lambda item: item[0]))

        for name, value in normalized:
            if not name:
                raise ValueError("ValuationKey dimension names must be non-empty.")
            if not isinstance(value, str):
                raise TypeError(f"ValuationKey dimension '{name}' must contain a string value.")

        object.__setattr__(
            self,
            "dimensions",
            MappingProxyType(dict(normalized)),
        )

    @property
    def canonical_dimensions(self) -> tuple[tuple[str, str], ...]:
        """Return the deterministic representation used for semantic identity."""
        return tuple(self.dimensions.items())

    def __hash__(self) -> int:
        return hash(self.canonical_dimensions)

    def __getitem__(self, key: str) -> str:
        return self.dimensions[key]

    def get(self, key: str, default: str | None = None) -> str | None:
        return self.dimensions.get(key, default)

    def __iter__(self) -> Iterator[str]:
        return iter(self.dimensions)

    def __len__(self) -> int:
        return len(self.dimensions)
