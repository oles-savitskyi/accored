from dataclasses import FrozenInstanceError

import pytest

from accore.platform.integration import (
    BoundIntegrationOperation,
    ContractVersion,
    InMemoryIntegrationOperationRegistry,
    IntegrationConflictError,
    IntegrationContractIdentity,
    IntegrationContractKind,
    IntegrationContractNotFoundError,
)


class ExampleContract:
    def __init__(self, identity: IntegrationContractIdentity) -> None:
        self._identity = identity

    @property
    def identity(self) -> IntegrationContractIdentity:
        return self._identity

    @property
    def description(self) -> str:
        return "Example operation"


class ExampleBinding:
    def execute(self, request: object) -> object:
        return {"received": request}


def make_identity(
    *,
    namespace: str = "standard.inventory",
    name: str = "rebuild",
    major: int = 1,
    minor: int = 0,
    kind: IntegrationContractKind = IntegrationContractKind.COMMAND,
) -> IntegrationContractIdentity:
    return IntegrationContractIdentity(
        namespace=namespace,
        name=name,
        version=ContractVersion(major, minor),
        kind=kind,
    )


def make_operation(
    identity: IntegrationContractIdentity | None = None,
) -> BoundIntegrationOperation:
    return BoundIntegrationOperation(
        contract=ExampleContract(identity or make_identity()),  # type: ignore[arg-type]
        binding=ExampleBinding(),
    )


def test_registry_registers_and_resolves_exact_operation() -> None:
    registry = InMemoryIntegrationOperationRegistry()
    operation = make_operation()

    registry.register(operation)

    assert registry.resolve(operation.contract.identity) is operation


def test_registry_uses_all_identity_dimensions_for_resolution() -> None:
    registry = InMemoryIntegrationOperationRegistry()
    operation = make_operation(make_identity())
    other_identities = [
        make_identity(namespace="standard.sales"),
        make_identity(name="rebuild-other"),
        make_identity(minor=1),
        make_identity(major=2),
        make_identity(kind=IntegrationContractKind.QUERY),
    ]
    registry.register(operation)

    for identity in other_identities:
        with pytest.raises(IntegrationContractNotFoundError):
            registry.resolve(identity)


def test_registry_rejects_duplicate_identity_without_replacing_operation() -> None:
    registry = InMemoryIntegrationOperationRegistry()
    first = make_operation()
    second = make_operation()
    registry.register(first)

    with pytest.raises(IntegrationConflictError):
        registry.register(second)

    assert registry.resolve(first.contract.identity) is first


def test_registry_rejects_reregistering_same_operation() -> None:
    registry = InMemoryIntegrationOperationRegistry()
    operation = make_operation()
    registry.register(operation)

    with pytest.raises(IntegrationConflictError):
        registry.register(operation)


def test_registry_raises_contract_not_found_for_unknown_identity() -> None:
    registry = InMemoryIntegrationOperationRegistry()

    with pytest.raises(IntegrationContractNotFoundError):
        registry.resolve(make_identity())


def test_bound_operation_is_immutable() -> None:
    operation = make_operation()

    with pytest.raises(FrozenInstanceError):
        operation.binding = ExampleBinding()  # type: ignore[misc]


def test_bound_operation_rejects_binding_without_execute() -> None:
    class InvalidBinding:
        pass

    with pytest.raises(TypeError, match="execute"):
        BoundIntegrationOperation(
            contract=ExampleContract(make_identity()),  # type: ignore[arg-type]
            binding=InvalidBinding(),  # type: ignore[arg-type]
        )


def test_registry_rejects_malformed_operation() -> None:
    registry = InMemoryIntegrationOperationRegistry()

    with pytest.raises(TypeError, match="contract.identity"):
        registry.register(object())  # type: ignore[arg-type]


def test_registry_rejects_malformed_lookup_identity() -> None:
    registry = InMemoryIntegrationOperationRegistry()

    with pytest.raises(TypeError, match="IntegrationContractIdentity"):
        registry.resolve("standard.inventory.rebuild")  # type: ignore[arg-type]
