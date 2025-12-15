# tests/50_core/test_utils_module_structure.py
"""Tests for the utils submodule structure and public API organization.

This module verifies that:
1. The utils package properly exports all public APIs
2. Each submodule contains the expected functions
3. The module organization follows the design pattern of one file per public API
"""

import zipbundler.utils as mod_utils
import zipbundler.utils.compress as mod_compress
import zipbundler.utils.discovered_packages as mod_discovered
import zipbundler.utils.excludes as mod_excludes
import zipbundler.utils.gitignore as mod_gitignore
import zipbundler.utils.includes as mod_includes


class TestUtilsModuleImports:
    """Test that the utils module can be imported in different ways."""

    def test_import_from_utils_package(self) -> None:
        """Test importing functions from zipbundler.utils."""
        # Just verify the functions are accessible and callable
        assert callable(mod_utils.resolve_includes)
        assert callable(mod_utils.resolve_excludes)
        assert callable(mod_utils.resolve_compress)
        assert callable(mod_utils.load_gitignore_patterns)
        assert callable(mod_utils.resolve_gitignore)
        assert callable(mod_utils.discover_installed_packages_roots)

    def test_import_submodules_directly(self) -> None:
        """Test importing submodules directly."""
        assert hasattr(mod_includes, "resolve_includes")
        assert hasattr(mod_excludes, "resolve_excludes")
        assert hasattr(mod_compress, "resolve_compress")
        assert hasattr(mod_gitignore, "load_gitignore_patterns")
        assert hasattr(mod_discovered, "discover_installed_packages_roots")

    def test_import_specific_functions_from_submodules(self) -> None:
        """Test that functions are accessible from submodules."""
        # Access functions through their module objects
        assert callable(mod_includes.resolve_includes)
        assert callable(mod_excludes.resolve_excludes)
        assert callable(mod_compress.resolve_compress)


class TestUtilsPackageStructure:
    """Test the structure and organization of the utils package."""

    def test_utils_package_exports_all_public_apis(self) -> None:
        """Test that utils.__init__ exports all public APIs."""
        expected_exports = {
            # includes
            "make_include_resolved",
            "parse_include_with_dest",
            "resolve_includes",
            # excludes
            "make_exclude_resolved",
            "resolve_excludes",
            # gitignore
            "load_gitignore_patterns",
            "resolve_gitignore",
            # compress
            "resolve_compress",
            # discovered_packages
            "discover_installed_packages_roots",
        }

        actual_exports = set(mod_utils.__all__)
        assert expected_exports == actual_exports, (
            f"Expected {expected_exports}, got {actual_exports}"
        )

    def test_utils_submodules_contain_expected_functions(self) -> None:
        """Test that each submodule contains its expected public functions."""
        # includes.py
        assert hasattr(mod_includes, "make_include_resolved")
        assert hasattr(mod_includes, "parse_include_with_dest")
        assert hasattr(mod_includes, "resolve_includes")

        # excludes.py
        assert hasattr(mod_excludes, "make_exclude_resolved")
        assert hasattr(mod_excludes, "resolve_excludes")

        # gitignore.py
        assert hasattr(mod_gitignore, "load_gitignore_patterns")
        assert hasattr(mod_gitignore, "resolve_gitignore")

        # compress.py
        assert hasattr(mod_compress, "resolve_compress")

        # discovered_packages.py
        assert hasattr(mod_discovered, "discover_installed_packages_roots")

    def test_public_apis_are_callable(self) -> None:
        """Test that all exported public APIs are callable."""
        for name in mod_utils.__all__:
            func = getattr(mod_utils, name)
            assert callable(func), (
                f"{name} is exported but not callable (type: {type(func).__name__})"
            )

    def test_imported_functions_are_from_correct_modules(self) -> None:
        """Test that functions are imported from their defining modules."""
        # Check that functions come from the expected modules
        assert mod_utils.resolve_includes.__module__ == "zipbundler.utils.includes"
        assert mod_utils.make_include_resolved.__module__ == "zipbundler.utils.includes"
        assert (
            mod_utils.parse_include_with_dest.__module__ == "zipbundler.utils.includes"
        )

        assert mod_utils.resolve_excludes.__module__ == "zipbundler.utils.excludes"
        assert mod_utils.make_exclude_resolved.__module__ == "zipbundler.utils.excludes"

        assert (
            mod_utils.load_gitignore_patterns.__module__ == "zipbundler.utils.gitignore"
        )
        assert mod_utils.resolve_gitignore.__module__ == "zipbundler.utils.gitignore"

        assert mod_utils.resolve_compress.__module__ == "zipbundler.utils.compress"

        assert (
            mod_utils.discover_installed_packages_roots.__module__
            == "zipbundler.utils.discovered_packages"
        )

    def test_no_private_functions_exported_from_utils_package(self) -> None:
        """Test that only public functions (not starting with _) are exported."""
        for name in mod_utils.__all__:
            assert not name.startswith("_"), (
                f"Private function '{name}' should not be exported from utils.__all__"
            )

    def test_module_docstrings_are_present(self) -> None:
        """Test that each utils submodule has a docstring."""
        modules = [
            mod_includes,
            mod_excludes,
            mod_gitignore,
            mod_compress,
            mod_discovered,
        ]
        for mod in modules:
            assert mod.__doc__ is not None, f"Module {mod.__name__} missing docstring"
            assert len(mod.__doc__) > 0, f"Module {mod.__name__} has empty docstring"

    def test_public_functions_have_docstrings(self) -> None:
        """Test that all public functions have proper docstrings."""
        for name in mod_utils.__all__:
            func = getattr(mod_utils, name)
            assert func.__doc__ is not None, f"Function {name} missing docstring"
            # Check that docstring is not just whitespace
            assert len(func.__doc__.strip()) > 0, f"Function {name} has empty docstring"
            # Check that docstring contains at least one section
            assert "Args:" in func.__doc__ or "Returns:" in func.__doc__, (
                f"Function {name} docstring incomplete (missing Args: or Returns:)"
            )
