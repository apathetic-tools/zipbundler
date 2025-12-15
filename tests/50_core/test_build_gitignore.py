# tests/50_core/test_build_gitignore.py
"""Tests for gitignore integration with build command."""

import os
import zipfile
from pathlib import Path

import zipbundler.cli as mod_main


def test_build_respects_gitignore_by_default(tmp_path: Path) -> None:
    """Test that build respects .gitignore patterns by default."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func(): pass\n")

        # Create .gitignore
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n__pycache__/\n")

        # Create config
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  }
}
"""
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        assert code == 0

        # Verify zip was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()

        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            # Should include Python files
            assert any("__init__.py" in n for n in names)
            assert any("module.py" in n for n in names)
    finally:
        os.chdir(original_cwd)


def test_build_with_gitignore_flag_explicit(tmp_path: Path) -> None:
    """Test build with explicit --gitignore flag."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func(): pass\n")

        # Create .gitignore
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n")

        # Create config
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  }
}
"""
        )

        # Build with explicit --gitignore flag
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--gitignore"])

        assert code == 0

        # Verify zip was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
    finally:
        os.chdir(original_cwd)


def test_build_with_no_gitignore_flag(tmp_path: Path) -> None:
    """Test build with --no-gitignore flag works (respects CLI flag)."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func(): pass\n")

        # Create .gitignore
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("module.py\n")

        # Create config
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  }
}
"""
        )

        # Build with --no-gitignore (ignore .gitignore file)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--no-gitignore"])

        assert code == 0

        # Verify build succeeds with --no-gitignore flag
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("__init__.py" in n for n in names)
    finally:
        os.chdir(original_cwd)


def test_build_gitignore_config_option_true(tmp_path: Path) -> None:
    """Test build with config option respect_gitignore: true."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func(): pass\n")

        # Create .gitignore
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n")

        # Create config with respect_gitignore: true
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  },
  "options": {
    "respect_gitignore": true
  }
}
"""
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        assert code == 0

        # Verify build succeeds with config option
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("__init__.py" in n for n in names)
    finally:
        os.chdir(original_cwd)


def test_build_gitignore_config_option_false(tmp_path: Path) -> None:
    """Test build with config option respect_gitignore: false."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func(): pass\n")

        # Create .gitignore
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n")

        # Create config with respect_gitignore: false
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  },
  "options": {
    "respect_gitignore": false
  }
}
"""
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        assert code == 0

        # Verify build succeeds with respect_gitignore: false
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("__init__.py" in n for n in names)
    finally:
        os.chdir(original_cwd)


def test_build_cli_flag_overrides_config(tmp_path: Path) -> None:
    """Test CLI flag --gitignore overrides config option."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func(): pass\n")

        # Create .gitignore
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n")

        # Create config with respect_gitignore: false
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  },
  "options": {
    "respect_gitignore": false
  }
}
"""
        )

        # Build with --gitignore flag (overrides config)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--gitignore"])

        assert code == 0

        # Verify CLI flag overrides config
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
    finally:
        os.chdir(original_cwd)


def test_build_no_gitignore_flag_overrides_config(tmp_path: Path) -> None:
    """Test CLI flag --no-gitignore overrides config option."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func(): pass\n")

        # Create .gitignore
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n")

        # Create config with respect_gitignore: true (default)
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  },
  "options": {
    "respect_gitignore": true
  }
}
"""
        )

        # Build with --no-gitignore flag (overrides config)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--no-gitignore"])

        assert code == 0

        # Verify CLI flag overrides config
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
    finally:
        os.chdir(original_cwd)


def test_build_gitignore_missing_file(tmp_path: Path) -> None:
    """Test build succeeds when .gitignore file is missing."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("")

        # Don't create .gitignore file

        # Create config
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  }
}
"""
        )

        # Build should succeed without .gitignore
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        assert code == 0

        # Verify all files included (no gitignore to filter)
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("__init__.py" in n for n in names)
            assert any("module.py" in n for n in names)
    finally:
        os.chdir(original_cwd)


def test_build_gitignore_combined_with_excludes(tmp_path: Path) -> None:
    """Test gitignore patterns combine with explicit excludes."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("")

        # Create .gitignore
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n")

        # Create config with explicit excludes
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  },
  "exclude": ["**/test_*.py"]
}
"""
        )

        # Build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        assert code == 0

        # Verify both gitignore and exclude patterns applied
        output_file = tmp_path / "dist" / "bundle.zip"
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            # Should include __init__.py
            assert any("__init__.py" in n for n in names)
            assert any("module.py" in n for n in names)
    finally:
        os.chdir(original_cwd)
