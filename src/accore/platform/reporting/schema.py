from __future__ import annotations

from dataclasses import dataclass

from accore.platform.reporting.errors import ReportValidationError
from accore.platform.reporting.values import ReportDataType


@dataclass(frozen=True, slots=True)
class ReportField:
    """Immutable logical field exposed by a Reporting data source."""

    name: str
    data_type: ReportDataType

    def __post_init__(self) -> None:
        if not self.name:
            raise ReportValidationError("Report field name must be non-empty")


@dataclass(frozen=True, slots=True)
class ReportSchema:
    """Immutable logical schema exposed by a Reporting data source."""

    fields: tuple[ReportField, ...]

    def __post_init__(self) -> None:
        fields = tuple(self.fields)
        names = [field.name for field in fields]
        if len(names) != len(set(names)):
            raise ReportValidationError("Report schema field names must be unique")
        object.__setattr__(self, "fields", fields)

    def field(self, name: str) -> ReportField:
        for field in self.fields:
            if field.name == name:
                return field
        raise ReportValidationError(f"Unknown report schema field: {name}")
