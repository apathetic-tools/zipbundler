# tests/50_core/test_list_command.py
"""Tests for the list command."""

from pathlib import Path

import pytest

import zipbundler.build as mod_build
import zipbundler.cli as mod_main


EXPECTED_FILE_COUNT_BASIC = 2
EXPECTED_FILE_COUNT_MULTIPLE = 4
EXPECTED_FILE_COUNT_ARCHIVE = 2
ARGPARSE_ERROR_EXIT_CODE = 2


def test_list_files_basic(tmp_path: Path) -> None:
    """Test list_files function with a simple package."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    files = mod_build.list_files([pkg_dir])

    # Should find 2 files: __init__.py and module.py
    assert len(files) == EXPECTED_FILE_COUNT_BASIC
    arcnames = [arcname for _, arcname in files]
    assert Path("mypackage/__init__.py") in arcnames
    assert Path("mypackage/module.py") in arcnames


def test_list_files_multiple_packages(tmp_path: Path) -> None:
    """Test list_files function with multiple packages."""
    # Create two test packages
    pkg1_dir = tmp_path / "package1"
    pkg1_dir.mkdir()
    (pkg1_dir / "__init__.py").write_text("")
    (pkg1_dir / "mod1.py").write_text("def func1():\n    pass\n")

    pkg2_dir = tmp_path / "package2"
    pkg2_dir.mkdir()
    (pkg2_dir / "__init__.py").write_text("")
    (pkg2_dir / "mod2.py").write_text("def func2():\n    pass\n")

    files = mod_build.list_files([pkg1_dir, pkg2_dir])

    # Should find 4 files total
    assert len(files) == EXPECTED_FILE_COUNT_MULTIPLE
    arcnames = [str(arcname) for _, arcname in files]
    assert any("package1/__init__.py" in a for a in arcnames)
    assert any("package1/mod1.py" in a for a in arcnames)
    assert any("package2/__init__.py" in a for a in arcnames)
    assert any("package2/mod2.py" in a for a in arcnames)


def test_list_files_count_mode(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test list_files function with count mode."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    files = mod_build.list_files([pkg_dir], count=True)

    # Should return empty list when count=True
    assert files == []

    # Should have printed count
    captured = capsys.readouterr()
    assert "Files: 2" in captured.out


def test_list_files_empty_package(tmp_path: Path) -> None:
    """Test list_files function with empty package directory."""
    # Create an empty directory
    pkg_dir = tmp_path / "emptypackage"
    pkg_dir.mkdir()

    files = mod_build.list_files([pkg_dir])

    # Should find no files
    assert len(files) == 0


def test_list_files_nonexistent_package(tmp_path: Path) -> None:
    """Test list_files function with nonexistent package."""
    nonexistent = tmp_path / "nonexistent"

    # Should raise ValueError
    with pytest.raises(ValueError, match="At least one package must be provided"):
        mod_build.list_files([])

    # Should handle nonexistent path gracefully (warning, but continue)
    files = mod_build.list_files([nonexistent])
    assert len(files) == 0


def test_cli_list_command_basic(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test list command via CLI with basic output."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func(["list", str(pkg_dir)])

    # Verify exit code is 0
    assert code == 0

    # Verify output contains the files
    captured = capsys.readouterr()
    output = captured.out
    assert "mypackage/__init__.py" in output or "__init__.py" in output
    assert "mypackage/module.py" in output or "module.py" in output


def test_cli_list_command_count(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test list command via CLI with --count option."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func(["list", str(pkg_dir), "--count"])

    # Verify exit code is 0
    assert code == 0

    # Verify output contains count
    captured = capsys.readouterr()
    output = captured.out
    assert f"Files: {EXPECTED_FILE_COUNT_BASIC}" in output


def test_cli_list_command_tree(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test list command via CLI with --tree option."""
    # Create a test package with nested structure
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")
    subdir = pkg_dir / "subpackage"
    subdir.mkdir()
    (subdir / "__init__.py").write_text("")
    (subdir / "submodule.py").write_text("def subfunc():\n    pass\n")

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func(["list", str(pkg_dir), "--tree"])

    # Verify exit code is 0
    assert code == 0

    # Verify output contains tree structure
    captured = capsys.readouterr()
    output = captured.out
    # Tree should have tree characters
    assert "├──" in output or "└──" in output


