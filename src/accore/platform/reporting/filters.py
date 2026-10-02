from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from accore.platform.reporting.errors import ReportValidationError
from accore.platform.reporting.values import ReportValue


class ReportFilterOperator(StrEnum):
    """Semantic comparison operators supported by Reporting."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    IN = "in"


@dataclass(frozen=True, slots=True)
class ReportFilter:
    """Immutable semantic filter over one logical source field."""

    field: str
    operator: ReportFilterOperator
    value: ReportValue | tuple[ReportValue, ...]

    def __post_init__(self) -> None:
        if not self.field:
            raise ReportValidationError("Report filter field must be non-empty")
        if self.operator is ReportFilterOperator.IN:
            if not isinstance(self.value, tuple) or not self.value:
                raise ReportValidationError("IN filter requires a non-empty tuple of values")
            if not all(isinstance(item, ReportValue) for item in self.value):
                raise ReportValidationError("IN filter values must be ReportValue instances")
            return
        if not isinstance(self.value, ReportValue):
            raise ReportValidationError("Non-IN report filters require exactly one ReportValue")
