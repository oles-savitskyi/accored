from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from accore.platform.foundation import Identifier
from accore.platform.reporting import ReportDataType, ReportValidationError, ReportValue


def test_report_value_preserves_decimal_without_float_conversion() -> None:
    value = ReportValue(Decimal("10.50"))

    assert value.value == Decimal("10.50")
    assert value.data_type is ReportDataType.DECIMAL


def test_report_value_distinguishes_boolean_from_integer() -> None:
    assert ReportValue(True).data_type is ReportDataType.BOOLEAN
    assert ReportValue(1).data_type is ReportDataType.INTEGER


def test_report_value_distinguishes_date_from_datetime() -> None:
    assert ReportValue(date(2026, 10, 1)).data_type is ReportDataType.DATE
    assert ReportValue(datetime(2026, 10, 1, tzinfo=UTC)).data_type is ReportDataType.DATETIME


def test_report_value_accepts_identifier() -> None:
    assert ReportValue(Identifier.new()).data_type is ReportDataType.IDENTIFIER


def test_report_value_rejects_float() -> None:
    with pytest.raises(ReportValidationError):
        ReportValue(1.5)  # type: ignore[arg-type]


def test_report_value_rejects_naive_datetime() -> None:
    with pytest.raises(ReportValidationError):
        ReportValue(datetime.fromisoformat("2026-10-01T00:00:00"))


def test_report_value_accepts_none_as_nullable_value() -> None:
    assert ReportValue(None).data_type is ReportDataType.NULL
