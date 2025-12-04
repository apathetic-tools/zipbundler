# tests/50_core/test_build_dependency_resolution.py
"""Tests for dependency resolution in build command."""

import os
import zipfile
from pathlib import Path

import zipbundler.cli as mod_main
import zipbundler.commands.build as mod_build


def test_resolve_installed_package_apathetic_utils() -> None:
    """Test resolving apathetic_utils as an installed package."""
    # apathetic_utils should be installed in the test environment
    result = mod_build._resolve_installed_package("apathetic_utils")  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    assert result is not None
    assert result.exists()
    assert result.is_dir()
    # Should contain __init__.py or other Python files
    assert (result / "__init__.py").exists() or any(
        (result / f).is_file() and str(f).endswith(".py") for f in result.iterdir()
    )


def test_resolve_installed_package_nonexistent() -> None:
    """Test resolving a non-existent package returns None."""
    result = mod_build._resolve_installed_package("nonexistent_package_xyz_123")  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    assert result is None


def test_resolve_package_pattern_with_installed_package(tmp_path: Path) -> None:
    """Test resolving a package pattern that includes an installed package."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Try to resolve apathetic_utils as an installed package
        resolved = mod_build._resolve_package_pattern("apathetic_utils", tmp_path)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        assert len(resolved) > 0
        assert all(p.exists() and p.is_dir() for p in resolved)
    finally:
        os.chdir(original_cwd)


def test_resolve_package_pattern_path_takes_precedence(tmp_path: Path) -> None:
    """Test that local paths take precedence over installed packages."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a local directory with a name that might match an installed package
        local_package = tmp_path / "apathetic_utils"
        local_package.mkdir()
        (local_package / "__init__.py").write_text("")

        # Should resolve to local path, not installed package
        resolved = mod_build._resolve_package_pattern("apathetic_utils", tmp_path)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        assert len(resolved) > 0
        # Should resolve to the local path (tmp_path/apathetic_utils)
        assert any(p.samefile(local_package) for p in resolved)
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_with_installed_package(tmp_path: Path) -> None:
    """Test build command with an installed package in config."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a local package
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create config file that includes both local and installed packages
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": [
    "src/mypackage/**/*.py",
    "apathetic_utils"
  ],
  "output": {
    "path": "dist/bundle.zip"
  }
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()

        # Verify zip file contains the local package
        # (installed package inclusion is tested in other tests)
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            # Should contain local package
            assert any("mypackage" in name for name in names), (
                f"Expected mypackage in {names}"
            )
    finally:
        os.chdir(original_cwd)


def test_resolve_package_pattern_path_with_slash_not_package(tmp_path: Path) -> None:
    """Test that patterns with slashes are not treated as package names."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Pattern with slash should not try to resolve as installed package
        resolved = mod_build._resolve_package_pattern(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
            "some/nonexistent/package", tmp_path
        )
        # Should not resolve (path doesn't exist and not treated as package name)
        assert len(resolved) == 0
    finally:
        os.chdir(original_cwd)


def test_resolve_package_pattern_relative_path_not_package(tmp_path: Path) -> None:
    """Test that relative paths starting with . are not treated as package names."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Pattern starting with . should not try to resolve as installed package
        resolved = mod_build._resolve_package_pattern("./nonexistent", tmp_path)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        # Should not resolve (path doesn't exist and not treated as package name)
        assert len(resolved) == 0
    finally:
        os.chdir(original_cwd)
