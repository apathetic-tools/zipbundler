# tests/50_core/test_zip_includes.py
"""Tests for zip include functionality."""

import os
import zipfile
from pathlib import Path

import zipbundler.cli as mod_main


def test_config_zip_include_basic(tmp_path: Path) -> None:
    """Test basic zip include from config."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a feature module to be zipped
        feature_dir = tmp_path / "features"
        feature_dir.mkdir()
        (feature_dir / "__init__.py").write_text("")
        (feature_dir / "utils.py").write_text("def feature_func(): pass\n")

        # Create a feature zip
        feature_zip = tmp_path / "feature.pyz"
        with zipfile.ZipFile(feature_zip, "w") as zf:
            zf.write(feature_dir / "__init__.py", "features/__init__.py")
            zf.write(feature_dir / "utils.py", "features/utils.py")

        # Create main package
        src_dir = tmp_path / "src" / "main"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "app.py").write_text("def main(): pass\n")

        # Create config with zip include
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/main/**/*.py"],
  "include": [
    { "path": "feature.pyz", "type": "zip" }
  ],
  "output": {
    "path": "dist/app.pyz"
  }
}
""",
            encoding="utf-8",
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])
        assert code == 0

        # Verify output
        output_file = tmp_path / "dist" / "app.pyz"
        assert output_file.exists()

        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            # Check main package is present
            assert any("main/__init__.py" in name for name in names)
            assert any("main/app.py" in name for name in names)
            # Check feature package from zip is present
            assert any("features/__init__.py" in name for name in names)
            assert any("features/utils.py" in name for name in names)

    finally:
        os.chdir(original_cwd)


def test_config_zip_include_with_dest(tmp_path: Path) -> None:
    """Test zip include with dest remapping."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a plugins module
        plugins_dir = tmp_path / "plugins_src"
        plugins_dir.mkdir()
        (plugins_dir / "__init__.py").write_text("")
        (plugins_dir / "plugin_a.py").write_text("def plugin_a(): pass\n")

        # Create a plugins zip
        plugins_zip = tmp_path / "plugins.pyz"
        with zipfile.ZipFile(plugins_zip, "w") as zf:
            zf.write(plugins_dir / "__init__.py", "__init__.py")
            zf.write(plugins_dir / "plugin_a.py", "plugin_a.py")

        # Create main package
        src_dir = tmp_path / "src" / "main"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create config with dest remapping
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/main/**/*.py"],
  "include": [
    { "path": "plugins.pyz", "type": "zip", "dest": "plugins/" }
  ],
  "output": {
    "path": "dist/app.pyz"
  }
}
""",
            encoding="utf-8",
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])
        assert code == 0

        # Verify output
        output_file = tmp_path / "dist" / "app.pyz"
        assert output_file.exists()

        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            # Check plugins are under plugins/ directory
            assert any("plugins/__init__.py" in name for name in names)
            assert any("plugins/plugin_a.py" in name for name in names)
            # Make sure they're not at root
            assert not any(name == "__init__.py" for name in names)
            assert not any(name == "plugin_a.py" for name in names)

    finally:
        os.chdir(original_cwd)


def test_cli_add_zip_flag(tmp_path: Path) -> None:
    """Test --add-zip CLI flag."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a feature zip
        feature_dir = tmp_path / "features"
        feature_dir.mkdir()
        (feature_dir / "feature.py").write_text("def feature(): pass\n")

        feature_zip = tmp_path / "feature.pyz"
        with zipfile.ZipFile(feature_zip, "w") as zf:
            zf.write(feature_dir / "feature.py", "feature.py")

        # Create main package
        src_dir = tmp_path / "src" / "main"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create config
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/main/**/*.py"],
  "output": {
    "path": "dist/app.pyz"
  }
}
""",
            encoding="utf-8",
        )

        # Build with --add-zip
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--add-zip", "feature.pyz"])
        assert code == 0

        # Verify output
        output_file = tmp_path / "dist" / "app.pyz"
        assert output_file.exists()

        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("feature.py" in name for name in names)

    finally:
        os.chdir(original_cwd)


