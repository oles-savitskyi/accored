from __future__ import annotations

import pytest

from accore.platform.valuation import ValuationKey


def test_valuation_key_normalizes_dimension_order() -> None:
    first = ValuationKey(
        {
            "warehouse": "WH-01",
            "product": "PR-01",
        }
    )
    second = ValuationKey(
        {
            "product": "PR-01",
            "warehouse": "WH-01",
        }
    )

    assert first == second
    assert first.canonical_dimensions == (
        ("product", "PR-01"),
        ("warehouse", "WH-01"),
    )


def test_valuation_key_is_hashable_and_semantically_comparable() -> None:
    key = ValuationKey(
        {
            "product": "PR-01",
            "warehouse": "WH-01",
        }
    )

    mapping = {key: "value"}

    assert mapping[key] == "value"


def test_valuation_key_is_immutable() -> None:
    key = ValuationKey(
        {
            "product": "PR-01",
            "warehouse": "WH-01",
        }
    )

    with pytest.raises(TypeError):
        key.dimensions["product"] = "PR-02"  # type: ignore[index]


def test_valuation_key_rejects_empty_dimension_name() -> None:
    with pytest.raises(ValueError, match="dimension names must be non-empty"):
        ValuationKey({"": "PR-01"})


def test_valuation_key_rejects_non_string_dimension_value() -> None:
    with pytest.raises(
        TypeError,
        match="must contain a string value",
    ):
        ValuationKey({"product": 123})  # type: ignore[dict-item]


def test_valuation_key_supports_mapping_style_access() -> None:
    key = ValuationKey(
        {
            "product": "PR-01",
            "warehouse": "WH-01",
        }
    )

    assert key["product"] == "PR-01"
    assert key.get("warehouse") == "WH-01"
    assert key.get("missing") is None
    assert list(key) == ["product", "warehouse"]
    assert len(key) == 2
