import pytest

from accore.platform.metadata.system_field import (
    SystemFieldMetadata,
    SystemFieldType,
)


def test_system_field_metadata() -> None:
    field = SystemFieldMetadata(
        name="id",
        field_type=SystemFieldType.ULID,
        nullable=False,
        required=True,
    )

    assert field.name == "id"
    assert field.field_type is SystemFieldType.ULID
    assert field.nullable is False
    assert field.required is True


def test_system_field_metadata_is_immutable() -> None:
    field = SystemFieldMetadata(
        name="id",
        field_type=SystemFieldType.ULID,
        nullable=False,
        required=True,
    )

    with pytest.raises(AttributeError):
        field.name = "other"  # type: ignore[misc]
