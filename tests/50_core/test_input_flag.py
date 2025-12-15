# tests/50_core/test_input_flag.py
"""Tests for the --input flag functionality."""

import os
import zipfile
from pathlib import Path

import zipbundler.cli as mod_main


def test_cli_input_flag_basic_append(tmp_path: Path) -> None:
    """Test --input flag with existing zip in APPEND mode (default)."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create initial package structure
        src1_dir = tmp_path / "src" / "package1"
        src1_dir.mkdir(parents=True)
        (src1_dir / "__init__.py").write_text("")
        (src1_dir / "module1.py").write_text("def func1():\n    pass\n")

        # Create initial config and build
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/package1/**/*.py"],
  "output": {
    "path": "dist/bundle.pyz"
  }
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])
        assert code == 0

        # Verify initial zip was created
        output_file = tmp_path / "dist" / "bundle.pyz"
        assert output_file.exists()

        # Verify initial content
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("package1/__init__.py" in name for name in names)
            assert any("package1/module1.py" in name for name in names)

        # Now create a second package
        src2_dir = tmp_path / "src" / "package2"
        src2_dir.mkdir(parents=True)
        (src2_dir / "__init__.py").write_text("")
        (src2_dir / "module2.py").write_text("def func2():\n    pass\n")

        # Update config to include both packages
        config_file.write_text(
            """{
  "packages": ["src/package1/**/*.py", "src/package2/**/*.py"],
  "output": {
    "path": "dist/bundle.pyz"
  }
}
""",
            encoding="utf-8",
        )

        # Build with --input flag (defaults to APPEND mode)
        # This should merge package2 with existing files from archive
        code = main_func(["--build", "--input", "dist/bundle.pyz", "--force"])
        assert code == 0

        # Verify output file still exists
        assert output_file.exists()

        # Verify both packages are in the output (APPEND preserves package1)
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("package1/__init__.py" in name for name in names)
            assert any("package1/module1.py" in name for name in names)
            assert any("package2/__init__.py" in name for name in names)
            assert any("package2/module2.py" in name for name in names)

    finally:
        os.chdir(original_cwd)


def test_cli_input_flag_with_directory(tmp_path: Path) -> None:
    """Test --input flag with directory path."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create initial package
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func():\n    pass\n")

        # Create initial config and build
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

        # Initial build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])
        assert code == 0

        output_file = tmp_path / "dist" / "bundle.pyz"
        assert output_file.exists()

        # Update package with new file
        (src_dir / "new_module.py").write_text("def new_func():\n    pass\n")

        # Build with --input flag pointing to directory instead of file
        code = main_func(["--build", "--input", "dist", "--force"])
        assert code == 0

        # Verify all files are in the output
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("mypackage/__init__.py" in name for name in names)
            assert any("mypackage/module.py" in name for name in names)
            assert any("mypackage/new_module.py" in name for name in names)

    finally:
        os.chdir(original_cwd)


