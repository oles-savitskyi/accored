from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from accore.platform.reporting.errors import ReportValidationError
from accore.platform.reporting.schema import ReportSchema
from accore.platform.reporting.values import ReportValue


@dataclass(frozen=True, slots=True)
class ReportRow:
    """Immutable analytical row with a defensively normalized value mapping."""

    values: Mapping[str, ReportValue]

    def __post_init__(self) -> None:
        values = dict(self.values)
        object.__setattr__(self, "values", MappingProxyType(values))

    def __getitem__(self, field: str) -> ReportValue:
        return self.values[field]


@dataclass(frozen=True, slots=True)
class ReportDataset:
    """Immutable analytical dataset returned by the Reporting runtime."""

    schema: ReportSchema
    rows: tuple[ReportRow, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "rows", tuple(self.rows))
        field_names = {field.name for field in self.schema.fields}
        for row in self.rows:
            if set(row.values) != field_names:
                raise ReportValidationError(
                    "Report dataset row fields must exactly match the dataset schema"
                )
