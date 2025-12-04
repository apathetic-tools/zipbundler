# tests/50_core/test_build_incremental.py
"""Tests for incremental build functionality."""

import os
import time
from pathlib import Path

import zipbundler.build as mod_build
import zipbundler.cli as mod_main


def test_build_zipapp_skips_when_up_to_date(tmp_path: Path) -> None:
    """Test that build_zipapp skips rebuild when output is up-to-date."""
    # Create a package structure
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "bundle.pyz"

    # First build
    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        force=False,
    )

    # Verify output exists
    assert output.exists()
    first_mtime = output.stat().st_mtime

    # Wait a bit to ensure different mtime
    time.sleep(0.1)

    # Second build without force - should skip
    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        force=False,
    )

    # Verify mtime hasn't changed (rebuild was skipped)
    second_mtime = output.stat().st_mtime
    assert second_mtime == first_mtime


def test_build_zipapp_rebuilds_when_source_changed(tmp_path: Path) -> None:
    """Test that build_zipapp rebuilds when source files are modified."""
    # Create a package structure
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    module_file = pkg_dir / "module.py"
    module_file.write_text("def func():\n    pass\n")
    (pkg_dir / "__init__.py").write_text("")

    output = tmp_path / "bundle.pyz"

    # First build
    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        force=False,
    )

    # Verify output exists
    assert output.exists()
    first_mtime = output.stat().st_mtime

    # Wait a bit to ensure different mtime
    time.sleep(0.1)

    # Modify source file
    module_file.write_text("def func():\n    pass\n# modified\n")

    # Second build without force - should rebuild
    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        force=False,
    )

    # Verify mtime has changed (rebuild occurred)
    second_mtime = output.stat().st_mtime
    assert second_mtime > first_mtime


def test_build_zipapp_force_rebuilds_even_when_up_to_date(tmp_path: Path) -> None:
    """Test that build_zipapp rebuilds when force=True even if up-to-date."""
    # Create a package structure
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "bundle.pyz"

    # First build
    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        force=False,
    )

    # Verify output exists
    assert output.exists()
    first_mtime = output.stat().st_mtime

    # Wait a bit to ensure different mtime
    time.sleep(0.1)

    # Second build with force=True - should rebuild
    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        force=True,
    )

    # Verify mtime has changed (rebuild occurred)
    second_mtime = output.stat().st_mtime
    assert second_mtime > first_mtime


def test_build_zipapp_rebuilds_when_output_missing(tmp_path: Path) -> None:
    """Test that build_zipapp rebuilds when output file doesn't exist."""
    # Create a package structure
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "bundle.pyz"

    # Build when output doesn't exist - should build
    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        force=False,
    )

    # Verify output was created
    assert output.exists()


def test_build_zipapp_rebuilds_when_file_deleted_and_other_changed(
    tmp_path: Path,
) -> None:
    """Test that build_zipapp rebuilds when a file is deleted and another is modified.

    Note: When a file is deleted, it's no longer in the collected files list,
    so we can't detect it directly. However, if we modify another file after
    deletion, we should rebuild. This test verifies that scenario.
    """
    # Create a package structure
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    init_file = pkg_dir / "__init__.py"
    init_file.write_text("")
    module_file = pkg_dir / "module.py"
    module_file.write_text("def func():\n    pass\n")

    output = tmp_path / "bundle.pyz"

    # First build
    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        force=False,
    )

    # Verify output exists
    assert output.exists()
    first_mtime = output.stat().st_mtime

    # Wait a bit to ensure different mtime
    time.sleep(0.1)

    # Delete source file
    module_file.unlink()

    # Wait a bit more
    time.sleep(0.1)

    # Modify remaining file to trigger rebuild
    init_file.write_text("# modified\n")

    # Second build without force - should rebuild (file was modified)
    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        force=False,
    )

    # Verify mtime has changed (rebuild occurred)
    second_mtime = output.stat().st_mtime
    assert second_mtime > first_mtime


def test_cli_build_command_incremental(tmp_path: Path) -> None:
    """Test CLI build command with incremental builds."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        module_file = src_dir / "module.py"
        module_file.write_text("def func():\n    pass\n")

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

        # First build
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()
        first_mtime = output_file.stat().st_mtime

        # Wait a bit
        time.sleep(0.1)

        # Second build - should skip
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify mtime hasn't changed
        second_mtime = output_file.stat().st_mtime
        assert second_mtime == first_mtime

        # Wait a bit
        time.sleep(0.1)

        # Modify source file
        module_file.write_text("def func():\n    pass\n# modified\n")

        # Third build - should rebuild
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify mtime has changed
        third_mtime = output_file.stat().st_mtime
        assert third_mtime > second_mtime

        # Wait a bit
        time.sleep(0.1)

        # Fourth build with --force - should rebuild
        code = main_func(["--build", "--build-force"])

        # Verify exit code is 0
        assert code == 0

        # Verify mtime has changed
        fourth_mtime = output_file.stat().st_mtime
        assert fourth_mtime > third_mtime
    finally:
        os.chdir(original_cwd)
