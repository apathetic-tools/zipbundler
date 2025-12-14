# tests/50_core/test_api.py
"""Tests for programmatic API functions."""

import os
import zipfile
from pathlib import Path

import pytest

import zipbundler


def test_create_archive_basic(tmp_path: Path) -> None:
    """Test create_archive with basic parameters."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "app.pyz"

    result = zipbundler.create_archive(
        source=pkg_dir,
        target=output,
        interpreter="/usr/bin/env python3",
        main="mypackage.module:func",
        compressed=True,
    )

    assert result == output
    assert output.exists()

    # Verify zip file is valid
    with zipfile.ZipFile(output, "r") as zf:
        names = zf.namelist()
        assert any("mypackage/__init__.py" in name for name in names)
        assert any("mypackage/module.py" in name for name in names)
        assert "__main__.py" in names

    # Verify shebang
    interpreter = zipbundler.get_interpreter(output)
    assert interpreter == "/usr/bin/env python3"


def test_create_archive_default_target(tmp_path: Path) -> None:
    """Test create_archive with default target."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    result = zipbundler.create_archive(source=pkg_dir)

    expected = pkg_dir.with_suffix(".pyz")
    assert result == expected
    assert expected.exists()


def test_create_archive_no_compression(tmp_path: Path) -> None:
    """Test create_archive without compression."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    output = tmp_path / "app.pyz"

    zipbundler.create_archive(
        source=pkg_dir,
        target=output,
        compressed=False,
    )

    assert output.exists()


def test_create_archive_source_not_found(tmp_path: Path) -> None:
    """Test create_archive raises FileNotFoundError for non-existent source."""
    non_existent = tmp_path / "nonexistent"

    with pytest.raises(FileNotFoundError, match="Source not found"):
        zipbundler.create_archive(source=non_existent)


def test_build_zip_with_packages(tmp_path: Path) -> None:
    """Test build_zip with packages parameter."""
    # Create a test package
    pkg_dir = tmp_path / "src" / "mypackage"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "dist" / "bundle.pyz"

    result = zipbundler.build_zip(
        packages=[str(pkg_dir)],
        output_path=output,
    )

    assert result.output_path == output
    assert output.exists()
    assert result.file_count > 0
    assert result.size_bytes > 0
    assert result.duration >= 0

    # Verify zip file is valid
    with zipfile.ZipFile(output, "r") as zf:
        names = zf.namelist()
        assert any("mypackage/__init__.py" in name for name in names)
        assert any("mypackage/module.py" in name for name in names)


def test_build_zip_with_config(tmp_path: Path) -> None:
    """Test build_zip with config_path parameter."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a test package
        pkg_dir = tmp_path / "src" / "mypackage"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")

        # Create a valid config file
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.pyz"
  }
}
""",
            encoding="utf-8",
        )

        result = zipbundler.build_zip(config_path=str(config_file))

        output = tmp_path / "dist" / "bundle.pyz"
        assert result.output_path == output
        assert output.exists()
    finally:
        os.chdir(original_cwd)


def test_build_zip_with_entry_point(tmp_path: Path) -> None:
    """Test build_zip with entry_point parameter."""
    # Create a test package
    pkg_dir = tmp_path / "src" / "mypackage"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "__main__.py").write_text("def main():\n    pass\n")

    output = tmp_path / "dist" / "bundle.pyz"

    result = zipbundler.build_zip(
        packages=[str(pkg_dir)],
        output_path=output,
        entry_point="mypackage.__main__:main",
    )

    assert result.output_path == output
    assert output.exists()

    # Verify __main__.py is in the zip
    with zipfile.ZipFile(output, "r") as zf:
        assert "__main__.py" in zf.namelist()


def test_build_zip_with_exclude(tmp_path: Path) -> None:
    """Test build_zip with exclude patterns."""
    # Create a test package with test files
    pkg_dir = tmp_path / "src" / "mypackage"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")
    (pkg_dir / "test_module.py").write_text("def test_func():\n    pass\n")

    output = tmp_path / "dist" / "bundle.pyz"

    result = zipbundler.build_zip(
        packages=[str(pkg_dir)],
        output_path=output,
        exclude=["**/test_*.py"],
    )

    assert result.output_path == output
    assert output.exists()

    # Verify test files are excluded
    with zipfile.ZipFile(output, "r") as zf:
        names = zf.namelist()
        assert any("mypackage/__init__.py" in name for name in names)
        assert any("mypackage/module.py" in name for name in names)
        assert not any("mypackage/test_module.py" in name for name in names)


def test_build_zip_with_compression(tmp_path: Path) -> None:
    """Test build_zip with compression options."""
    # Create a test package
    pkg_dir = tmp_path / "src" / "mypackage"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "__init__.py").write_text("")

    output = tmp_path / "dist" / "bundle.pyz"

    result = zipbundler.build_zip(
        packages=[str(pkg_dir)],
        output_path=output,
        compression="deflate",
        compression_level=9,
    )

    assert result.output_path == output
    assert output.exists()


def test_build_zip_with_metadata(tmp_path: Path) -> None:
    """Test build_zip with metadata."""
    # Create a test package
    pkg_dir = tmp_path / "src" / "mypackage"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "__init__.py").write_text("")

    output = tmp_path / "dist" / "bundle.pyz"

    result = zipbundler.build_zip(
        packages=[str(pkg_dir)],
        output_path=output,
        metadata={
            "display_name": "My Package",
            "version": "1.0.0",
            "description": "A test package",
        },
    )

    assert result.output_path == output
    assert output.exists()

    # Verify PKG-INFO is in the zip
    with zipfile.ZipFile(output, "r") as zf:
        assert "PKG-INFO" in zf.namelist()


def test_build_zip_no_packages(tmp_path: Path) -> None:
    """Test build_zip raises ValueError when no packages provided."""
    output = tmp_path / "dist" / "bundle.pyz"

    with pytest.raises(ValueError, match="packages must be provided"):
        zipbundler.build_zip(output_path=output)


def test_get_interpreter_exported(tmp_path: Path) -> None:
    """Test that get_interpreter is exported from zipbundler."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    output = tmp_path / "app.pyz"

    zipbundler.create_archive(
        source=pkg_dir,
        target=output,
        interpreter="/usr/bin/env python3",
    )

    # Test that get_interpreter is accessible
    interpreter = zipbundler.get_interpreter(output)
    assert interpreter == "/usr/bin/env python3"


