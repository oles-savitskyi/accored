from dataclasses import dataclass
from inspect import signature

from accore.platform.configuration.identity import ConfigurationIdentity
from accore.platform.persistence import ObjectPersistence


@dataclass(frozen=True)
class PersistentConfiguration:
    identity: ConfigurationIdentity
    value: str


class InMemoryConfigurationPersistence:
    def __init__(self) -> None:
        self._configurations: dict[ConfigurationIdentity, PersistentConfiguration] = {}

    def create(self, configuration: PersistentConfiguration) -> None:
        self._configurations[configuration.identity] = configuration

    def get(self, identity: ConfigurationIdentity) -> PersistentConfiguration:
        return self._configurations[identity]

    def update(self, configuration: PersistentConfiguration) -> None:
        self._configurations[configuration.identity] = configuration


def test_configuration_persistence_contract_shape() -> None:
    assert list(signature(ObjectPersistence.create).parameters) == ["self", "obj"]
    assert list(signature(ObjectPersistence.get).parameters) == ["self", "identity"]
    assert list(signature(ObjectPersistence.update).parameters) == ["self", "obj"]


def test_configuration_persistence_supports_create_get_update() -> None:
    persistence = InMemoryConfigurationPersistence()
    identity = ConfigurationIdentity("standard")
    created = PersistentConfiguration(identity, "v1")
    updated = PersistentConfiguration(identity, "v2")

    persistence.create(created)
    assert persistence.get(identity) == created

    persistence.update(updated)
    assert persistence.get(identity) == updated
