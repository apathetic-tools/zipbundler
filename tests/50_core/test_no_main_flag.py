# tests/50_core/test_no_main_flag.py
"""Tests for --no-main CLI flag and insert_main config option."""

import argparse
import zipfile
from pathlib import Path

import pytest

import zipbundler.commands.zipapp_style as mod_zipapp_cmd


@pytest.fixture
def test_package(tmp_path: Path) -> Path:
    """Create a simple test package."""
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "main.py").write_text("def main():\n    print('Hello')\n")
    return pkg_dir


def test_zipapp_style_with_no_main_flag(
    test_package: Path,
    tmp_path: Path,
) -> None:
    """Test that --no-main flag prevents __main__.py creation."""
    output = tmp_path / "app.pyz"

    args = argparse.Namespace(
        include=str(test_package),
        output=str(output),
        entry_point=False,  # Simulates --no-main
        shebang=None,
        compress=False,
        compression_level=None,
        force=False,
        log_level="info",
    )

    result = mod_zipapp_cmd.handle_zipapp_style_command(args)

    assert result == 0
    assert output.exists()

    # Verify __main__.py was NOT created
    with zipfile.ZipFile(output, "r") as zf:
        assert "__main__.py" not in zf.namelist()


def test_zipapp_style_with_main_flag(
    test_package: Path,
    tmp_path: Path,
) -> None:
    """Test that --main flag creates __main__.py."""
    output = tmp_path / "app.pyz"

    args = argparse.Namespace(
        include=str(test_package),
        output=str(output),
        entry_point="mypackage.main:main",  # Simulates --main
        shebang=None,
        compress=False,
        compression_level=None,
        force=False,
        log_level="info",
    )

    result = mod_zipapp_cmd.handle_zipapp_style_command(args)

    assert result == 0
    assert output.exists()

    # Verify __main__.py was created
    with zipfile.ZipFile(output, "r") as zf:
        assert "__main__.py" in zf.namelist()


def test_zipapp_style_without_main_flag(
    test_package: Path,
    tmp_path: Path,
) -> None:
    """Test that omitting --main flag doesn't create __main__.py."""
    output = tmp_path / "app.pyz"

    args = argparse.Namespace(
        include=str(test_package),
        output=str(output),
        entry_point=None,  # Not specified (no --main or --no-main)
        shebang=None,
        compress=False,
        compression_level=None,
        force=False,
        log_level="info",
    )

    result = mod_zipapp_cmd.handle_zipapp_style_command(args)

    assert result == 0
    assert output.exists()

    # Verify __main__.py was NOT created
    with zipfile.ZipFile(output, "r") as zf:
        assert "__main__.py" not in zf.namelist()
