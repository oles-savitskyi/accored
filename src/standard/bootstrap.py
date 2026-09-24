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
from accore.platform.posting import RegisterPostingResultCoordinator
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
from standard.definitions.catalogs import standard_catalog_definitions
from standard.registers.inventory import inventory_register_configuration


@dataclass(frozen=True, slots=True)
class _InventoryRegisterPlatformComposition:
    totals_engine: TotalsEngine
    maintenance: TotalsMaintenanceCoordinator
    mutation: RegisterMutationOrchestrator
    movement_validator: MovementValidator
    posting_result_coordinator: RegisterPostingResultCoordinator
    movement_query: MovementQueryService
    balance_query: BalanceQueryService


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
