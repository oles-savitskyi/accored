from accore.platform.foundation import Identifier
from accore.platform.metadata import CatalogMetadata
from accore.platform.runtime.catalog import CatalogRuntime
from accore.platform.runtime.resolution import RuntimeResolver
from standard.bootstrap import StandardConfigurationBootstrap
from standard.definitions.assortment import ASSORTMENT_ID


def test_standard_bootstrap_produces_resolvable_runtime_context() -> None:
    registry, resolver = StandardConfigurationBootstrap().initialize()

    assert ASSORTMENT_ID != Identifier.new()

    assert registry.contains(ASSORTMENT_ID)
    assert isinstance(resolver, RuntimeResolver)

    runtime = resolver.resolve(ASSORTMENT_ID)

    assert isinstance(runtime, CatalogRuntime)

    metadata = runtime.metadata

    assert isinstance(metadata, CatalogMetadata)
    assert metadata.identifier == ASSORTMENT_ID
    assert metadata.name == "Assortment"
