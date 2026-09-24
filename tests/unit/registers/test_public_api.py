from accore.platform import registers
from accore.platform.registers import (
    DefaultBalanceQueryService,
    DefaultMovementQueryService,
    DefaultTotalsEngine,
    DefaultTotalsMaintenanceCoordinator,
    MaintenanceOperation,
    MappingRegisterPostingContractResolver,
    MovementType,
    RegisterMutationOrchestrator,
    RegisterOperationDomain,
    RegisterOperationDomainRegistry,
    TotalsConsistencyState,
    TotalsDefinition,
    TotalsEngine,
    TotalsLifecycleState,
    TotalsMaintenanceCoordinator,
    TotalsReader,
)

EXPECTED_PUBLIC_API = {
    "BalanceQuery",
    "BalanceQueryError",
    "BalanceQueryService",
    "BalanceQueryValidationError",
    "BalanceResult",
    "DefaultBalanceQueryService",
    "DefaultMovementQueryService",
    "DefaultMovementValidator",
    "DefaultTotalsEngine",
    "DefaultTotalsMaintenanceCoordinator",
    "MaintenanceOperation",
    "MaintenanceOutcome",
    "MaintenanceResult",
    "MappingRegisterPostingContractResolver",
    "Movement",
    "MovementAttributes",
    "MovementDimensionFilter",
    "MovementDimensions",
    "MovementQuery",
    "MovementQueryPeriod",
    "MovementQueryService",
    "MovementQueryValidationError",
    "MovementResources",
    "MovementType",
    "MovementValidationError",
    "MovementValidator",
    "RegisterMutationMaintenanceError",
    "RegisterMutationOrchestrator",
    "RegisterOperationDomain",
    "RegisterOperationDomainRegistry",
    "RegisterPostingContract",
    "RegisterPostingContractResolver",
    "TotalValue",
    "TotalsAggregationError",
    "TotalsConsistencyState",
    "TotalsDefinition",
    "TotalsDefinitionError",
    "TotalsEngine",
    "TotalsError",
    "TotalsKey",
    "TotalsKeyError",
    "TotalsLifecycleState",
    "TotalsMaintenanceAdmissionError",
    "TotalsMaintenanceCoordinator",
    "TotalsMaintenanceState",
    "TotalsMovementTypeError",
    "TotalsReader",
    "TotalsRegisterMismatchError",
    "TotalsResourceError",
}


def test_package_all_matches_approved_public_api() -> None:
    assert set(registers.__all__) == EXPECTED_PUBLIC_API
    assert len(registers.__all__) == len(EXPECTED_PUBLIC_API)


def test_every_declared_public_symbol_is_bound_in_package_namespace() -> None:
    for name in registers.__all__:
        assert hasattr(registers, name), name
        assert getattr(registers, name) is not None


def test_internal_implementation_helpers_are_not_public() -> None:
    assert not hasattr(registers, "_MovementSet")
    assert not hasattr(registers, "_ImmutableMapping")
    assert not hasattr(registers, "MovementSetLike")
    assert not hasattr(registers, "RegisterService")
    assert not hasattr(registers, "RegisterFacade")


def test_recover_is_public_without_recover_maintenance_operation() -> None:
    assert hasattr(TotalsMaintenanceCoordinator, "recover")
    assert [operation.name for operation in MaintenanceOperation] == [
        "APPLY",
        "REMOVE",
        "REBUILD",
    ]
    assert not hasattr(MaintenanceOperation, "RECOVER")


def test_public_maintenance_state_contract_is_stable() -> None:
    assert [state.name for state in TotalsLifecycleState] == [
        "CREATED",
        "ACTIVE",
        "MAINTENANCE",
    ]
    assert [state.name for state in TotalsConsistencyState] == [
        "VALID",
        "INDETERMINATE",
        "RECOVERY_REQUIRED",
    ]


def test_public_concrete_implementations_are_constructible() -> None:
    register = "goods"
    definition = TotalsDefinition(
        register_identity=register,
        dimensions=("product",),
        resource_name="quantity",
        movement_type_signs={MovementType.INCOME: 1, MovementType.EXPENSE: -1},
    )
    engine = DefaultTotalsEngine((definition,))
    domains = RegisterOperationDomainRegistry()

    assert isinstance(domains.get(register), RegisterOperationDomain)
    assert DefaultTotalsMaintenanceCoordinator(engine, object())
    assert DefaultBalanceQueryService(engine)
    assert DefaultMovementQueryService(object())


def test_public_package_is_canonical_import_boundary() -> None:
    assert registers.DefaultTotalsEngine is DefaultTotalsEngine
    assert registers.DefaultTotalsMaintenanceCoordinator is DefaultTotalsMaintenanceCoordinator
    assert (
        registers.MappingRegisterPostingContractResolver is MappingRegisterPostingContractResolver
    )
    assert registers.RegisterOperationDomain is RegisterOperationDomain
    assert registers.RegisterOperationDomainRegistry is RegisterOperationDomainRegistry
    assert registers.RegisterMutationOrchestrator is RegisterMutationOrchestrator
    assert registers.DefaultMovementQueryService is DefaultMovementQueryService
    assert registers.DefaultBalanceQueryService is DefaultBalanceQueryService


def test_public_totals_reader_is_read_side_boundary() -> None:
    assert TotalsReader in TotalsEngine.__mro__
