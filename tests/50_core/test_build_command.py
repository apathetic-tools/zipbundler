# tests/50_core/test_build_command.py
"""Tests for the build command."""

import os
import zipfile
from pathlib import Path

import zipbundler.cli as mod_main


def test_cli_build_command_basic(tmp_path: Path) -> None:
    """Test build command with valid config file and packages."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func():\n    pass\n")

        # Create a valid config file
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
        code = main_func(["build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()

        # Verify zip file is valid and contains expected files
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("mypackage/__init__.py" in name for name in names)
            assert any("mypackage/module.py" in name for name in names)
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_no_config(tmp_path: Path) -> None:
    """Test build command when no config file exists."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Don't create any config file

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["build"])

        # Verify exit code is 1 (error - no config found)
        assert code == 1
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_with_entry_point(tmp_path: Path) -> None:
    """Test build command with entry point in config."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "__main__.py").write_text("def main():\n    print('Hello')\n")

        # Create config file with entry point
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "entry_point": "mypackage.__main__:main",
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

        # Verify zip file contains __main__.py
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert "__main__.py" in names
            # Verify __main__.py contains entry point code
            main_content = zf.read("__main__.py").decode("utf-8")
            assert "from mypackage.__main__ import main" in main_content
            assert "main()" in main_content
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_with_exclude(tmp_path: Path) -> None:
    """Test build command with exclude patterns."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure with tests
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func():\n    pass\n")
        tests_dir = src_dir / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").write_text("")
        (tests_dir / "test_module.py").write_text("def test_func():\n    pass\n")

        # Create config file with exclude
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "exclude": ["**/tests/**"],
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

        # Verify zip file does NOT contain test files
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("mypackage/__init__.py" in name for name in names)
            assert any("mypackage/module.py" in name for name in names)
            assert not any("tests" in name for name in names)
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_cli_override_output(tmp_path: Path) -> None:
    """Test build command with CLI override for output path."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create config file
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
        custom_output = tmp_path / "custom.zip"
        code = main_func(["build", "-o", str(custom_output)])

        # Verify exit code is 0
        assert code == 0

        # Verify custom output file was created (not the one from config)
        assert custom_output.exists()
        assert not (tmp_path / "dist" / "bundle.zip").exists()
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_output_name_generates_path(tmp_path: Path) -> None:
    """Test build command with output.name generating default path."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func():\n    pass\n")

        # Create config file with output.name but no output.path
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "name": "my_custom_package"
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

        # Verify zip file was created at path generated from output.name
        output_file = tmp_path / "dist" / "my_custom_package.pyz"
        assert output_file.exists()

        # Verify zip file is valid and contains expected files
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("mypackage/__init__.py" in name for name in names)
            assert any("mypackage/module.py" in name for name in names)
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_output_name_ignored_with_path(
    tmp_path: Path,
) -> None:
    """Test that output.name is ignored when output.path is provided."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create config file with both output.path and output.name
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/custom_path.zip",
    "name": "ignored_name"
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

        # Verify zip file was created at the specified path (not generated from name)
        output_file = tmp_path / "dist" / "custom_path.zip"
        assert output_file.exists()

        # Verify the name-based path was NOT created
        assert not (tmp_path / "dist" / "ignored_name.zip").exists()
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_output_directory(tmp_path: Path) -> None:
    """Test build command with output.directory configuration."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func():\n    pass\n")

        # Create config file with output.directory and output.name
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "directory": "build",
    "name": "my_package"
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

        # Verify zip file was created in the custom directory
        output_file = tmp_path / "build" / "my_package.pyz"
        assert output_file.exists()

        # Verify zip file is valid and contains expected files
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("mypackage/__init__.py" in name for name in names)
            assert any("mypackage/module.py" in name for name in names)

        # Verify default dist directory was NOT used
        assert not (tmp_path / "dist" / "my_package.pyz").exists()
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_output_directory_only(tmp_path: Path) -> None:
    """Test build command with only output.directory (no name)."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func():\n    pass\n")

        # Create config file with only output.directory
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "directory": "output"
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

        # Verify zip file was created in custom directory with default name
        output_file = tmp_path / "output" / "bundle.pyz"
        assert output_file.exists()

        # Verify zip file is valid
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("mypackage/__init__.py" in name for name in names)
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_invalid_config(tmp_path: Path) -> None:
    """Test build command with invalid config (missing packages)."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create config file without packages
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
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

        # Verify exit code is 1 (error - validation failed)
        assert code == 1
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_no_packages_resolved(tmp_path: Path) -> None:
    """Test build command when no packages can be resolved from patterns."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create config file with non-existent package pattern
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["nonexistent/package/**/*.py"],
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

        # Verify exit code is 1 (error - no packages resolved)
        assert code == 1
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_dry_run(tmp_path: Path) -> None:
    """Test build command with --dry-run flag."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create config file
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
        code = main_func(["build", "--dry-run"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was NOT created (dry-run)
        output_file = tmp_path / "dist" / "bundle.zip"
        assert not output_file.exists()
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_custom_config_path(tmp_path: Path) -> None:
    """Test build command with custom config path."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create config file at custom path
        config_file = tmp_path / "custom.jsonc"
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
        code = main_func(["build", "--config", str(config_file)])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_no_shebang_flag(tmp_path: Path) -> None:
    """Test build command with --no-shebang flag."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func():\n    pass\n")

        # Create config file with shebang enabled
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  },
  "options": {
    "shebang": "/usr/bin/env python3"
  }
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["build", "--no-shebang"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()

        # Verify no shebang was prepended - file should start with zip magic bytes
        content = output_file.read_bytes()
        assert content.startswith(b"PK")
        assert not content.startswith(b"#!/")
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_config_shebang_false(tmp_path: Path) -> None:
    """Test build command with shebang: false in config."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func():\n    pass\n")

        # Create config file with shebang disabled
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  },
  "options": {
    "shebang": false
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

        # Verify no shebang was prepended - file should start with zip magic bytes
        content = output_file.read_bytes()
        assert content.startswith(b"PK")
        assert not content.startswith(b"#!/")
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_compression_level(tmp_path: Path) -> None:
    """Test build command with --compression-level CLI option."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure with content that compresses well
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        # Create a file with repetitive content
        content = "def func():\n    " + "x" * 1000 + "\n    pass\n"
        (src_dir / "module.py").write_text(content)

        # Create config file with compression but no compression_level
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  },
  "options": {
    "compression": "deflate"
  }
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["build", "--compression-level", "9"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()

        # Verify compression is enabled with deflate
        with zipfile.ZipFile(output_file, "r") as zf:
            for info in zf.infolist():
                assert info.compress_type == zipfile.ZIP_DEFLATED
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_compression_level_override_config(tmp_path: Path) -> None:
    """Test that --compression-level CLI option overrides config."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func():\n    pass\n")

        # Create config file with compression_level set to 1
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  },
  "options": {
    "compression": "deflate",
    "compression_level": 1
  }
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        # Override with CLI option
        code = main_func(["build", "--compression-level", "9"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()

        # Verify compression is enabled
        with zipfile.ZipFile(output_file, "r") as zf:
            for info in zf.infolist():
                assert info.compress_type == zipfile.ZIP_DEFLATED
    finally:
        os.chdir(original_cwd)


def test_cli_build_command_python_config(tmp_path: Path) -> None:
    """Test build command with Python config file."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func():\n    pass\n")

        # Create a valid Python config file
        config_file = tmp_path / ".zipbundler.py"
        config_file.write_text(
            """config = {
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
        code = main_func(["build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()

        # Verify zip file is valid and contains expected files
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("mypackage/__init__.py" in name for name in names)
            assert any("mypackage/module.py" in name for name in names)
    finally:
        os.chdir(original_cwd)
