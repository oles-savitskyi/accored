from accore.platform.configuration import (
    ConfigurationIdentity,
    ConfigurationLifecycleState,
    ConfigurationVersion,
)


def test_configuration_public_api() -> None:
    assert ConfigurationIdentity is not None
    assert ConfigurationVersion is not None
    assert ConfigurationLifecycleState is not None


def test_configuration_public_api_exports() -> None:
    from accore.platform import configuration

    assert configuration.__all__ == [
        "ConfigurationIdentity",
        "ConfigurationLifecycleState",
        "ConfigurationVersion",
    ]
