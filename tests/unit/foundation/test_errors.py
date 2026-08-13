import pytest

from accore.platform.foundation.errors import (
    AcCoreError,
    CompilationError,
    DefinitionError,
    MetadataError,
    RegistryError,
    RuntimeResolutionError,
)


@pytest.mark.parametrize(
    "error_type",
    [
        DefinitionError,
        MetadataError,
        CompilationError,
        RegistryError,
        RuntimeResolutionError,
    ],
)
def test_platform_errors_inherit_from_accore_error(
    error_type: type[AcCoreError],
) -> None:
    error = error_type("test error")

    assert isinstance(error, AcCoreError)
    assert str(error) == "test error"


def test_accore_error_is_an_exception() -> None:
    error = AcCoreError("test error")

    assert isinstance(error, Exception)


def test_specific_error_can_be_caught_as_accore_error() -> None:
    with pytest.raises(AcCoreError):
        raise DefinitionError("invalid definition")