def test_cli_list_command_multiple_packages(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test list command via CLI with multiple packages."""
    # Create two test packages
    pkg1_dir = tmp_path / "package1"
    pkg1_dir.mkdir()
    (pkg1_dir / "__init__.py").write_text("")

    pkg2_dir = tmp_path / "package2"
    pkg2_dir.mkdir()
    (pkg2_dir / "__init__.py").write_text("")

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func(["list", str(pkg1_dir), str(pkg2_dir)])

    # Verify exit code is 0
    assert code == 0

    # Verify output contains files from both packages
    captured = capsys.readouterr()
    output = captured.out
    assert "package1" in output or "__init__.py" in output
    assert "package2" in output or "__init__.py" in output


def test_cli_list_command_no_source() -> None:
    """Test list command via CLI without source argument."""
    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    # argparse raises SystemExit when required arguments are missing
    with pytest.raises(SystemExit) as exc_info:
        main_func(["list"])

    # Should exit with error code 2 (argparse error)
    assert exc_info.value.code == ARGPARSE_ERROR_EXIT_CODE


def test_list_files_from_archive_basic(tmp_path: Path) -> None:
    """Test list_files_from_archive function with a simple archive."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    # Create an archive
    archive = tmp_path / "app.pyz"
    mod_build.build_zipapp(
        output=archive,
        packages=[pkg_dir],
        entry_point=None,
        shebang="#!/usr/bin/env python3",
    )

    # List files from archive
    files = mod_build.list_files_from_archive(archive)

    # Should find Python files from the archive
    assert len(files) >= EXPECTED_FILE_COUNT_ARCHIVE
    arcnames = [str(arcname) for _, arcname in files]
    assert any("__init__.py" in a for a in arcnames)
    assert any("module.py" in a for a in arcnames)


def test_list_files_from_archive_with_entry_point(tmp_path: Path) -> None:
    """Test list_files_from_archive function with archive containing entry point."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    # Create an archive with entry point
    archive = tmp_path / "app.pyz"
    mod_build.build_zipapp(
        output=archive,
        packages=[pkg_dir],
        entry_point="from mypackage import func\nfunc()",
        shebang="#!/usr/bin/env python3",
    )

    # List files from archive
    files = mod_build.list_files_from_archive(archive)

    # Should find Python files including __main__.py
    arcnames = [str(arcname) for _, arcname in files]
    assert any("__main__.py" in a for a in arcnames)
    assert any("__init__.py" in a for a in arcnames)
    assert any("module.py" in a for a in arcnames)


def test_list_files_from_archive_count_mode(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test list_files_from_archive function with count mode."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    # Create an archive
    archive = tmp_path / "app.pyz"
    mod_build.build_zipapp(
        output=archive,
        packages=[pkg_dir],
        entry_point=None,
        shebang="#!/usr/bin/env python3",
    )

    # List files from archive with count
    files = mod_build.list_files_from_archive(archive, count=True)

    # Should return empty list when count=True
    assert files == []

    # Should have printed count
    captured = capsys.readouterr()
    assert "Files:" in captured.out


def test_list_files_from_archive_nonexistent(tmp_path: Path) -> None:
    """Test list_files_from_archive function with nonexistent archive."""
    nonexistent = tmp_path / "nonexistent.pyz"

    # Should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        mod_build.list_files_from_archive(nonexistent)


def test_cli_list_command_archive(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test list command via CLI with archive file."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    # Create an archive
    archive = tmp_path / "app.pyz"
    mod_build.build_zipapp(
        output=archive,
        packages=[pkg_dir],
        entry_point=None,
        shebang="#!/usr/bin/env python3",
    )

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func(["list", str(archive)])

    # Verify exit code is 0
    assert code == 0

    # Verify output contains the files
    captured = capsys.readouterr()
    output = captured.out
    assert "__init__.py" in output or "mypackage" in output
    assert "module.py" in output


def test_cli_list_command_archive_count(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test list command via CLI with archive file and --count option."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    # Create an archive
    archive = tmp_path / "app.pyz"
    mod_build.build_zipapp(
        output=archive,
        packages=[pkg_dir],
        entry_point=None,
        shebang="#!/usr/bin/env python3",
    )

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func(["list", str(archive), "--count"])

    # Verify exit code is 0
    assert code == 0

    # Verify output contains count
    captured = capsys.readouterr()
    output = captured.out
    assert "Files:" in output


def test_cli_list_command_archive_tree(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test list command via CLI with archive file and --tree option."""
    # Create a test package with nested structure
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")
    subdir = pkg_dir / "subpackage"
    subdir.mkdir()
    (subdir / "__init__.py").write_text("")
    (subdir / "submodule.py").write_text("def subfunc():\n    pass\n")

    # Create an archive
    archive = tmp_path / "app.pyz"
    mod_build.build_zipapp(
        output=archive,
        packages=[pkg_dir],
        entry_point=None,
        shebang="#!/usr/bin/env python3",
    )

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func(["list", str(archive), "--tree"])

    # Verify exit code is 0
    assert code == 0

    # Verify output contains tree structure
    captured = capsys.readouterr()
    output = captured.out
    # Tree should have tree characters
    assert "├──" in output or "└──" in output
