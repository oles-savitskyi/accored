from __future__ import annotations

from accore.platform.metadata.system_field import (
    SystemFieldMetadata,
    SystemFieldType,
)


def default_catalog_system_fields() -> tuple[SystemFieldMetadata, ...]:
    """Return the standard system fields for a catalog."""

    return (
        SystemFieldMetadata(
            name="id",
            field_type=SystemFieldType.ULID,
            nullable=False,
            required=True,
        ),
        SystemFieldMetadata(
            name="parent_id",
            field_type=SystemFieldType.ULID,
            nullable=True,
            required=False,
        ),
        SystemFieldMetadata(
            name="is_folder",
            field_type=SystemFieldType.BOOLEAN,
            nullable=False,
            required=True,
        ),
        SystemFieldMetadata(
            name="created_at",
            field_type=SystemFieldType.DATETIME,
            nullable=False,
            required=True,
        ),
        SystemFieldMetadata(
            name="updated_at",
            field_type=SystemFieldType.DATETIME,
            nullable=False,
            required=True,
        ),
        SystemFieldMetadata(
            name="deleted",
            field_type=SystemFieldType.BOOLEAN,
            nullable=False,
            required=True,
        ),
        SystemFieldMetadata(
            name="version",
            field_type=SystemFieldType.INTEGER,
            nullable=False,
            required=True,
        ),
    )
