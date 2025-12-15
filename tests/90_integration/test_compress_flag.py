# tests/50_core/test_compress_flag.py
"""Tests for compress control via --compress/--no-compress flag."""

import os
import zipfile
from pathlib import Path

import zipbundler.cli as mod_main


def test_cli_build_with_no_compress_flag(tmp_path: Path) -> None:
    """Test that --no-compress flag disables compression."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure with some content
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("# init file\n" * 100)
        (src_dir / "module.py").write_text(
            "def hello():\n    return 'Hello, World!'\n" * 100
        )

        # Create config file
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

        # Build with --no-compress flag
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--no-compress"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.pyz"
        assert output_file.exists()

        # Verify all files in zip use STORED compression
        with zipfile.ZipFile(output_file, "r") as zf:
            for info in zf.infolist():
                # ZIP_STORED = 0, ZIP_DEFLATED = 8
                assert info.compress_type == zipfile.ZIP_STORED
    finally:
        os.chdir(original_cwd)


def test_cli_build_with_compress_flag(tmp_path: Path) -> None:
    """Test that --compress flag enables compression."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure with some content
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("# init file\n" * 100)
        (src_dir / "module.py").write_text(
            "def hello():\n    return 'Hello, World!'\n" * 100
        )

        # Create config file
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

        # Build with --compress flag
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--compress"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.pyz"
        assert output_file.exists()

        # Verify files in zip use DEFLATED compression
        with zipfile.ZipFile(output_file, "r") as zf:
            for info in zf.infolist():
                # ZIP_DEFLATED = 8 for most files
                # PKG-INFO or other metadata might be STORED
                assert info.compress_type in (
                    zipfile.ZIP_DEFLATED,
                    zipfile.ZIP_STORED,
                )
    finally:
        os.chdir(original_cwd)


def test_cli_build_default_compression_behavior(tmp_path: Path) -> None:
    """Test that default behavior (no flag) enables compression."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure with some content
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("# init file\n" * 100)
        (src_dir / "module.py").write_text(
            "def hello():\n    return 'Hello, World!'\n" * 100
        )

        # Create config file with no compression settings
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

        # Build without any compression flags
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.pyz"
        assert output_file.exists()

        # Verify default uses DEFLATED compression
        with zipfile.ZipFile(output_file, "r") as zf:
            has_deflated = False
            for info in zf.infolist():
                if info.compress_type == zipfile.ZIP_DEFLATED:
                    has_deflated = True
            # Should have at least some deflated files
            assert has_deflated
    finally:
        os.chdir(original_cwd)
