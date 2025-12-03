# tests/50_core/test_build_dry_run.py
"""Tests for dry-run mode in zipapp building."""

from pathlib import Path

import pytest

import zipbundler.build as mod_build
import zipbundler.main as mod_main


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


def test_cli_dry_run_flag(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test that --dry-run flag works via CLI."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "app.pyz"

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func([str(pkg_dir), "-o", str(output), "--dry-run"])

    # Verify exit code is 0
    assert code == 0

    # Verify zip file was NOT created
    assert not output.exists()

    # Verify dry-run message appears in output
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "dry-run" in combined.lower() or "would create" in combined.lower()


def test_cli_dry_run_without_output(tmp_path: Path) -> None:
    """Test that --dry-run works without --output flag."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func([str(pkg_dir), "--dry-run"])

    # Verify exit code is 0 (should not error about missing --output)
    assert code == 0


def test_cli_dry_run_with_entry_point(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test --dry-run flag with entry point via CLI."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "main.py").write_text("def main():\n    pass\n")

    output = tmp_path / "app.pyz"

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func(
        [str(pkg_dir), "-o", str(output), "-m", "mypackage.main:main", "--dry-run"]
    )

    # Verify exit code is 0
    assert code == 0

    # Verify zip file was NOT created
    assert not output.exists()

    # Verify dry-run message appears
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "dry-run" in combined.lower() or "would create" in combined.lower()