def test_validate_config_valid(tmp_path: Path) -> None:
    """Test load_and_validate_config with valid config."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a valid config file
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.pyz"
  }
}
""",
            encoding="utf-8",
        )

        result = zipbundler.load_and_validate_config()
        assert result is not None
        _config_path, _config, validation = result
        assert validation.valid is True
    finally:
        os.chdir(original_cwd)


def test_validate_config_invalid(tmp_path: Path) -> None:
    """Test load_and_validate_config with invalid config."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create an invalid config file (missing packages)
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "output": {
    "path": "dist/bundle.pyz"
  }
}
""",
            encoding="utf-8",
        )

        try:
            result = zipbundler.load_and_validate_config()
            # If it doesn't raise, check validation result
            if result is not None:
                _config_path, _config, validation = result
                assert validation.valid is False
        except ValueError:
            # Expected: validation failed
            pass
    finally:
        os.chdir(original_cwd)


def test_load_config_exported(tmp_path: Path) -> None:
    """Test that load_config is exported from zipbundler."""
    # Create a config file
    config_file = tmp_path / ".zipbundler.jsonc"
    config_file.write_text(
        """{
  "packages": ["src/mypackage/**/*.py"]
}
""",
        encoding="utf-8",
    )

    config = zipbundler.load_config(config_file)
    assert isinstance(config, dict)
    assert "packages" in config


def test_find_config_exported(tmp_path: Path) -> None:
    """Test that find_config is exported from zipbundler."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a config file
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"]
}
""",
            encoding="utf-8",
        )

        result = zipbundler.find_config(None, tmp_path)
        assert result is not None
        found_path, found_config = result
        assert found_path == config_file
        assert isinstance(found_config, dict)
        assert "packages" in found_config
    finally:
        os.chdir(original_cwd)
