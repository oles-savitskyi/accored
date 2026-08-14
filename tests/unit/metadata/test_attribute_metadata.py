import pytest

from accore.platform.definitions.attribute import AttributeType
from accore.platform.metadata.attribute import AttributeMetadata


def test_attribute_metadata_preserves_definition_properties() -> None:
    metadata = AttributeMetadata(
        name="code",
        attribute_type=AttributeType.STRING,
        nullable=False,
        default_value="",
        description="Item code",
    )

    assert metadata.name == "code"
    assert metadata.attribute_type is AttributeType.STRING
    assert metadata.nullable is False
    assert metadata.default_value == ""
    assert metadata.description == "Item code"


def test_reference_attribute_metadata_preserves_target() -> None:
    metadata = AttributeMetadata(
        name="unit",
        attribute_type=AttributeType.REFERENCE,
        reference_target="MeasureUnits",
    )

    assert metadata.reference_target == "MeasureUnits"


def test_attribute_metadata_is_immutable() -> None:
    metadata = AttributeMetadata(
        name="code",
        attribute_type=AttributeType.STRING,
    )

    with pytest.raises(AttributeError):
        metadata.name = "other"  # type: ignore[misc]
