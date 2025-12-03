# tests/50_core/test_build_dry_run.py
"""Tests for dry-run mode in zipapp building."""

from pathlib import Path

import zipbundler.build as mod_build


def test_build_zipapp_dry_run_does_not_create_file(tmp_path: Path) -> None:
    """Test that dry-run mode does not create the output file."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "app.pyz"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=None,
        dry_run=True,
    )

    # Verify zip file was NOT created
    assert not output.exists()


def test_build_zipapp_dry_run_with_entry_point(tmp_path: Path) -> None:
    """Test dry-run mode with an entry point."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def main():\n    pass\n")

    output = tmp_path / "app.pyz"
    entry_point = "from mypackage.module import main; main()"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=entry_point,
        dry_run=True,
    )

    # Verify zip file was NOT created
    assert not output.exists()


def test_build_zipapp_dry_run_with_compression(tmp_path: Path) -> None:
    """Test dry-run mode with compression enabled."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    output = tmp_path / "app.pyz"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=None,
        compress=True,
        dry_run=True,
    )

    # Verify zip file was NOT created
    assert not output.exists()


def test_build_zipapp_dry_run_multiple_packages(tmp_path: Path) -> None:
    """Test dry-run mode with multiple packages."""
    # Create two test packages
    pkg1_dir = tmp_path / "package1"
    pkg1_dir.mkdir()
    (pkg1_dir / "__init__.py").write_text("")
    (pkg1_dir / "mod1.py").write_text("def func1():\n    pass\n")

    pkg2_dir = tmp_path / "package2"
    pkg2_dir.mkdir()
    (pkg2_dir / "__init__.py").write_text("")
    (pkg2_dir / "mod2.py").write_text("def func2():\n    pass\n")

    output = tmp_path / "app.pyz"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg1_dir, pkg2_dir],
        entry_point=None,
        dry_run=True,
    )

    # Verify zip file was NOT created
    assert not output.exists()


# CLI tests removed - old zipapp-style CLI no longer exists
