from accore.platform.configuration import ConfigurationLifecycleState


def test_configuration_lifecycle_states() -> None:
    assert [state.value for state in ConfigurationLifecycleState] == [
        "discovered",
        "loaded",
        "validated",
        "prepared",
        "ready",
        "active",
        "inactive",
    ]
