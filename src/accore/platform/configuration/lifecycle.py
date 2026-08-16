from enum import Enum


class ConfigurationLifecycleState(str, Enum):
    """Lifecycle states of a metadata configuration."""

    DISCOVERED = "discovered"
    LOADED = "loaded"
    VALIDATED = "validated"
    PREPARED = "prepared"
    READY = "ready"
    ACTIVE = "active"
    INACTIVE = "inactive"
