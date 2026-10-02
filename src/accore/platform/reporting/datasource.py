from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from accore.platform.reporting.dataset import ReportRow
from accore.platform.reporting.errors import ReportDataSourceNotFoundError
from accore.platform.reporting.filters import ReportFilter
from accore.platform.reporting.schema import ReportSchema


@dataclass(frozen=True, slots=True)
class ReportDataSourceIdentity:
    """Stable logical identity of a Reporting data source."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Report data source identity value must be non-empty")


@dataclass(frozen=True, slots=True)
class ReportDataSourceRequest:
    """Immutable semantic read request sent to a logical Reporting source."""

    filters: tuple[ReportFilter, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "filters", tuple(self.filters))


class ReportReadConsistency(StrEnum):
    """Consistency semantics declared by a logical Reporting source."""

    SOURCE_LOCAL = "source_local"


class ReportDataSource(Protocol):
    """Read-only logical data source contract."""

    identity: ReportDataSourceIdentity

    def schema(self) -> ReportSchema:
        """Return the source logical schema."""

    def consistency(self) -> ReportReadConsistency:
        """Return the source read consistency semantics."""

    def read(self, request: ReportDataSourceRequest) -> tuple[ReportRow, ...]:
        """Read normalized immutable rows for the semantic request."""


class ReportDataSourceRegistry(Protocol):
    """Registry boundary for logical Reporting data sources."""

    def register(self, source: ReportDataSource) -> None:
        """Register one logical data source."""

    def get(self, identity: ReportDataSourceIdentity) -> ReportDataSource:
        """Resolve one logical data source by identity."""


class DefaultReportDataSourceRegistry:
    """In-memory registry for Reporting logical data sources."""

    def __init__(self) -> None:
        self._sources: dict[ReportDataSourceIdentity, ReportDataSource] = {}

    def register(self, source: ReportDataSource) -> None:
        self._sources[source.identity] = source

    def get(self, identity: ReportDataSourceIdentity) -> ReportDataSource:
        try:
            return self._sources[identity]
        except KeyError as exc:
            raise ReportDataSourceNotFoundError(
                f"Reporting data source not found: {identity}"
            ) from exc
