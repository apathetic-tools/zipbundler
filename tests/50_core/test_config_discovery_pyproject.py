# tests/50_core/test_config_discovery_pyproject.py
"""Tests for config discovery with pyproject.toml support.

These tests verify that find_config() correctly skips pyproject.toml files
without [tool.zipbundler] sections and continues searching up the directory
tree.
"""

import os
from pathlib import Path

import pytest

import zipbundler


def test_find_config_skips_pyproject_without_section(tmp_path: Path) -> None:
    """Test that find_config skips pyproject.toml without [tool.zipbundler]."""
    # Create directory structure:
    # parent_dir/
    #   .zipbundler.jsonc (valid config)
    # tmp_path/
    #   pyproject.toml (no [tool.zipbundler])
    parent_dir = tmp_path.parent

    # Create valid config in parent directory
    config_file = parent_dir / ".zipbundler.jsonc"
    config_file.write_text(
        """{
  "packages": ["src/**/*.py"]
}
""",
        encoding="utf-8",
    )

    # Create pyproject.toml without [tool.zipbundler] section in tmp_path
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[tool.poetry]
name = "myproject"
version = "0.1.0"
""",
        encoding="utf-8",
    )

    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        result = zipbundler.find_config(None, tmp_path)
        # Should find parent config, not the pyproject.toml
        assert result is not None
        found_path, found_config = result
        assert found_path == config_file
        assert isinstance(found_config, dict)
    finally:
        os.chdir(original_cwd)
        # Clean up the parent config file
        config_file.unlink()


def test_find_config_uses_pyproject_with_section(tmp_path: Path) -> None:
    """Test that find_config uses pyproject.toml WITH [tool.zipbundler]."""
    # Create pyproject.toml with [tool.zipbundler] section
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[tool.poetry]
name = "myproject"
version = "0.1.0"

[tool.zipbundler]
packages = ["src/**/*.py"]
""",
        encoding="utf-8",
    )

    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        result = zipbundler.find_config(None, tmp_path)
        assert result is not None
        found_path, found_config = result
        assert found_path == pyproject
        assert isinstance(found_config, dict)
        assert "packages" in found_config
    finally:
        os.chdir(original_cwd)


def test_find_config_prefers_jsonc_over_invalid_pyproject(
    tmp_path: Path,
) -> None:
    """Test priority: valid .jsonc is preferred over invalid pyproject.toml."""
    # Create directory structure:
    # tmp_path/
    #   pyproject.toml (no [tool.zipbundler])
    #   .zipbundler.jsonc (valid)

    # Create pyproject.toml without section
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[tool.poetry]
name = "myproject"
""",
        encoding="utf-8",
    )

    # Create valid jsonc config
    jsonc_config = tmp_path / ".zipbundler.jsonc"
    jsonc_config.write_text(
        """{
  "packages": ["src/**/*.py"]
}
""",
        encoding="utf-8",
    )

    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        result = zipbundler.find_config(None, tmp_path)
        assert result is not None
        found_path, _found_config = result
        # .jsonc has higher priority than .toml
        assert found_path == jsonc_config
    finally:
        os.chdir(original_cwd)


def test_explicit_pyproject_without_section_errors(tmp_path: Path) -> None:
    """Test that explicit --config pyproject.toml errors if section missing."""
    # Create pyproject.toml without [tool.zipbundler]
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[tool.poetry]
name = "myproject"
""",
        encoding="utf-8",
    )

    # Explicit config path should error when section is missing
    with pytest.raises(ValueError, match=r"No \[tool\.zipbundler\] section found"):
        zipbundler.find_config(str(pyproject), tmp_path)


def test_find_config_searches_past_multiple_invalid_pyproject(
    tmp_path: Path,
) -> None:
    """Test that find_config searches past multiple invalid pyproject.toml."""
    # Create directory structure:
    # tmp_path/
    #   .zipbundler.jsonc (in parent)
    #   subdir1/
    #     pyproject.toml (no [tool.zipbundler])
    #     subdir2/
    #       pyproject.toml (no [tool.zipbundler])

    # Create valid config at top level
    config_file = tmp_path / ".zipbundler.jsonc"
    config_file.write_text(
        """{
  "packages": ["src/**/*.py"]
}
""",
        encoding="utf-8",
    )

    # Create subdirectories with invalid pyproject.toml files
    subdir1 = tmp_path / "subdir1"
    subdir1.mkdir()
    pyproject1 = subdir1 / "pyproject.toml"
    pyproject1.write_text(
        """[tool.poetry]
name = "project1"
""",
        encoding="utf-8",
    )

    subdir2 = subdir1 / "subdir2"
    subdir2.mkdir()
    pyproject2 = subdir2 / "pyproject.toml"
    pyproject2.write_text(
        """[tool.poetry]
name = "project2"
""",
        encoding="utf-8",
    )

    original_cwd = Path.cwd()
    try:
        os.chdir(subdir2)
        result = zipbundler.find_config(None, subdir2)
        # Should find the top-level config, skipping both pyproject.toml files
        assert result is not None
        found_path, _found_config = result
        assert found_path == config_file
    finally:
        os.chdir(original_cwd)


def test_find_config_prefers_local_valid_pyproject_over_parent(
    tmp_path: Path,
) -> None:
    """Test priority: local valid pyproject.toml beats parent config."""
    # Create directory structure:
    # tmp_path/
    #   .zipbundler.jsonc (parent config)
    #   subdir/
    #     pyproject.toml (with [tool.zipbundler])

    # Create parent config
    parent_config = tmp_path / ".zipbundler.jsonc"
    parent_config.write_text(
        """{
  "packages": ["parent/**/*.py"]
}
""",
        encoding="utf-8",
    )

    # Create subdir with valid pyproject.toml
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    local_pyproject = subdir / "pyproject.toml"
    local_pyproject.write_text(
        """[tool.poetry]
name = "local"

[tool.zipbundler]
packages = ["local/**/*.py"]
""",
        encoding="utf-8",
    )

    original_cwd = Path.cwd()
    try:
        os.chdir(subdir)
        result = zipbundler.find_config(None, subdir)
        # Should prefer local pyproject.toml (closest to cwd)
        assert result is not None
        found_path, found_config = result
        assert found_path == local_pyproject
        assert found_config.get("packages") == ["local/**/*.py"]
    finally:
        os.chdir(original_cwd)


def test_find_config_skips_malformed_pyproject(tmp_path: Path) -> None:
    """Test that find_config skips malformed/corrupted pyproject.toml files."""
    # Create directory structure:
    # tmp_path/
    #   .zipbundler.jsonc (valid fallback)
    #   malformed_pyproject/
    #     pyproject.toml (malformed TOML)

    # Create valid fallback config
    fallback_config = tmp_path / ".zipbundler.jsonc"
    fallback_config.write_text(
        """{
  "packages": ["fallback/**/*.py"]
}
""",
        encoding="utf-8",
    )

    # Create subdir with malformed pyproject.toml
    subdir = tmp_path / "malformed_pyproject"
    subdir.mkdir()
    malformed_toml = subdir / "pyproject.toml"
    # Write invalid TOML (missing closing quote)
    malformed_toml.write_text(
        """[tool.poetry
name = "broken"
""",
        encoding="utf-8",
    )

    original_cwd = Path.cwd()
    try:
        os.chdir(subdir)
        result = zipbundler.find_config(None, subdir)
        # Should skip malformed TOML and find fallback config
        assert result is not None
        found_path, found_config = result
        assert found_path == fallback_config
        assert found_config.get("packages") == ["fallback/**/*.py"]
    finally:
        os.chdir(original_cwd)
