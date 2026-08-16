from accore.platform.runtime import MetadataLookupError


def test_metadata_lookup_error_is_lookup_error() -> None:
    assert issubclass(MetadataLookupError, LookupError)


def test_metadata_lookup_error_preserves_message() -> None:
    error = MetadataLookupError("Metadata attribute was not found.")

    assert str(error) == "Metadata attribute was not found."
