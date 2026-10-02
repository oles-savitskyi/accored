from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from accore.platform.foundation import Identifier
from accore.platform.reporting.errors import ReportValidationError

ReportValueType = Identifier | bool | int | Decimal | str | date | datetime | None


class ReportDataType(str, Enum):
    """Scalar semantic types supported by the Reporting foundation."""

    IDENTIFIER = "identifier"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    DECIMAL = "decimal"
    STRING = "string"
    DATE = "date"
    DATETIME = "datetime"
    NULL = "null"


@dataclass(frozen=True, slots=True)
class ReportValue:
    """Immutable scalar value allowed at the Reporting semantic boundary."""

    value: ReportValueType

    def __post_init__(self) -> None:
        value = self.value
        if value is None:
            return
        if isinstance(value, bool):
            return
        if isinstance(value, int):
            return
        if isinstance(value, Decimal):
            return
        if isinstance(value, datetime):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ReportValidationError("Report datetime values must be timezone-aware")
            return
        if isinstance(value, (Identifier, str, date)):
            return
        raise ReportValidationError(f"Unsupported report value type: {type(value).__name__}")

    @property
    def data_type(self) -> ReportDataType:
        """Return the semantic Reporting type of this value."""
        if self.value is None:
            return ReportDataType.NULL
        if isinstance(self.value, Identifier):
            return ReportDataType.IDENTIFIER
        if isinstance(self.value, bool):
            return ReportDataType.BOOLEAN
        if isinstance(self.value, int):
            return ReportDataType.INTEGER
        if isinstance(self.value, Decimal):
            return ReportDataType.DECIMAL
        if isinstance(self.value, datetime):
            return ReportDataType.DATETIME
        if isinstance(self.value, date):
            return ReportDataType.DATE
        return ReportDataType.STRING
