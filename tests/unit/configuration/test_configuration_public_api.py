from accore.platform.configuration import (
    ActiveConfiguration,
    ConfigurationActivator,
    ConfigurationCandidate,
    ConfigurationIdentity,
    ConfigurationLifecycleState,
    ConfigurationLoader,
    ConfigurationValidationError,
    ConfigurationValidator,
    ConfigurationVersion,
)


def test_configuration_public_api() -> None:
    assert ActiveConfiguration is not None
    assert ConfigurationActivator is not None
    assert ConfigurationCandidate is not None
    assert ConfigurationIdentity is not None
    assert ConfigurationLifecycleState is not None
    assert ConfigurationLoader is not None
    assert ConfigurationValidationError is not None
    assert ConfigurationValidator is not None
    assert ConfigurationVersion is not None


def test_configuration_public_api_exports() -> None:
    from accore.platform import configuration

    assert configuration.__all__ == [
        "ActiveConfiguration",
        "ConfigurationActivator",
        "ConfigurationCandidate",
        "ConfigurationIdentity",
        "ConfigurationLifecycleState",
        "ConfigurationLoader",
        "ConfigurationValidationError",
        "ConfigurationValidator",
        "ConfigurationVersion",
    ]
