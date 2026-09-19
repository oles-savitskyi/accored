from __future__ import annotations

from threading import Barrier, Thread

from accore.platform.foundation import Identifier
from accore.platform.registers.operation_domain import (
    RegisterOperationDomain,
    RegisterOperationDomainRegistry,
)


def test_domain_returns_operation_result() -> None:
    register = Identifier.new()
    domain = RegisterOperationDomain(register)

    assert domain.execute(lambda: 42) == 42
    assert domain.register_identity == register


def test_registry_reuses_domain_for_same_register() -> None:
    register = Identifier.new()
    registry = RegisterOperationDomainRegistry()

    first = registry.get(register)
    second = registry.get(register)

    assert first is second


def test_registry_isolates_different_registers() -> None:
    first_register = Identifier.new()
    second_register = Identifier.new()
    registry = RegisterOperationDomainRegistry()

    first = registry.get(first_register)
    second = registry.get(second_register)

    assert first is not second
    assert first.register_identity == first_register
    assert second.register_identity == second_register


def test_registry_concurrent_first_use_returns_one_domain() -> None:
    register = Identifier.new()
    registry = RegisterOperationDomainRegistry()
    barrier = Barrier(8)
    domains: list[RegisterOperationDomain] = []

    def worker() -> None:
        barrier.wait()
        domains.append(registry.get(register))

    threads = [Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(domains) == 8
    assert len({id(domain) for domain in domains}) == 1
