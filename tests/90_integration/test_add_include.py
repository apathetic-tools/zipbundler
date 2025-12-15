# tests/50_core/test_add_include.py
"""Tests for the --add-include CLI flag."""

import os
import zipfile
from pathlib import Path

import zipbundler.cli as mod_main


def test_add_include_directory(tmp_path: Path) -> None:
    """Test --add-include with a directory appends to config packages."""
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

        # Create config with only pkg1
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

        # Build with --add-include to add pkg2
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--add-include", "extra/pkg2"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip contains files from both packages
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("pkg1/__init__.py" in name for name in names)
            assert any("pkg1/module1.py" in name for name in names)
            assert any("pkg2/__init__.py" in name for name in names)
            assert any("pkg2/module2.py" in name for name in names)
    finally:
        os.chdir(original_cwd)


def test_add_include_file_with_dest(tmp_path: Path) -> None:
    """Test --add-include with file and destination."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package
        pkg_dir = tmp_path / "src" / "mypackage"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")

        # Create additional files outside the package
        config_content = tmp_path / "config.json"
        config_content.write_text('{"key": "value"}')

        readme_file = tmp_path / "README.md"
        readme_file.write_text("# My Package\n")

        # Create config with just the package
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

        # Build with --add-include to add files with custom destinations
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(
            [
                "--build",
                "--add-include",
                "config.json:etc/config.json",
                "README.md:docs/README.md",
            ]
        )

        # Verify exit code is 0
        assert code == 0

        # Verify zip contains files with correct destinations
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert "etc/config.json" in names
            assert "docs/README.md" in names
            assert any("mypackage/__init__.py" in name for name in names)
    finally:
        os.chdir(original_cwd)


def test_add_include_file_without_dest(tmp_path: Path) -> None:
    """Test --add-include with file but no destination (uses basename)."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package
        pkg_dir = tmp_path / "src" / "mypackage"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")

        # Create an additional file
        data_file = tmp_path / "data.txt"
        data_file.write_text("some data")

        # Create config
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

        # Build with --add-include but no destination (should use basename)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--add-include", "data.txt"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip contains file at basename
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert "data.txt" in names
    finally:
        os.chdir(original_cwd)


def test_add_include_multiple_items(tmp_path: Path) -> None:
    """Test --add-include with multiple items in one call."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package
        pkg_dir = tmp_path / "src" / "pkg"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "__init__.py").write_text("")

        # Create extra files
        (tmp_path / "file1.txt").write_text("file1")
        (tmp_path / "file2.txt").write_text("file2")

        # Create additional package
        extra_pkg = tmp_path / "extra" / "extrapkg"
        extra_pkg.mkdir(parents=True)
        (extra_pkg / "__init__.py").write_text("")
        (extra_pkg / "mod.py").write_text("pass\n")

        # Create config
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/pkg/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  }
}
""",
            encoding="utf-8",
        )

        # Build with multiple --add-include items
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(
            [
                "--build",
                "--add-include",
                "file1.txt",
                "file2.txt:data/file2.txt",
                "extra/extrapkg",
            ]
        )

        # Verify exit code is 0
        assert code == 0

        # Verify all items are in zip
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert "file1.txt" in names
            assert "data/file2.txt" in names
            assert any("extrapkg/__init__.py" in name for name in names)
    finally:
        os.chdir(original_cwd)
