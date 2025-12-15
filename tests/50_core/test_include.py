# tests/50_core/test_include.py
"""Tests for the --include CLI flag and include config field."""

import os
import zipfile
from pathlib import Path

import zipbundler.cli as mod_main


def test_include_directory_overrides_config(tmp_path: Path) -> None:
    """Test --include overrides config packages."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create two separate package directories
        pkg1_dir = tmp_path / "src" / "pkg1"
        pkg1_dir.mkdir(parents=True)
        (pkg1_dir / "__init__.py").write_text("")
        (pkg1_dir / "module1.py").write_text("def func1(): pass\n")

        pkg2_dir = tmp_path / "extra" / "pkg2"
        pkg2_dir.mkdir(parents=True)
        (pkg2_dir / "__init__.py").write_text("")
        (pkg2_dir / "module2.py").write_text("def func2(): pass\n")

        # Create config with pkg1
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/pkg1/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  }
}
""",
            encoding="utf-8",
        )

        # Build with --include to override config (should only include pkg2)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--include", "extra/pkg2"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip contains only pkg2, not pkg1 (override behavior)
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            # pkg2 should be included
            assert any("pkg2/__init__.py" in name for name in names)
            assert any("pkg2/module2.py" in name for name in names)
            # pkg1 should NOT be included (overridden)
            assert not any("pkg1" in name for name in names)
    finally:
        os.chdir(original_cwd)


