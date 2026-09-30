from __future__ import annotations

from dataclasses import dataclass

from accore.platform.configuration import (
    ConfigurationActivator,
    ConfigurationIdentity,
    ConfigurationLoader,
    ConfigurationValidator,
    ConfigurationVersion,
    MetadataResolver,
    RuntimeConfigurationBinding,
    RuntimeConfigurationContext,
)
from accore.platform.metadata import MetadataCompiler
from accore.platform.persistence import RegisterFactPersistence
from accore.platform.posting import (
    CompositePostingResultCoordinator,
    RegisterPostingResultCoordinator,
    ValuationPostingCoordinator,
)
from accore.platform.registers import (
    BalanceQueryService,
    DefaultBalanceQueryService,
    DefaultMovementQueryService,
    DefaultMovementValidator,
    DefaultTotalsEngine,
    DefaultTotalsMaintenanceCoordinator,
    MaintenanceOutcome,
    MappingRegisterPostingContractResolver,
    MovementQueryService,
    MovementValidator,
    RegisterMutationOrchestrator,
    RegisterOperationDomainRegistry,
    TotalsEngine,
    TotalsMaintenanceCoordinator,
)
from accore.platform.runtime.resolution import RuntimeResolver
from accore.platform.valuation import (
    DefaultCostTotalsEngine,
    DefaultValuationCoordinator,
    DefaultValuationPlanValidator,
    DefaultValuationPreparationStateFactory,
    DefaultValuationRebuilder,
    FIFOValuationMethod,
    ValuationEngine,
)
from standard.definitions.catalogs import standard_catalog_definitions
from standard.registers.inventory import inventory_register_configuration
from standard.valuation import (
    InventoryValuationInputProvider,
    InventoryValuationKeyMapper,
    StandardValuationFactPersistence,
    StandardValuationOperationPersistence,
    StandardValuationResultPersistence,
)


@dataclass(frozen=True, slots=True)
class _InventoryRegisterPlatformComposition:
    totals_engine: TotalsEngine
    maintenance: TotalsMaintenanceCoordinator
    mutation: RegisterMutationOrchestrator
    movement_validator: MovementValidator
    posting_result_coordinator: RegisterPostingResultCoordinator
    movement_query: MovementQueryService
    balance_query: BalanceQueryService


@dataclass(frozen=True, slots=True)
class _InventoryPostingPlatformComposition:
    register: _InventoryRegisterPlatformComposition
    valuation_engine: ValuationEngine
    valuation_lifecycle: DefaultValuationCoordinator
    valuation_posting: ValuationPostingCoordinator
    valuation_rebuilder: DefaultValuationRebuilder
    posting_result_coordinator: CompositePostingResultCoordinator


class StandardConfigurationBootstrap:
    """Bootstrap the Standard Configuration runtime context."""

    def initialize(self) -> tuple[RuntimeConfigurationContext, RuntimeResolver]:
        """Initialize the Standard Configuration runtime context."""
        loader = ConfigurationLoader(MetadataCompiler())
        candidate = loader.load(
            standard_catalog_definitions(),
            identity=ConfigurationIdentity("standard"),
            version=ConfigurationVersion(1),
        )

        validator = ConfigurationValidator()
        validator.validate(candidate)

        active = ConfigurationActivator().activate(candidate)

        binding = RuntimeConfigurationBinding()
        binding.bind(active)

        context = binding.acquire()
        resolver = RuntimeResolver(MetadataResolver())

        return context, resolver

    def compose_inventory_register_platform(
        self,
        persistence: RegisterFactPersistence,
    ) -> _InventoryRegisterPlatformComposition:
        """Compose Inventory semantics over the generic Register Platform."""
        configuration = inventory_register_configuration()
        totals_engine = DefaultTotalsEngine((configuration.totals_definition,))
        maintenance = DefaultTotalsMaintenanceCoordinator(totals_engine, persistence)
        contract_resolver = MappingRegisterPostingContractResolver(
            {configuration.register_identity: configuration.posting_contract}
        )
        movement_validator = DefaultMovementValidator(contract_resolver)
        mutation = RegisterMutationOrchestrator(
            persistence=persistence,
            totals=maintenance,
            domains=RegisterOperationDomainRegistry(),
            validator=movement_validator,
        )
        posting_result_coordinator = RegisterPostingResultCoordinator(
            mutation=mutation,
            persistence=persistence,
            register_identities=(configuration.register_identity,),
        )

        initialization = maintenance.rebuild(configuration.register_identity)
        if initialization.outcome is not MaintenanceOutcome.SUCCESS:
            raise RuntimeError(
                "Inventory register composition could not initialize Totals: "
                f"outcome={initialization.outcome.value!r}, "
                f"state={initialization.state!r}"
            )

        return _InventoryRegisterPlatformComposition(
            totals_engine=totals_engine,
            maintenance=maintenance,
            mutation=mutation,
            movement_validator=movement_validator,
            posting_result_coordinator=posting_result_coordinator,
            movement_query=DefaultMovementQueryService(persistence),
            balance_query=DefaultBalanceQueryService(totals_engine),
        )

    def compose_inventory_posting_platform(
        self,
        register_persistence: RegisterFactPersistence,
        valuation_fact_persistence: StandardValuationFactPersistence,
        valuation_result_persistence: StandardValuationResultPersistence,
    ) -> _InventoryPostingPlatformComposition:
        """Compose Inventory Register and Valuation into one posting coordinator."""
        register = self.compose_inventory_register_platform(register_persistence)
        fact_persistence = valuation_fact_persistence
        result_persistence = valuation_result_persistence

        key_mapper = InventoryValuationKeyMapper()
        input_provider = InventoryValuationInputProvider(key_mapper)
        operation_persistence = StandardValuationOperationPersistence()
        preparation_state_factory = DefaultValuationPreparationStateFactory(fact_persistence)
        valuation_engine = ValuationEngine(
            input_provider=input_provider,
            preparation_state_factory=preparation_state_factory,
            method=FIFOValuationMethod(),
        )
        totals_engine = DefaultCostTotalsEngine()
        validator = DefaultValuationPlanValidator(fact_persistence)
        valuation_rebuilder = DefaultValuationRebuilder(
            fact_persistence=fact_persistence,
            result_persistence=result_persistence,
            totals_engine=totals_engine,
        )
        lifecycle = DefaultValuationCoordinator(
            fact_persistence=fact_persistence,
            operation_persistence=operation_persistence,
            result_persistence=result_persistence,
            totals_engine=totals_engine,
            validator=validator,
            rebuilder=valuation_rebuilder,
        )
        valuation_posting = ValuationPostingCoordinator(
            valuation_engine,
            lifecycle,
        )
        posting_result_coordinator = CompositePostingResultCoordinator(
            (register.posting_result_coordinator, valuation_posting)
        )

        return _InventoryPostingPlatformComposition(
            register=register,
            valuation_engine=valuation_engine,
            valuation_lifecycle=lifecycle,
            valuation_posting=valuation_posting,
            valuation_rebuilder=valuation_rebuilder,
            posting_result_coordinator=posting_result_coordinator,
        )
