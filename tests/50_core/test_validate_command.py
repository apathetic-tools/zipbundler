# tests/50_core/test_validate_command.py
"""Tests for the validate command."""

import os
from pathlib import Path

import zipbundler.cli as mod_main


def test_cli_validate_command_valid_config(tmp_path: Path) -> None:
    """Test validate command with valid config file."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a valid config file
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/my_package/**/*.py"],
  "exclude": ["**/__pycache__/**"],
  "output": {
    "path": "dist/my_package.zip"
  }
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["validate"])

        # Verify exit code is 0
        assert code == 0
    finally:
        os.chdir(original_cwd)


def test_cli_validate_command_missing_packages(tmp_path: Path) -> None:
    """Test validate command with missing packages field."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create config file without packages
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "exclude": ["**/__pycache__/**"]
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["validate"])

        # Verify exit code is 1 (error)
        assert code == 1
    finally:
        os.chdir(original_cwd)


def test_cli_validate_command_invalid_entry_point(tmp_path: Path) -> None:
    """Test validate command with invalid entry point format."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create config file with invalid entry point
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/my_package/**/*.py"],
  "entry_point": "invalid-entry-point-format"
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["validate"])

        # Verify exit code is 1 (error)
        assert code == 1
    finally:
        os.chdir(original_cwd)


def test_cli_validate_command_valid_entry_point(tmp_path: Path) -> None:
    """Test validate command with valid entry point format."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create config file with valid entry point
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/my_package/**/*.py"],
  "entry_point": "my_package.__main__:main"
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["validate"])

        # Verify exit code is 0
        assert code == 0
    finally:
        os.chdir(original_cwd)


def test_cli_validate_command_empty_packages_warning(tmp_path: Path) -> None:
    """Test validate command with empty packages list (warning)."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create config file with empty packages
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": []
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["validate"])

        # Verify exit code is 0 (warning, not error)
        assert code == 0
    finally:
        os.chdir(original_cwd)


def test_cli_validate_command_strict_mode(tmp_path: Path) -> None:
    """Test validate command with --strict flag (warnings become errors)."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create config file with empty packages (warning)
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": []
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["validate", "--strict"])

        # Verify exit code is 1 (warning becomes error in strict mode)
        assert code == 1
    finally:
        os.chdir(original_cwd)


def test_cli_validate_command_custom_config_path(tmp_path: Path) -> None:
    """Test validate command with custom config path."""
    # Create a valid config file at custom path
    config_file = tmp_path / "custom.jsonc"
    config_file.write_text(
        """{
  "packages": ["src/my_package/**/*.py"]
}
""",
        encoding="utf-8",
    )

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func(["validate", "--config", str(config_file)])

    # Verify exit code is 0
    assert code == 0


def test_cli_validate_command_no_config_file(tmp_path: Path) -> None:
    """Test validate command when no config file exists."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Don't create any config file

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["validate"])

        # Verify exit code is 1 (error - no config found)
        assert code == 1
    finally:
        os.chdir(original_cwd)


def test_cli_validate_command_invalid_json(tmp_path: Path) -> None:
    """Test validate command with invalid JSON syntax."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create config file with invalid JSON
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/my_package/**/*.py"
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["validate"])

        # Verify exit code is 1 (error - invalid JSON)
        assert code == 1
    finally:
        os.chdir(original_cwd)


def test_cli_validate_command_invalid_packages_type(tmp_path: Path) -> None:
    """Test validate command with packages as non-list."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create config file with packages as string instead of list
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": "src/my_package/**/*.py"
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["validate"])

        # Verify exit code is 1 (error)
        assert code == 1
    finally:
        os.chdir(original_cwd)


def test_cli_validate_command_finds_config_in_parent_directory(tmp_path: Path) -> None:
    """Test validate command finds config file in parent directory."""
    original_cwd = Path.cwd()
    try:
        # Create config file in parent directory
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/my_package/**/*.py"]
}
""",
            encoding="utf-8",
        )

        # Create a subdirectory and change to it
        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)
        os.chdir(subdir)

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["validate"])

        # Verify exit code is 0 (config found in parent)
        assert code == 0
    finally:
        os.chdir(original_cwd)


def test_cli_validate_command_prefers_local_over_parent_config(tmp_path: Path) -> None:
    """Test validate command prefers local config over parent config."""
    original_cwd = Path.cwd()
    try:
        # Create config file in parent directory
        parent_config = tmp_path / ".zipbundler.jsonc"
        parent_config.write_text(
            """{
  "packages": ["parent_package/**/*.py"]
}
""",
            encoding="utf-8",
        )

        # Create a subdirectory with its own config
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        local_config = subdir / ".zipbundler.jsonc"
        local_config.write_text(
            """{
  "packages": ["local_package/**/*.py"]
}
""",
            encoding="utf-8",
        )

        os.chdir(subdir)

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["validate"])

        # Verify exit code is 0 (local config found)
        assert code == 0
    finally:
        os.chdir(original_cwd)


def test_cli_validate_command_prefers_jsonc_over_pyproject_toml(
    tmp_path: Path,
) -> None:
    """Test validate prefers .zipbundler.jsonc over pyproject.toml when both exist."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create both config files
        jsonc_config = tmp_path / ".zipbundler.jsonc"
        jsonc_config.write_text(
            """{
  "packages": ["jsonc_package/**/*.py"]
}
""",
            encoding="utf-8",
        )

        toml_config = tmp_path / "pyproject.toml"
        toml_config.write_text(
            """[tool.zipbundler]
packages = ["toml_package/**/*.py"]
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["validate"])

        # Verify exit code is 0 (config found, jsonc preferred)
        assert code == 0
    finally:
        os.chdir(original_cwd)
