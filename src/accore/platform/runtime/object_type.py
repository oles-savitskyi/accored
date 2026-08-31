from __future__ import annotations

from typing import Protocol, runtime_checkable

from accore.platform.foundation import Identifier


@runtime_checkable
class RuntimeObjectType(Protocol):
    """Architectural contract for executable runtime object types.

    RuntimeResolver resolves RuntimeObjectType instances.
    Object Runtime consumes RuntimeObjectType instances without depending
    on concrete runtime implementations such as CatalogRuntime.
    """

    def metadata_identity(self) -> Identifier:
        """Return the identity of the metadata represented by this runtime type."""
        ...