def test_cli_input_flag_nonexistent(tmp_path: Path) -> None:
    """Test --input flag with nonexistent file."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create package
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func():\n    pass\n")

        # Create config
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

        # Try to build with nonexistent input file
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--input", "dist/nonexistent.pyz"])

        # Should fail
        assert code == 1

    finally:
        os.chdir(original_cwd)


def test_cli_input_flag_preserves_files(tmp_path: Path) -> None:
    """Test that --input flag preserves files not being updated."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create initial package
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func():\n    pass\n")

        # Create config
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.pyz"
  },
  "metadata": {
    "display_name": "MyApp",
    "version": "1.0.0"
  }
}
""",
            encoding="utf-8",
        )

        # Initial build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])
        assert code == 0

        output_file = tmp_path / "dist" / "bundle.pyz"
        assert output_file.exists()

        # Verify PKG-INFO exists from initial build
        with zipfile.ZipFile(output_file, "r") as zf:
            assert "PKG-INFO" in zf.namelist()
            pkg_info = zf.read("PKG-INFO").decode("utf-8")
            assert "MyApp" in pkg_info
            assert "1.0.0" in pkg_info

        # Update a module without changing metadata
        (src_dir / "module.py").write_text("def func():\n    return 42\n")

        # Build with --input - should preserve PKG-INFO and other metadata
        code = main_func(["--build", "--input", "dist/bundle.pyz", "--force"])
        assert code == 0

        # Verify PKG-INFO is still there
        with zipfile.ZipFile(output_file, "r") as zf:
            assert "PKG-INFO" in zf.namelist()
            pkg_info = zf.read("PKG-INFO").decode("utf-8")
            assert "MyApp" in pkg_info
            assert "1.0.0" in pkg_info

    finally:
        os.chdir(original_cwd)


def test_cli_input_flag_replace_mode(tmp_path: Path) -> None:
    """Test --input with --replace flag (wipes existing files)."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create initial packages
        src1_dir = tmp_path / "src" / "package1"
        src1_dir.mkdir(parents=True)
        (src1_dir / "__init__.py").write_text("")
        (src1_dir / "module1.py").write_text("def func1():\n    pass\n")

        src2_dir = tmp_path / "src" / "package2"
        src2_dir.mkdir(parents=True)
        (src2_dir / "__init__.py").write_text("")
        (src2_dir / "module2.py").write_text("def func2():\n    pass\n")

        # Create config with package1
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/package1/**/*.py"],
  "output": {
    "path": "dist/bundle.pyz"
  }
}
""",
            encoding="utf-8",
        )

        # Initial build with package1
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])
        assert code == 0

        output_file = tmp_path / "dist" / "bundle.pyz"
        assert output_file.exists()

        # Verify only package1 is in output
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("package1/__init__.py" in name for name in names)
            assert any("package1/module1.py" in name for name in names)
            assert not any("package2" in name for name in names)

        # Update config to only include package2
        config_file.write_text(
            """{
  "packages": ["src/package2/**/*.py"],
  "output": {
    "path": "dist/bundle.pyz"
  }
}
""",
            encoding="utf-8",
        )

        # Build with --input and --replace (should wipe package1)
        code = main_func(
            ["--build", "--input", "dist/bundle.pyz", "--replace", "--force"]
        )
        assert code == 0

        # Verify ONLY package2 is in the output (package1 was wiped)
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            # Package2 should be present
            assert any("package2/__init__.py" in name for name in names)
            assert any("package2/module2.py" in name for name in names)
            # Package1 should NOT be present (was wiped in REPLACE mode)
            assert not any("package1" in name for name in names)

    finally:
        os.chdir(original_cwd)


def test_cli_input_flag_replace_shorthand(tmp_path: Path) -> None:
    """Test --input with -r shorthand for --replace."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create initial packages
        src1_dir = tmp_path / "src" / "package1"
        src1_dir.mkdir(parents=True)
        (src1_dir / "__init__.py").write_text("")
        (src1_dir / "module1.py").write_text("def func1():\n    pass\n")

        src2_dir = tmp_path / "src" / "package2"
        src2_dir.mkdir(parents=True)
        (src2_dir / "__init__.py").write_text("")
        (src2_dir / "module2.py").write_text("def func2():\n    pass\n")

        # Create config with package1
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/package1/**/*.py"],
  "output": {
    "path": "dist/bundle.pyz"
  }
}
""",
            encoding="utf-8",
        )

        # Initial build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])
        assert code == 0

        output_file = tmp_path / "dist" / "bundle.pyz"
        assert output_file.exists()

        # Update config to package2
        config_file.write_text(
            """{
  "packages": ["src/package2/**/*.py"],
  "output": {
    "path": "dist/bundle.pyz"
  }
}
""",
            encoding="utf-8",
        )

        # Build with -r shorthand for --replace
        code = main_func(["--build", "--input", "dist/bundle.pyz", "-r", "--force"])
        assert code == 0

        # Verify only package2 is present
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert any("package2/__init__.py" in name for name in names)
            assert any("package2/module2.py" in name for name in names)
            assert not any("package1" in name for name in names)

    finally:
        os.chdir(original_cwd)
