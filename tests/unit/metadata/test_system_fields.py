from accore.platform.metadata.system_field import SystemFieldType
from accore.platform.metadata.system_fields import default_catalog_system_fields


def test_default_catalog_system_fields() -> None:
    fields = default_catalog_system_fields()

    assert [field.name for field in fields] == [
        "id",
        "parent_id",
        "is_folder",
        "created_at",
        "updated_at",
        "deleted",
        "version",
    ]


def test_default_catalog_system_field_types() -> None:
    fields = default_catalog_system_fields()

    assert fields[0].field_type is SystemFieldType.ULID
    assert fields[1].field_type is SystemFieldType.ULID
    assert fields[2].field_type is SystemFieldType.BOOLEAN
    assert fields[3].field_type is SystemFieldType.DATETIME
    assert fields[4].field_type is SystemFieldType.DATETIME
    assert fields[5].field_type is SystemFieldType.BOOLEAN
    assert fields[6].field_type is SystemFieldType.INTEGER


def test_only_parent_id_is_nullable() -> None:
    fields = default_catalog_system_fields()

    nullable_fields = [field.name for field in fields if field.nullable]

    assert nullable_fields == ["parent_id"]
