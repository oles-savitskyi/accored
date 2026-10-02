import ast
from pathlib import Path

PROCESSING_SOURCE = (
    Path(__file__).parents[3] / "src" / "standard" / "processings" / "inventory_rebuild.py"
)
FORBIDDEN_MODULE_PREFIXES = (
    "accore.platform.persistence",
    "accore.platform.storage",
    "accore.platform.runtime",
)
EXPECTED_DEPENDENCIES = {
    "register_maintenance": "TotalsMaintenanceCoordinator",
    "valuation_rebuilder": "ValuationRebuilder",
}


def _parse() -> ast.Module:
    return ast.parse(PROCESSING_SOURCE.read_text(encoding="utf-8"))


def _imported_module_names() -> set[str]:
    modules: set[str] = set()

    for node in ast.walk(_parse()):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)

    return modules


def _constructor_dependencies() -> dict[str, str]:
    for node in _parse().body:
        if isinstance(node, ast.ClassDef) and node.name == "InventoryDerivedStateRebuildProcessing":
            constructor = next(
                method
                for method in node.body
                if isinstance(method, ast.FunctionDef) and method.name == "__init__"
            )
            return {
                argument.arg: ast.unparse(argument.annotation)
                for argument in constructor.args.args[1:]
                if argument.annotation is not None
            }
    raise AssertionError("InventoryDerivedStateRebuildProcessing.__init__ was not found")


def test_inventory_rebuild_processing_does_not_import_persistence_or_runtime() -> None:
    imported_modules = _imported_module_names()

    forbidden = {
        module
        for module in imported_modules
        if any(
            module == prefix or module.startswith(f"{prefix}.")
            for prefix in FORBIDDEN_MODULE_PREFIXES
        )
    }

    assert forbidden == set()


def test_inventory_rebuild_processing_dependencies_are_subsystem_contracts() -> None:
    assert _constructor_dependencies() == EXPECTED_DEPENDENCIES
