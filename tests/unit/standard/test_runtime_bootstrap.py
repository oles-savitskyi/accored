from accore.platform.metadata import CatalogMetadata
from accore.platform.runtime.catalog import CatalogRuntime
from accore.platform.runtime.resolution import RuntimeResolver
from standard.bootstrap import StandardConfigurationBootstrap
from standard.definitions.assortment import ASSORTMENT_ID


def test_standard_bootstrap_produces_resolvable_runtime_context() -> None:
    context, resolver = StandardConfigurationBootstrap().initialize()

    assert isinstance(resolver, RuntimeResolver)

    runtime = resolver.resolve(context, ASSORTMENT_ID)

    assert isinstance(runtime, CatalogRuntime)

    metadata = runtime.metadata

    assert isinstance(metadata, CatalogMetadata)
    assert metadata.identifier == ASSORTMENT_ID
    assert metadata.name == "Assortment"
