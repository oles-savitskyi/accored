from __future__ import annotations


class AcCoreError(Exception):
    """Base exception for AcCoreD."""


class DefinitionError(AcCoreError):
    """Raised when a definition is invalid."""


class MetadataError(AcCoreError):
    """Raised when metadata is invalid or inconsistent."""


class CompilationError(AcCoreError):
    """Raised when a definition cannot be compiled."""


class RegistryError(AcCoreError):
    """Raised when registry operations fail."""


class RuntimeResolutionError(AcCoreError):
    """Raised when runtime resolution fails."""
