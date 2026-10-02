from __future__ import annotations


class ReportError(Exception):
    """Base error for Reporting semantic failures."""


class ReportValidationError(ReportError, ValueError):
    """Raised when Reporting metadata or values violate semantic invariants."""


class ReportDataSourceError(ReportError):
    """Base error for Reporting data-source failures."""


class ReportDataSourceNotFoundError(ReportDataSourceError):
    """Raised when a requested Reporting data source is not registered."""
