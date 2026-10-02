import pytest

from accore.platform.reporting import (
    DefaultReportDataSourceRegistry,
    ReportDataSourceIdentity,
    ReportDataSourceNotFoundError,
    ReportDataSourceRequest,
    ReportDataType,
    ReportField,
    ReportFilter,
    ReportFilterOperator,
    ReportReadConsistency,
    ReportRow,
    ReportSchema,
    ReportValue,
)


class Source:
    identity = ReportDataSourceIdentity("inventory.balance")

    def schema(self) -> ReportSchema:
        return ReportSchema((ReportField("warehouse", ReportDataType.STRING),))

    def consistency(self) -> ReportReadConsistency:
        return ReportReadConsistency.SOURCE_LOCAL

    def read(self, request: ReportDataSourceRequest) -> tuple[ReportRow, ...]:
        return ()


def test_registry_resolves_registered_source() -> None:
    registry = DefaultReportDataSourceRegistry()
    source = Source()
    registry.register(source)

    assert registry.get(source.identity) is source


def test_registry_has_explicit_not_found_error() -> None:
    registry = DefaultReportDataSourceRegistry()

    with pytest.raises(ReportDataSourceNotFoundError):
        registry.get(ReportDataSourceIdentity("missing"))


def test_request_is_immutable() -> None:
    filters = (
        ReportFilter(
            "warehouse",
            ReportFilterOperator.EQUALS,
            ReportValue("A"),
        ),
    )
    request = ReportDataSourceRequest(filters=filters)

    assert request.filters == filters


def test_source_declares_source_local_consistency() -> None:
    assert Source().consistency() is ReportReadConsistency.SOURCE_LOCAL
