# tests/50_core/test_build_metadata.py
"""Tests for metadata preservation in zip bundles."""

import os
import zipfile
from pathlib import Path

import zipbundler.cli as mod_main


def test_cli_build_command_with_metadata(tmp_path: Path) -> None:
    """Test build command with metadata in config."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func():\n    pass\n")

        # Create config file with metadata
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  },
  "metadata": {
    "display_name": "My Package",
    "description": "A great Python package",
    "version": "1.0.0",
    "author": "Test Author",
    "license": "MIT"
  }
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()

        # Verify PKG-INFO exists in zip
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert "PKG-INFO" in names

            # Verify PKG-INFO content
            pkg_info = zf.read("PKG-INFO").decode("utf-8")
            assert "Name: My Package" in pkg_info
            assert "Version: 1.0.0" in pkg_info
            assert "Summary: A great Python package" in pkg_info
            assert "Author: Test Author" in pkg_info
            assert "License: MIT" in pkg_info
            assert "Metadata-Version: 2.1" in pkg_info
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_with_partial_metadata(tmp_path: Path) -> None:
    """Test build command with partial metadata in config."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create config file with partial metadata
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  },
  "metadata": {
    "display_name": "My Package",
    "version": "2.0.0"
  }
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()

        # Verify PKG-INFO exists and contains provided fields
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert "PKG-INFO" in names

            # Verify PKG-INFO content
            pkg_info = zf.read("PKG-INFO").decode("utf-8")
            assert "Name: My Package" in pkg_info
            assert "Version: 2.0.0" in pkg_info
            assert "Metadata-Version: 2.1" in pkg_info
            # Should not contain fields that weren't provided
            assert "Summary:" not in pkg_info
            assert "Author:" not in pkg_info
            # License field should have the fallback value
            fallback_license = (
                "License: All rights reserved. See additional license files "
                "if distributed alongside this file for additional terms."
            )
            assert fallback_license in pkg_info
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_without_metadata(tmp_path: Path) -> None:
    """Test build command without metadata in config (no PKG-INFO)."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create config file without metadata
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  }
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()

        # Verify PKG-INFO does NOT exist in zip
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert "PKG-INFO" not in names
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_auto_detects_metadata_from_pyproject(tmp_path: Path) -> None:
    """Test build command auto-detects metadata from pyproject.toml."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create pyproject.toml with metadata
        pyproject_content = """[project]
name = "my-project"
version = "1.5.0"
description = "A project from pyproject.toml"
authors = [
    {name = "pyproject Author"}
]
"""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(pyproject_content, encoding="utf-8")

        # Create config file WITHOUT metadata
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  }
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()

        # Verify PKG-INFO was auto-generated from pyproject.toml
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert "PKG-INFO" in names

            # Verify PKG-INFO content from pyproject.toml
            pkg_info = zf.read("PKG-INFO").decode("utf-8")
            assert "Name: my-project" in pkg_info
            assert "Version: 1.5.0" in pkg_info
            assert "Summary: A project from pyproject.toml" in pkg_info
            assert "Author: pyproject Author" in pkg_info
            # Should have the default fallback license
            fallback_license = (
                "License: All rights reserved. See additional license files "
                "if distributed alongside this file for additional terms."
            )
            assert fallback_license in pkg_info
            assert "Metadata-Version: 2.1" in pkg_info
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_config_metadata_overrides_pyproject(tmp_path: Path) -> None:
    """Test that config metadata takes priority over pyproject.toml."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create pyproject.toml with metadata
        pyproject_content = """[project]
name = "pyproject-name"
version = "1.0.0"
license = {text = "Apache-2.0"}
"""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(pyproject_content, encoding="utf-8")

        # Create config file WITH metadata (should override pyproject.toml)
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  },
  "metadata": {
    "display_name": "Config Package",
    "version": "2.0.0"
  }
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()

        # Verify PKG-INFO uses config metadata
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert "PKG-INFO" in names

            # Verify PKG-INFO uses config metadata (not pyproject.toml)
            pkg_info = zf.read("PKG-INFO").decode("utf-8")
            assert "Name: Config Package" in pkg_info
            assert "Version: 2.0.0" in pkg_info
            assert "Name: pyproject-name" not in pkg_info
            assert "Version: 1.0.0" not in pkg_info
            # License from config is not set, so fallback should be used
            fallback_license = (
                "License: All rights reserved. See additional license files "
                "if distributed alongside this file for additional terms."
            )
            assert fallback_license in pkg_info
    finally:
        os.chdir(original_cwd)