def test_include_file_with_destination(tmp_path: Path) -> None:
    """Test --include with file and custom destination format."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package
        pkg_dir = tmp_path / "src" / "mypackage"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")

        # Create additional files
        extra_pkg = tmp_path / "extra" / "extrapkg"
        extra_pkg.mkdir(parents=True)
        (extra_pkg / "__init__.py").write_text("")

        # Create config (will be overridden)
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

        # Build with --include to override with a different package
        # Note: CLI --include patterns work with glob patterns, not file:dest syntax
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(
            [
                "--build",
                "--include",
                "extra/extrapkg",
            ]
        )

        # Verify exit code is 0
        assert code == 0

        # Verify zip contains only the override package
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("extrapkg/__init__.py" in name for name in names)
            # Original package should not be included (--include overrides)
            assert not any("mypackage" in name for name in names)
    finally:
        os.chdir(original_cwd)


def test_include_multiple_items(tmp_path: Path) -> None:
    """Test --include with multiple items."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create packages
        pkg1_dir = tmp_path / "src" / "pkg1"
        pkg1_dir.mkdir(parents=True)
        (pkg1_dir / "__init__.py").write_text("")

        pkg2_dir = tmp_path / "src" / "pkg2"
        pkg2_dir.mkdir(parents=True)
        (pkg2_dir / "__init__.py").write_text("")

        # Create config (will be overridden)
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["other/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  }
}
""",
            encoding="utf-8",
        )

        # Build with --include multiple items
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(
            [
                "--build",
                "--include",
                "src/pkg1",
                "src/pkg2",
            ]
        )

        # Verify exit code is 0
        assert code == 0

        # Verify both packages are included
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("pkg1/__init__.py" in name for name in names)
            assert any("pkg2/__init__.py" in name for name in names)
    finally:
        os.chdir(original_cwd)


def test_include_with_exclude_combined(tmp_path: Path) -> None:
    """Test --include with --exclude applied together."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package with test files
        pkg_dir = tmp_path / "src" / "mypackage"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "module.py").write_text("def func(): pass\n")
        (pkg_dir / "test_module.py").write_text("def test(): pass\n")

        # Create config
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["other/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  }
}
""",
            encoding="utf-8",
        )

        # Build with --include and --exclude
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(
            [
                "--build",
                "--include",
                "src/mypackage",
                "--exclude",
                "**/test_*.py",
            ]
        )

        # Verify exit code is 0
        assert code == 0

        # Verify zip includes module.py but excludes test_module.py
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("module.py" in name for name in names)
            assert not any("test_module.py" in name for name in names)
    finally:
        os.chdir(original_cwd)


def test_include_overrides_empty_packages(tmp_path: Path) -> None:
    """Test --include overrides config with empty packages."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package
        pkg_dir = tmp_path / "src" / "mypackage"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")

        # Create config with empty packages
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": [],
  "output": {
    "path": "dist/bundle.zip"
  }
}
""",
            encoding="utf-8",
        )

        # Build with --include to override empty packages
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--include", "src/mypackage"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip contains the package
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("mypackage/__init__.py" in name for name in names)
    finally:
        os.chdir(original_cwd)


def test_config_include_field_jsonc(tmp_path: Path) -> None:
    """Test 'include' field in .jsonc config file extends packages."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create packages
        pkg_dir = tmp_path / "src" / "mypackage"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")

        extra_file = tmp_path / "extra.txt"
        extra_file.write_text("extra content")

        # Create config with both packages and include fields
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "include": ["extra.txt"],
  "output": {
    "path": "dist/bundle.zip"
  }
}
""",
            encoding="utf-8",
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip contains both items
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("mypackage/__init__.py" in name for name in names)
            assert "extra.txt" in names
    finally:
        os.chdir(original_cwd)


def test_config_include_field_json(tmp_path: Path) -> None:
    """Test 'include' field in .json config file extends packages."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package
        pkg_dir = tmp_path / "src" / "mypackage"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")

        extra_file = tmp_path / "data.json"
        extra_file.write_text('{"key": "value"}')

        # Create config with both packages and include fields
        config_file = tmp_path / ".zipbundler.json"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "include": ["data.json"],
  "output": {
    "path": "dist/bundle.zip"
  }
}
""",
            encoding="utf-8",
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip contains both package and extra file
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("mypackage/__init__.py" in name for name in names)
            assert "data.json" in names
    finally:
        os.chdir(original_cwd)


def test_config_include_field_python(tmp_path: Path) -> None:
    """Test 'include' field in .py config file extends packages."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package
        pkg_dir = tmp_path / "src" / "mypackage"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")

        extra_file = tmp_path / "config.txt"
        extra_file.write_text("config")

        # Create Python config with both packages and include fields
        config_file = tmp_path / ".zipbundler.py"
        config_file.write_text(
            """config = {
    "packages": ["src/mypackage/**/*.py"],
    "include": ["config.txt"],
    "output": {
        "path": "dist/bundle.zip"
    }
}
""",
            encoding="utf-8",
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip contains both items
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("mypackage/__init__.py" in name for name in names)
            assert "config.txt" in names
    finally:
        os.chdir(original_cwd)


def test_config_include_field_pyproject_toml(tmp_path: Path) -> None:
    """Test 'include' field in pyproject.toml [tool.zipbundler] section."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package
        pkg_dir = tmp_path / "src" / "mypackage"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")

        data_file = tmp_path / "data.txt"
        data_file.write_text("data")

        # Create pyproject.toml with both packages and include fields
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text(
            """[tool.zipbundler]
packages = ["src/mypackage/**/*.py"]
include = ["data.txt"]

[tool.zipbundler.output]
path = "dist/bundle.zip"
""",
            encoding="utf-8",
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip contains both items
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("mypackage/__init__.py" in name for name in names)
            assert "data.txt" in names
    finally:
        os.chdir(original_cwd)


def test_cli_include_overrides_config_include(tmp_path: Path) -> None:
    """Test that CLI --include overrides config packages/include."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create two packages
        pkg1_dir = tmp_path / "src" / "pkg1"
        pkg1_dir.mkdir(parents=True)
        (pkg1_dir / "__init__.py").write_text("")

        pkg2_dir = tmp_path / "src" / "pkg2"
        pkg2_dir.mkdir(parents=True)
        (pkg2_dir / "__init__.py").write_text("")

        extra_file = tmp_path / "extra.txt"
        extra_file.write_text("extra")

        # Create config with pkg1 and include field
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/pkg1/**/*.py"],
  "include": ["extra.txt"],
  "output": {
    "path": "dist/bundle.zip"
  }
}
""",
            encoding="utf-8",
        )

        # Build with --include to override config (pkg2 instead of pkg1)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--include", "src/pkg2"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip contains only pkg2 (config include is overridden)
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("pkg2/__init__.py" in name for name in names)
            assert not any("pkg1" in name for name in names)
            # extra.txt from config include should NOT be present
            assert "extra.txt" not in names
    finally:
        os.chdir(original_cwd)


def test_cli_add_include_extends_config_include(tmp_path: Path) -> None:
    """Test that CLI --add-include extends config packages/include."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create two packages
        pkg1_dir = tmp_path / "src" / "pkg1"
        pkg1_dir.mkdir(parents=True)
        (pkg1_dir / "__init__.py").write_text("")

        pkg2_dir = tmp_path / "src" / "pkg2"
        pkg2_dir.mkdir(parents=True)
        (pkg2_dir / "__init__.py").write_text("")

        extra_file = tmp_path / "extra.txt"
        extra_file.write_text("extra")

        # Create config with pkg1 and include field
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/pkg1/**/*.py"],
  "include": ["extra.txt"],
  "output": {
    "path": "dist/bundle.zip"
  }
}
""",
            encoding="utf-8",
        )

        # Build with --add-include to extend config (add pkg2)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--add-include", "src/pkg2"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip contains both packages and extra file
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("pkg1/__init__.py" in name for name in names)
            assert any("pkg2/__init__.py" in name for name in names)
            # Config include field should also be present
            assert "extra.txt" in names
    finally:
        os.chdir(original_cwd)


def test_exclude_in_python_config(tmp_path: Path) -> None:
    """Test exclude patterns in .py config file."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package with test files
        pkg_dir = tmp_path / "src" / "mypackage"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "module.py").write_text("def func(): pass\n")
        (pkg_dir / "test_module.py").write_text("def test(): pass\n")

        # Create Python config with exclude
        config_file = tmp_path / ".zipbundler.py"
        config_file.write_text(
            """config = {
    "packages": ["src/mypackage/**/*.py"],
    "exclude": ["**/test_*.py"],
    "output": {
        "path": "dist/bundle.zip"
    }
}
""",
            encoding="utf-8",
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip excludes test files
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("module.py" in name for name in names)
            assert not any("test_" in name for name in names)
    finally:
        os.chdir(original_cwd)


def test_include_and_exclude_in_python_config(tmp_path: Path) -> None:
    """Test both packages/include and exclude in .py config file."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create packages
        pkg_dir = tmp_path / "src" / "mypackage"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "module.py").write_text("def func(): pass\n")
        (pkg_dir / "test_module.py").write_text("def test(): pass\n")

        extra_dir = tmp_path / "extra"
        extra_dir.mkdir()
        (extra_dir / "extra.txt").write_text("extra")

        # Create Python config with packages, include and exclude
        config_file = tmp_path / ".zipbundler.py"
        config_file.write_text(
            """config = {
    "packages": ["src/mypackage/**/*.py"],
    "include": ["extra/extra.txt"],
    "exclude": ["**/test_*.py"],
    "output": {
        "path": "dist/bundle.zip"
    }
}
""",
            encoding="utf-8",
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip contains both dirs but excludes test files
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("module.py" in name for name in names)
            assert any("extra.txt" in name for name in names)
            assert not any("test_" in name for name in names)
    finally:
        os.chdir(original_cwd)


def test_exclude_in_json_config(tmp_path: Path) -> None:
    """Test exclude patterns in .json config file."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package with test files
        pkg_dir = tmp_path / "src" / "mypackage"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "module.py").write_text("def func(): pass\n")
        (pkg_dir / "test_module.py").write_text("def test(): pass\n")

        # Create JSON config with exclude
        config_file = tmp_path / ".zipbundler.json"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "exclude": ["**/test_*.py"],
  "output": {
    "path": "dist/bundle.zip"
  }
}
""",
            encoding="utf-8",
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip excludes test files
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("module.py" in name for name in names)
            assert not any("test_" in name for name in names)
    finally:
        os.chdir(original_cwd)


def test_include_in_json_config(tmp_path: Path) -> None:
    """Test include field extending packages in .json config file."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package
        pkg_dir = tmp_path / "src" / "mypackage"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")

        data_file = tmp_path / "data.txt"
        data_file.write_text("data")

        # Create JSON config with packages and include
        config_file = tmp_path / ".zipbundler.json"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "include": ["data.txt"],
  "output": {
    "path": "dist/bundle.zip"
  }
}
""",
            encoding="utf-8",
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip contains both items
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("mypackage/__init__.py" in name for name in names)
            assert "data.txt" in names
    finally:
        os.chdir(original_cwd)


def test_include_in_pyproject_toml(tmp_path: Path) -> None:
    """Test include field extending packages in pyproject.toml."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package
        pkg_dir = tmp_path / "src" / "mypackage"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")

        extra_file = tmp_path / "extra.txt"
        extra_file.write_text("extra")

        # Create pyproject.toml with packages and include
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text(
            """[tool.zipbundler]
packages = ["src/mypackage/**/*.py"]
include = ["extra.txt"]

[tool.zipbundler.output]
path = "dist/bundle.zip"
""",
            encoding="utf-8",
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip contains both items
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("mypackage/__init__.py" in name for name in names)
            assert "extra.txt" in names
    finally:
        os.chdir(original_cwd)


def test_exclude_in_pyproject_toml(tmp_path: Path) -> None:
    """Test exclude patterns in pyproject.toml."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package with test files
        pkg_dir = tmp_path / "src" / "mypackage"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "module.py").write_text("def func(): pass\n")
        (pkg_dir / "test_module.py").write_text("def test(): pass\n")

        # Create pyproject.toml with exclude
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text(
            """[tool.zipbundler]
packages = ["src/mypackage/**/*.py"]
exclude = ["**/test_*.py"]

[tool.zipbundler.output]
path = "dist/bundle.zip"
""",
            encoding="utf-8",
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip excludes test files
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("module.py" in name for name in names)
            assert not any("test_" in name for name in names)
    finally:
        os.chdir(original_cwd)


def test_include_exclude_in_pyproject_toml(tmp_path: Path) -> None:
    """Test packages/include and exclude in pyproject.toml."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create packages
        pkg_dir = tmp_path / "src" / "mypackage"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "module.py").write_text("def func(): pass\n")
        (pkg_dir / "test_module.py").write_text("def test(): pass\n")

        extra_dir = tmp_path / "extra"
        extra_dir.mkdir()
        (extra_dir / "extra.txt").write_text("extra")

        # Create pyproject.toml with packages, include and exclude
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text(
            """[tool.zipbundler]
packages = ["src/mypackage/**/*.py"]
include = ["extra/extra.txt"]
exclude = ["**/test_*.py"]

[tool.zipbundler.output]
path = "dist/bundle.zip"
""",
            encoding="utf-8",
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip contains both dirs but excludes test files
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("module.py" in name for name in names)
            assert any("extra.txt" in name for name in names)
            assert not any("test_" in name for name in names)
    finally:
        os.chdir(original_cwd)
