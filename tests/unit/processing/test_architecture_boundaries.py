import ast
from pathlib import Path

PROCESSING_PACKAGE = Path(__file__).parents[3] / "src" / "accore" / "platform" / "processing"
FORBIDDEN_MODULE_PREFIXES = (
    "accore.platform.persistence",
    "accore.platform.storage",
    "accore.platform.registers",
    "accore.platform.valuation",
    "accore.platform.posting",
    "accore.platform.runtime",
    "standard",
)
FORBIDDEN_PUBLIC_NAMES = {
    "ProcessingRegistry",
    "ProcessingPipeline",
    "Workflow",
    "WorkflowStep",
    "Job",
    "Scheduler",
    "CommandBus",
    "ServiceContainer",
    "TransactionManager",
}


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _imported_module_names(path: Path) -> set[str]:
    modules: set[str] = set()

    for node in ast.walk(_parse(path)):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)

    return modules


def _public_names(path: Path) -> set[str]:
    for node in _parse(path).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    return {
                        element.value
                        for element in node.value.elts
                        if isinstance(element, ast.Constant) and isinstance(element.value, str)
                    }
    return set()


def test_platform_processing_does_not_import_forbidden_subsystems() -> None:
    imported_modules = {
        module
        for path in PROCESSING_PACKAGE.glob("*.py")
        for module in _imported_module_names(path)
    }

    forbidden = {
        module
        for module in imported_modules
        if any(
            module == prefix or module.startswith(f"{prefix}.")
            for prefix in FORBIDDEN_MODULE_PREFIXES
        )
    }

    assert forbidden == set()


def test_processing_public_api_does_not_expose_framework_infrastructure() -> None:
    public_names = _public_names(PROCESSING_PACKAGE / "__init__.py")

    assert FORBIDDEN_PUBLIC_NAMES.isdisjoint(public_names)
