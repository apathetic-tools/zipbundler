# tests/50_core/test_compress_config.py
"""Tests for compress option in configuration file."""

import os
import zipfile
from pathlib import Path

import zipbundler.cli as mod_main


def test_config_compress_false(tmp_path: Path) -> None:
    """Test that compress: false in config disables compression."""
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

        # Create config file with compress: false
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.pyz"
  },
  "options": {
    "compress": false
  }
}
""",
            encoding="utf-8",
        )

        # Build without flags (should use config)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.pyz"
        assert output_file.exists()

        # Verify all files use STORED compression
        with zipfile.ZipFile(output_file, "r") as zf:
            for info in zf.infolist():
                assert info.compress_type == zipfile.ZIP_STORED
    finally:
        os.chdir(original_cwd)


def test_config_compress_true(tmp_path: Path) -> None:
    """Test that compress: true in config enables compression."""
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

        # Create config file with compress: true
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.pyz"
  },
  "options": {
    "compress": true
  }
}
""",
            encoding="utf-8",
        )

        # Build without flags (should use config)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.pyz"
        assert output_file.exists()

        # Verify files use DEFLATED compression
        with zipfile.ZipFile(output_file, "r") as zf:
            has_deflated = False
            for info in zf.infolist():
                if info.compress_type == zipfile.ZIP_DEFLATED:
                    has_deflated = True
            assert has_deflated
    finally:
        os.chdir(original_cwd)


def test_cli_flag_overrides_config_compress(tmp_path: Path) -> None:
    """Test that CLI --no-compress overrides config compress: true."""
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

        # Create config file with compress: true
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.pyz"
  },
  "options": {
    "compress": true
  }
}
""",
            encoding="utf-8",
        )

        # Build with --no-compress flag (should override config)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--no-compress"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.pyz"
        assert output_file.exists()

        # Verify all files use STORED compression (CLI flag overrides)
        with zipfile.ZipFile(output_file, "r") as zf:
            for info in zf.infolist():
                assert info.compress_type == zipfile.ZIP_STORED
    finally:
        os.chdir(original_cwd)


def test_cli_compress_overrides_config_compress_false(tmp_path: Path) -> None:
    """Test that CLI --compress overrides config compress: false."""
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

        # Create config file with compress: false
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.pyz"
  },
  "options": {
    "compress": false
  }
}
""",
            encoding="utf-8",
        )

        # Build with --compress flag (should override config)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--compress"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.pyz"
        assert output_file.exists()

        # Verify files use DEFLATED compression (CLI flag overrides)
        with zipfile.ZipFile(output_file, "r") as zf:
            has_deflated = False
            for info in zf.infolist():
                if info.compress_type == zipfile.ZIP_DEFLATED:
                    has_deflated = True
            assert has_deflated
    finally:
        os.chdir(original_cwd)