def test_cli_add_zip_with_dest(tmp_path: Path) -> None:
    """Test --add-zip with dest remapping."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a plugins zip
        plugins_dir = tmp_path / "plugins_src"
        plugins_dir.mkdir()
        (plugins_dir / "plugin.py").write_text("def plugin(): pass\n")

        plugins_zip = tmp_path / "plugins.pyz"
        with zipfile.ZipFile(plugins_zip, "w") as zf:
            zf.write(plugins_dir / "plugin.py", "plugin.py")

        # Create main package
        src_dir = tmp_path / "src" / "main"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create config
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/main/**/*.py"],
  "output": {
    "path": "dist/app.pyz"
  }
}
""",
            encoding="utf-8",
        )

        # Build with --add-zip and dest
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--add-zip", "plugins.pyz:plugins/"])
        assert code == 0

        # Verify output
        output_file = tmp_path / "dist" / "app.pyz"
        assert output_file.exists()

        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("plugins/plugin.py" in name for name in names)

    finally:
        os.chdir(original_cwd)


def test_zip_include_respects_excludes(tmp_path: Path) -> None:
    """Test that exclude patterns apply to zip contents."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a zip with both .py and .pyc files
        test_dir = tmp_path / "test_src"
        test_dir.mkdir()
        (test_dir / "module.py").write_text("def func(): pass\n")
        (test_dir / "module.pyc").write_bytes(b"compiled")

        test_zip = tmp_path / "test.pyz"
        with zipfile.ZipFile(test_zip, "w") as zf:
            zf.write(test_dir / "module.py", "module.py")
            zf.write(test_dir / "module.pyc", "module.pyc")

        # Create main package
        src_dir = tmp_path / "src" / "main"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create config with exclude pattern
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/main/**/*.py"],
  "exclude": ["*.pyc"],
  "include": [
    { "path": "test.pyz", "type": "zip" }
  ],
  "output": {
    "path": "dist/app.pyz"
  }
}
""",
            encoding="utf-8",
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])
        assert code == 0

        # Verify output
        output_file = tmp_path / "dist" / "app.pyz"
        assert output_file.exists()

        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            # .py should be present
            assert any("module.py" in name for name in names)
            # .pyc should be excluded
            assert not any("module.pyc" in name for name in names)

    finally:
        os.chdir(original_cwd)


def test_multiple_zip_includes(tmp_path: Path) -> None:
    """Test multiple zip includes merge correctly."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create two zips
        zip1_dir = tmp_path / "zip1_src"
        zip1_dir.mkdir()
        (zip1_dir / "mod1.py").write_text("def func1(): pass\n")

        zip1 = tmp_path / "zip1.pyz"
        with zipfile.ZipFile(zip1, "w") as zf:
            zf.write(zip1_dir / "mod1.py", "mod1.py")

        zip2_dir = tmp_path / "zip2_src"
        zip2_dir.mkdir()
        (zip2_dir / "mod2.py").write_text("def func2(): pass\n")

        zip2 = tmp_path / "zip2.pyz"
        with zipfile.ZipFile(zip2, "w") as zf:
            zf.write(zip2_dir / "mod2.py", "mod2.py")

        # Create main package
        src_dir = tmp_path / "src" / "main"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create config with multiple zips
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/main/**/*.py"],
  "include": [
    { "path": "zip1.pyz", "type": "zip" },
    { "path": "zip2.pyz", "type": "zip" }
  ],
  "output": {
    "path": "dist/app.pyz"
  }
}
""",
            encoding="utf-8",
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])
        assert code == 0

        # Verify output
        output_file = tmp_path / "dist" / "app.pyz"
        assert output_file.exists()

        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("mod1.py" in name for name in names)
            assert any("mod2.py" in name for name in names)

    finally:
        os.chdir(original_cwd)
