# tests/50_core/test_init_command.py
"""Tests for the init command."""

import os
from pathlib import Path

import zipbundler.main as mod_main


def test_cli_init_command_creates_file(tmp_path: Path) -> None:
    """Test init command creates default config file."""
    # Change to tmp_path
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["init"])

        # Verify exit code is 0
        assert code == 0

        # Verify config file was created
        config_file = tmp_path / ".zipbundler.jsonc"
        assert config_file.exists()

        # Verify content contains expected fields
        content = config_file.read_text(encoding="utf-8")
        assert '"packages"' in content
        assert '"exclude"' in content
        assert '"output"' in content
        assert '"options"' in content
    finally:
        os.chdir(original_cwd)


def test_cli_init_command_custom_output(tmp_path: Path) -> None:
    """Test init command with custom output path."""
    custom_path = tmp_path / "custom.jsonc"

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func(["init", "-o", str(custom_path)])

    # Verify exit code is 0
    assert code == 0

    # Verify config file was created at custom path
    assert custom_path.exists()

    # Verify content contains expected fields
    content = custom_path.read_text(encoding="utf-8")
    assert '"packages"' in content


def test_cli_init_command_existing_file(tmp_path: Path) -> None:
    """Test init command fails when file exists without --force."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create existing config file
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text("existing content")

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["init"])

        # Verify exit code is 1 (error)
        assert code == 1

        # Verify file content was not changed
        assert config_file.read_text(encoding="utf-8") == "existing content"
    finally:
        os.chdir(original_cwd)


def test_cli_init_command_force_overwrite(tmp_path: Path) -> None:
    """Test init command overwrites existing file with --force."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create existing config file
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text("existing content")

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["init", "--force"])

        # Verify exit code is 0
        assert code == 0

        # Verify file content was overwritten
        content = config_file.read_text(encoding="utf-8")
        assert content != "existing content"
        assert '"packages"' in content
    finally:
        os.chdir(original_cwd)
