from __future__ import annotations

from dataclasses import dataclass

from accore.platform.integration import (
    ContractVersion,
    IntegrationContractIdentity,
    IntegrationContractKind,
)


@dataclass(frozen=True, slots=True)
class StandardIntegrationContract:
    """Immutable descriptive contract metadata published by Standard Edition."""

    identity: IntegrationContractIdentity
    description: str

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError("Standard Integration contract description must be non-empty.")


STANDARD_INVENTORY_REBUILD_CONTRACT = StandardIntegrationContract(
    identity=IntegrationContractIdentity(
        namespace="standard.processing",
        name="inventory.rebuild",
        version=ContractVersion(1, 0),
        kind=IntegrationContractKind.COMMAND,
    ),
    description="Rebuild Inventory Register Totals and Valuation derived state.",
)

STANDARD_INVENTORY_BALANCE_QUERY_CONTRACT = StandardIntegrationContract(
    identity=IntegrationContractIdentity(
        namespace="standard.reporting",
        name="inventory.balance",
        version=ContractVersion(1, 0),
        kind=IntegrationContractKind.QUERY,
    ),
    description="Execute the Standard Inventory Balance report.",
)

__all__ = [
    "STANDARD_INVENTORY_BALANCE_QUERY_CONTRACT",
    "STANDARD_INVENTORY_REBUILD_CONTRACT",
    "StandardIntegrationContract",
]
