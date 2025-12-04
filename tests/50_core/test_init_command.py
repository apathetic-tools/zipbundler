# tests/50_core/test_init_command.py
"""Tests for the init command."""

import os
from pathlib import Path

import zipbundler.cli as mod_main


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


def test_cli_init_command_with_cli_preset(tmp_path: Path) -> None:
    """Test init command with CLI preset."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["init", "--preset", "cli"])

        # Verify exit code is 0
        assert code == 0

        # Verify config file was created
        config_file = tmp_path / ".zipbundler.jsonc"
        assert config_file.exists()

        # Verify CLI preset content
        content = config_file.read_text(encoding="utf-8")
        assert '"entry_point"' in content
        assert '"metadata"' in content
        assert "my_package.__main__:main" in content
    finally:
        os.chdir(original_cwd)


def test_cli_init_command_with_library_preset(tmp_path: Path) -> None:
    """Test init command with library preset."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["init", "--preset", "library"])

        # Verify exit code is 0
        assert code == 0

        # Verify config file was created
        config_file = tmp_path / ".zipbundler.jsonc"
        assert config_file.exists()

        # Verify library preset content (no entry point, shebang false)
        content = config_file.read_text(encoding="utf-8")
        assert '"metadata"' in content
        assert '"shebang": false' in content
        assert '"main_guard": false' in content
    finally:
        os.chdir(original_cwd)


def test_cli_init_command_with_minimal_preset(tmp_path: Path) -> None:
    """Test init command with minimal preset."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["init", "--preset", "minimal"])

        # Verify exit code is 0
        assert code == 0

        # Verify config file was created
        config_file = tmp_path / ".zipbundler.jsonc"
        assert config_file.exists()

        # Verify minimal preset content (just packages and output)
        content = config_file.read_text(encoding="utf-8")
        assert '"packages"' in content
        assert '"output"' in content
        # Should not have exclude, options, or metadata
        assert '"exclude"' not in content
        assert '"options"' not in content
        assert '"metadata"' not in content
    finally:
        os.chdir(original_cwd)


def test_cli_init_command_list_presets() -> None:
    """Test init command --list-presets flag."""
    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func(["init", "--list-presets"])

    # Verify exit code is 0
    assert code == 0


def test_cli_init_command_invalid_preset(tmp_path: Path) -> None:
    """Test init command with invalid preset name."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["init", "--preset", "invalid"])

        # Verify exit code is 1 (error)
        assert code == 1

        # Verify config file was not created
        config_file = tmp_path / ".zipbundler.jsonc"
        assert not config_file.exists()
    finally:
        os.chdir(original_cwd)
