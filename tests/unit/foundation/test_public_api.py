from accore.platform.foundation import (
    AcCoreError,
    CompilationError,
    DefinitionError,
    Identifier,
    MetadataError,
    RegistryError,
    RuntimeResolutionError,
)


def test_foundation_public_api_exports_identifier() -> None:
    identifier = Identifier.new()

    assert isinstance(identifier, Identifier)


def test_foundation_public_api_exports_error_types() -> None:
    error_types = (
        AcCoreError,
        DefinitionError,
        MetadataError,
        CompilationError,
        RegistryError,
        RuntimeResolutionError,
    )

    for error_type in error_types:
        assert issubclass(error_type, AcCoreError)
