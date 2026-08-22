from accore.platform.configuration import RuntimeConfigurationContext
from accore.platform.runtime.resolution import RuntimeResolver
from standard.bootstrap import StandardConfigurationBootstrap


def test_standard_configuration_bootstrap_exposes_initialize_contract() -> None:
    bootstrap = StandardConfigurationBootstrap()

    assert hasattr(bootstrap, "initialize")


def test_standard_configuration_bootstrap_creates_runtime_components() -> None:
    bootstrap = StandardConfigurationBootstrap()

    context, resolver = bootstrap.initialize()

    assert isinstance(context, RuntimeConfigurationContext)
    assert isinstance(resolver, RuntimeResolver)
