# tests/50_core/test_build_exclude.py
"""Tests for exclude pattern functionality."""

import zipfile
from pathlib import Path

import zipbundler.build as mod_build


EXPECTED_FILE_COUNT_TWO = 2


def test_build_zipapp_exclude_simple_pattern(tmp_path: Path) -> None:
    """Test build_zipapp with simple exclude pattern."""
    # Create a test package with multiple files
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")
    (pkg_dir / "test_module.py").write_text("def test_func():\n    pass\n")

    output = tmp_path / "output.pyz"

    # Build with exclude pattern for test files
    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        exclude=["**/test_*.py"],
    )

    # Verify zip was created
    assert output.exists()

    # Extract and verify test_module.py is excluded
    with zipfile.ZipFile(output, "r") as zf:
        names = zf.namelist()
        # Should have __init__.py and module.py, but not test_module.py
        assert "mypackage/__init__.py" in names or "__init__.py" in names
        assert "mypackage/module.py" in names or "module.py" in names
        assert "mypackage/test_module.py" not in names
        assert "test_module.py" not in names


def test_build_zipapp_exclude_directory_pattern(tmp_path: Path) -> None:
    """Test build_zipapp with directory exclude pattern."""
    # Create a test package with subdirectories
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    # Create tests subdirectory
    tests_dir = pkg_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_module.py").write_text("def test_func():\n    pass\n")

    # Create another subdirectory that should be included
    utils_dir = pkg_dir / "utils"
    utils_dir.mkdir()
    (utils_dir / "__init__.py").write_text("")
    (utils_dir / "helper.py").write_text("def helper():\n    pass\n")

    output = tmp_path / "output.pyz"

    # Build with exclude pattern for tests directory
    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        exclude=["**/tests/**"],
    )

    # Verify zip was created
    assert output.exists()

    # Extract and verify tests directory is excluded
    with zipfile.ZipFile(output, "r") as zf:
        names = zf.namelist()
        # Should have main files
        assert any("mypackage/__init__.py" in n or "__init__.py" in n for n in names)
        assert any("mypackage/module.py" in n or "module.py" in n for n in names)
        # Should have utils files
        assert any("utils" in n and "helper.py" in n for n in names)
        # Should NOT have tests files
        assert not any("tests" in n and "test_module.py" in n for n in names)
        assert not any("tests/__init__.py" in n for n in names)


def test_build_zipapp_exclude_multiple_patterns(tmp_path: Path) -> None:
    """Test build_zipapp with multiple exclude patterns."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")
    (pkg_dir / "test_module.py").write_text("def test_func():\n    pass\n")
    (pkg_dir / "temp_file.py").write_text("def temp():\n    pass\n")

    output = tmp_path / "output.pyz"

    # Build with multiple exclude patterns
    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        exclude=["**/test_*.py", "**/temp_*.py"],
    )

    # Verify zip was created
    assert output.exists()

    # Extract and verify excluded files are not present
    with zipfile.ZipFile(output, "r") as zf:
        names = zf.namelist()
        # Should have main files
        assert any("__init__.py" in n for n in names)
        assert any("module.py" in n and "test" not in n for n in names)
        # Should NOT have excluded files
        assert not any("test_module.py" in n for n in names)
        assert not any("temp_file.py" in n for n in names)


def test_build_zipapp_exclude_none(tmp_path: Path) -> None:
    """Test build_zipapp with no exclude patterns (all files included)."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "output.pyz"

    # Build without exclude patterns
    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        exclude=None,
    )

    # Verify zip was created
    assert output.exists()

    # Extract and verify all files are included
    with zipfile.ZipFile(output, "r") as zf:
        names = zf.namelist()
        assert any("__init__.py" in n for n in names)
        assert any("module.py" in n for n in names)


def test_list_files_exclude_simple_pattern(tmp_path: Path) -> None:
    """Test list_files with simple exclude pattern."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")
    (pkg_dir / "test_module.py").write_text("def test_func():\n    pass\n")

    # List files with exclude pattern
    files = mod_build.list_files([pkg_dir], exclude=["**/test_*.py"])

    # Should find 2 files (excluding test_module.py)
    assert len(files) == EXPECTED_FILE_COUNT_TWO
    arcnames = [str(arcname) for _, arcname in files]
    assert any("__init__.py" in a for a in arcnames)
    assert any("module.py" in a and "test" not in a for a in arcnames)
    assert not any("test_module.py" in a for a in arcnames)


def test_list_files_exclude_directory_pattern(tmp_path: Path) -> None:
    """Test list_files with directory exclude pattern."""
    # Create a test package with subdirectories
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    # Create tests subdirectory
    tests_dir = pkg_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_module.py").write_text("def test_func():\n    pass\n")

    # List files with exclude pattern
    files = mod_build.list_files([pkg_dir], exclude=["**/tests/**"])

    # Should find 2 files (excluding tests directory)
    assert len(files) == EXPECTED_FILE_COUNT_TWO
    arcnames = [str(arcname) for _, arcname in files]
    assert not any("tests" in a for a in arcnames)


def test_list_files_exclude_none(tmp_path: Path) -> None:
    """Test list_files with no exclude patterns (all files included)."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    # List files without exclude patterns
    files = mod_build.list_files([pkg_dir], exclude=None)

    # Should find all files
    assert len(files) == EXPECTED_FILE_COUNT_TWO
    arcnames = [str(arcname) for _, arcname in files]
    assert any("__init__.py" in a for a in arcnames)
    assert any("module.py" in a for a in arcnames)


def test_build_zipapp_exclude_dry_run(tmp_path: Path) -> None:
    """Test build_zipapp dry run with exclude patterns."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")
    (pkg_dir / "test_module.py").write_text("def test_func():\n    pass\n")

    output = tmp_path / "output.pyz"

    # Build with exclude pattern in dry run mode
    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        exclude=["**/test_*.py"],
        dry_run=True,
    )

    # Verify zip was NOT created (dry run)
    assert not output.exists()
