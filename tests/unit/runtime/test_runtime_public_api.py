from __future__ import annotations

import accore.platform.runtime as runtime_api
from accore.platform.runtime import (
    CatalogRuntime,
    MetadataLookupError,
    RuntimeObjectType,
    RuntimeResolver,
)


def test_runtime_public_api_exports_expected_symbols() -> None:
    expected = {
        "CatalogRuntime",
        "MetadataLookupError",
        "RuntimeObjectType",
        "RuntimeResolver",
    }

    assert set(runtime_api.__all__) == expected


def test_runtime_public_api_exposes_expected_symbols() -> None:
    assert runtime_api.CatalogRuntime is CatalogRuntime
    assert runtime_api.MetadataLookupError is MetadataLookupError
    assert runtime_api.RuntimeResolver is RuntimeResolver


def test_runtime_public_api_exports_runtime_object_type() -> None:
    assert runtime_api.RuntimeObjectType is RuntimeObjectType
