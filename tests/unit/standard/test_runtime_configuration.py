from __future__ import annotations

from accore.platform.foundation import Identifier
from standard.configuration import StandardRuntimeConfiguration


def test_standard_runtime_configuration_is_immutable() -> None:
    register_identity = Identifier.new()
    configuration = StandardRuntimeConfiguration(register_identity)

    assert configuration.inventory_register_identity == register_identity


def test_standard_bootstrap_initializes_runtime_configuration_projection() -> None:
    from standard.bootstrap import StandardConfigurationBootstrap
    from standard.registers.inventory import INVENTORY_REGISTER_ID

    context, _ = StandardConfigurationBootstrap().initialize()

    configuration = context.application_configuration

    assert isinstance(configuration, StandardRuntimeConfiguration)
    assert configuration.inventory_register_identity == INVENTORY_REGISTER_ID
