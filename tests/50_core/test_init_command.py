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


def test_cli_init_command_auto_detects_metadata_from_pyproject(tmp_path: Path) -> None:
    """Test init command auto-detects metadata from pyproject.toml."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create pyproject.toml with metadata
        pyproject_content = """[project]
name = "test-package"
version = "1.2.3"
description = "A test package description"
authors = [
    {name = "Test Author"}
]
license = {text = "MIT"}
"""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(pyproject_content, encoding="utf-8")

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["init"])

        # Verify exit code is 0
        assert code == 0

        # Verify config file was created
        config_file = tmp_path / ".zipbundler.jsonc"
        assert config_file.exists()

        # Verify metadata was auto-detected and injected
        content = config_file.read_text(encoding="utf-8")
        assert '"metadata"' in content
        assert '"display_name": "test-package"' in content
        assert '"version": "1.2.3"' in content
        assert '"description": "A test package description"' in content
        assert '"author": "Test Author"' in content
        assert '"license": "MIT"' in content
    finally:
        os.chdir(original_cwd)


def test_cli_init_command_auto_detects_partial_metadata_from_pyproject(
    tmp_path: Path,
) -> None:
    """Test init command auto-detects partial metadata from pyproject.toml."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create pyproject.toml with partial metadata
        pyproject_content = """[project]
name = "partial-package"
version = "0.5.0"
"""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(pyproject_content, encoding="utf-8")

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["init"])

        # Verify exit code is 0
        assert code == 0

        # Verify config file was created
        config_file = tmp_path / ".zipbundler.jsonc"
        assert config_file.exists()

        # Verify partial metadata was auto-detected
        content = config_file.read_text(encoding="utf-8")
        assert '"metadata"' in content
        assert '"display_name": "partial-package"' in content
        assert '"version": "0.5.0"' in content
        # Should not have description, author, or license
        assert '"description"' not in content or '"description": null' in content
    finally:
        os.chdir(original_cwd)


def test_cli_init_command_no_metadata_when_no_pyproject(tmp_path: Path) -> None:
    """Test init command does not add metadata when pyproject.toml doesn't exist."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["init", "--preset", "basic"])

        # Verify exit code is 0
        assert code == 0

        # Verify config file was created
        config_file = tmp_path / ".zipbundler.jsonc"
        assert config_file.exists()

        # Verify metadata section is still commented (not auto-detected)
        content = config_file.read_text(encoding="utf-8")
        # For basic preset, metadata should be commented out
        assert '// "metadata":' in content or '"metadata":' not in content
    finally:
        os.chdir(original_cwd)


def test_cli_init_command_auto_detects_entry_point_from_pyproject(
    tmp_path: Path,
) -> None:
    """Test init command auto-detects entry_point from pyproject.toml."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create pyproject.toml with scripts section
        pyproject_content = """[project]
name = "test-package"

[project.scripts]
test-cli = "my_package.__main__:main"
"""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(pyproject_content, encoding="utf-8")

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["init"])

        # Verify exit code is 0
        assert code == 0

        # Verify config file was created
        config_file = tmp_path / ".zipbundler.jsonc"
        assert config_file.exists()

        # Verify entry_point was auto-detected and injected
        content = config_file.read_text(encoding="utf-8")
        assert '"entry_point"' in content
        assert '"entry_point": "my_package.__main__:main"' in content
    finally:
        os.chdir(original_cwd)


def test_cli_init_command_auto_detects_entry_point_with_module_only(
    tmp_path: Path,
) -> None:
    """Test init command auto-detects entry_point with module-only format."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create pyproject.toml with scripts section (module only, no function)
        pyproject_content = """[project]
name = "test-package"

[project.scripts]
test-cli = "my_package"
"""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(pyproject_content, encoding="utf-8")

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["init"])

        # Verify exit code is 0
        assert code == 0

        # Verify config file was created
        config_file = tmp_path / ".zipbundler.jsonc"
        assert config_file.exists()

        # Verify entry_point was auto-detected and injected
        content = config_file.read_text(encoding="utf-8")
        assert '"entry_point"' in content
        assert '"entry_point": "my_package"' in content
    finally:
        os.chdir(original_cwd)


def test_cli_init_command_no_entry_point_when_no_scripts(tmp_path: Path) -> None:
    """Test init command does not add entry_point when no scripts section exists."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create pyproject.toml without scripts section
        pyproject_content = """[project]
name = "test-package"
version = "1.0.0"
"""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(pyproject_content, encoding="utf-8")

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["init", "--preset", "basic"])

        # Verify exit code is 0
        assert code == 0

        # Verify config file was created
        config_file = tmp_path / ".zipbundler.jsonc"
        assert config_file.exists()

        # Verify entry_point section is still commented (not auto-detected)
        content = config_file.read_text(encoding="utf-8")
        # For basic preset, entry_point should be commented out
        assert '// "entry_point":' in content or '"entry_point"' not in content
    finally:
        os.chdir(original_cwd)


def test_cli_init_command_auto_detects_both_metadata_and_entry_point(
    tmp_path: Path,
) -> None:
    """Test init auto-detects both metadata and entry_point from pyproject.toml."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create pyproject.toml with both metadata and scripts
        pyproject_content = """[project]
name = "test-package"
version = "1.2.3"
description = "A test package"

[project.scripts]
test-cli = "my_package.__main__:main"
"""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_file.write_text(pyproject_content, encoding="utf-8")

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["init"])

        # Verify exit code is 0
        assert code == 0

        # Verify config file was created
        config_file = tmp_path / ".zipbundler.jsonc"
        assert config_file.exists()

        # Verify both metadata and entry_point were auto-detected
        content = config_file.read_text(encoding="utf-8")
        assert '"metadata"' in content
        assert '"display_name": "test-package"' in content
        assert '"entry_point"' in content
        assert '"entry_point": "my_package.__main__:main"' in content
    finally:
        os.chdir(original_cwd)
