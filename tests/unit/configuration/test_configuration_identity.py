from dataclasses import FrozenInstanceError

import pytest

from accore.platform.configuration import (
    ConfigurationIdentity,
    ConfigurationVersion,
)


def test_configuration_identity() -> None:
    identity = ConfigurationIdentity("standard")

    assert identity.value == "standard"
    assert str(identity) == "standard"


def test_configuration_identity_equality() -> None:
    assert ConfigurationIdentity("standard") == ConfigurationIdentity("standard")
    assert ConfigurationIdentity("standard") != ConfigurationIdentity("custom")


def test_configuration_identity_rejects_empty_value() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        ConfigurationIdentity("")


def test_configuration_identity_rejects_whitespace_only_value() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        ConfigurationIdentity("   ")


def test_configuration_identity_is_immutable() -> None:
    identity = ConfigurationIdentity("standard")

    with pytest.raises(FrozenInstanceError):
        identity.value = "custom"  # type: ignore[misc]


def test_configuration_version() -> None:
    version = ConfigurationVersion(1)

    assert version.value == 1
    assert str(version) == "1"


def test_configuration_version_equality() -> None:
    assert ConfigurationVersion(1) == ConfigurationVersion(1)
    assert ConfigurationVersion(1) != ConfigurationVersion(2)


def test_configuration_version_rejects_zero() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        ConfigurationVersion(0)


def test_configuration_version_rejects_negative_value() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        ConfigurationVersion(-1)


def test_configuration_version_is_immutable() -> None:
    version = ConfigurationVersion(1)

    with pytest.raises(FrozenInstanceError):
        version.value = 2  # type: ignore[misc]
