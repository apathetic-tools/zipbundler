# tests/10_lint/test_lint__no_from_app_imports.py
"""Custom lint rule: Enforce `import <mod> as mod_<mod>` pattern in tests.

This test acts as a "poor person's linter" since we can't create custom ruff rules yet.
It enforces that ALL test files use
`import <package>.<module> as mod_<module>` format
instead of `from <package>.<module> import ...` when importing from our project.

CRITICAL: This rule applies to ALL imports from our project, including private
functions (those starting with _). There are NO exceptions (except TYPE_CHECKING).

Why this matters:
- runtime_swap: Tests can run against either installed package or stitched
  script. The `import ... as mod_*` pattern ensures the module object
  is available for runtime swapping.
- patch_everywhere: Predictive patching requires module objects to be available
  at the module level. Using `from ... import` breaks this because the imported
  function is no longer associated with its module object.

If you need to test private functions, import the module and access the function
via the module object: `mod_utils._private_function()` instead of importing
the function directly.
"""

import ast
from pathlib import Path

from tests.utils import DISALLOWED_PACKAGES


class ImportChecker(ast.NodeVisitor):
    """Visitor to check for disallowed imports and track TYPE_CHECKING context."""

    def __init__(self) -> None:
        self.bad_imports: list[ast.ImportFrom] = []
        self.in_type_checking = False

    def visit_If(self, node: ast.If) -> None:
        # Check if this is an if TYPE_CHECKING block
        if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
            old_state = self.in_type_checking
            self.in_type_checking = True
            for stmt in node.body:
                self.visit(stmt)
            self.in_type_checking = old_state
        else:
            self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if (
            node.module
            and any(node.module.startswith(pkg) for pkg in DISALLOWED_PACKAGES)
            and not self.in_type_checking
        ):
            self.bad_imports.append(node)
        self.generic_visit(node)


def test_no_app_from_imports() -> None:
    """Enforce `import <mod> as mod_<mod>` pattern for all project imports in tests/.

    This is a custom lint rule implemented as a pytest test because we can't
    create custom ruff rules yet. It ensures all files in tests/ (including
    conftest.py, tests/utils/, etc.) use the module-level import pattern required
    for runtime_swap and patch_everywhere to work correctly.

    Exception: Imports inside `if TYPE_CHECKING:` blocks are allowed for type
    annotations only.
    """
    tests_dir = Path(__file__).parents[1]  # tests/ directory (not project root)
    bad_files: list[Path] = []

    for path in tests_dir.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        checker = ImportChecker()
        checker.visit(tree)
        if checker.bad_imports:
            # NO EXCEPTIONS (except TYPE_CHECKING): All imports from our
            # project must use module-level imports. This includes private
            # functions - use mod_module._private_function() instead
            bad_files.append(path)

    if bad_files:
        packages_str = ", ".join(DISALLOWED_PACKAGES)
        print(
            "\n❌ Disallowed `from <package>.<module> import ...`"
            " imports found in test files:",
        )
        print(f"   Disallowed packages: {packages_str}")
        for path in bad_files:
            print(f"  - {path}")
        print(
            "\nAll test files MUST use module-level imports:"
            f"\n  ❌ from {DISALLOWED_PACKAGES[0]}.module import function"
            f"\n  ✅ import {DISALLOWED_PACKAGES[0]}.module as mod_module"
            "\n"
            "\nThis pattern is required for:"
            "\n  - runtime_swap: Module objects needed for runtime mode switching"
            "\n  - patch_everywhere: Predictive patching requires module-level access"
            "\n"
            "\nFor private functions, access via module object:"
            "\n  ✅ mod_module._private_function()"
            "\n  ❌ from module import _private_function"
        )
        xmsg = (
            f"{len(bad_files)} test file(s) use disallowed"
            f" `from {packages_str}.*` imports."
            " All test imports from these packages must use"
            f" `import <package>.<module> as mod_<module>` format."
        )
        raise AssertionError(xmsg)
