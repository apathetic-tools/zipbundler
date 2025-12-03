# tests/50_core/test_zipapp_style_source.py
"""Tests for zipapp-style SOURCE building, including reading .pyz archives."""

import shutil
import zipfile
from pathlib import Path

import pytest

import zipbundler.build as mod_build
import zipbundler.cli as mod_main


def test_zipapp_style_from_directory(tmp_path: Path) -> None:
    """Test zipapp-style CLI building from a directory."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def hello():\n    print('hello')\n")

    output = tmp_path / "app.pyz"

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func([str(pkg_dir), "-o", str(output)])

    # Verify exit code is 0
    assert code == 0

    # Verify output file was created
    assert output.exists()

    # Verify zip file contains expected files
    with zipfile.ZipFile(output, "r") as zf:
        names = zf.namelist()
        assert any("mypackage/__init__.py" in name for name in names)
        assert any("mypackage/module.py" in name for name in names)


def test_zipapp_style_from_archive(tmp_path: Path) -> None:
    """Test zipapp-style CLI building from a .pyz archive."""
    # Create initial archive
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def hello():\n    print('hello')\n")

    initial_archive = tmp_path / "initial.pyz"
    mod_build.build_zipapp(
        output=initial_archive,
        packages=[pkg_dir],
        entry_point=None,
        shebang="#!/usr/bin/env python3",
    )

    # Now build a new archive from the initial archive
    output = tmp_path / "new.pyz"

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func([str(initial_archive), "-o", str(output)])

    # Verify exit code is 0
    assert code == 0

    # Verify output file was created
    assert output.exists()

    # Verify zip file contains expected files from original archive
    with zipfile.ZipFile(output, "r") as zf:
        names = zf.namelist()
        assert any("mypackage/__init__.py" in name for name in names)
        assert any("mypackage/module.py" in name for name in names)


def test_zipapp_style_from_archive_with_options(tmp_path: Path) -> None:
    """Test zipapp-style CLI building from archive with shebang and entry point."""
    # Create initial archive
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "main.py").write_text("def main():\n    print('hello')\n")

    initial_archive = tmp_path / "initial.pyz"
    mod_build.build_zipapp(
        output=initial_archive,
        packages=[pkg_dir],
        entry_point=None,
        shebang="#!/usr/bin/env python3",
    )

    # Build new archive with different shebang and entry point
    output = tmp_path / "new.pyz"

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func(
        [
            str(initial_archive),
            "-o",
            str(output),
            "-p",
            "/usr/bin/env python3.12",
            "-m",
            "mypackage.main:main",
        ]
    )

    # Verify exit code is 0
    assert code == 0

    # Verify output file was created
    assert output.exists()

    # Verify new shebang was applied
    interpreter = mod_build.get_interpreter(output)
    assert interpreter == "/usr/bin/env python3.12"

    # Verify entry point was added
    with zipfile.ZipFile(output, "r") as zf:
        assert "__main__.py" in zf.namelist()


def test_zipapp_style_from_archive_no_output(tmp_path: Path) -> None:
    """Test zipapp-style CLI fails when -o is not provided."""
    # Create initial archive
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    initial_archive = tmp_path / "initial.pyz"
    mod_build.build_zipapp(
        output=initial_archive,
        packages=[pkg_dir],
        entry_point=None,
    )

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func([str(initial_archive)])

    # Verify exit code is 1 (error - output required)
    assert code == 1


def test_zipapp_style_from_archive_compress(tmp_path: Path) -> None:
    """Test zipapp-style CLI building from archive with compression."""
    # Create initial archive
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    initial_archive = tmp_path / "initial.pyz"
    mod_build.build_zipapp(
        output=initial_archive,
        packages=[pkg_dir],
        entry_point=None,
        compress=False,  # Initial archive not compressed
    )

    # Build new archive with compression
    output = tmp_path / "new.pyz"

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func([str(initial_archive), "-o", str(output), "-c"])

    # Verify exit code is 0
    assert code == 0

    # Verify output file was created
    assert output.exists()

    # Verify compression was applied
    with zipfile.ZipFile(output, "r") as zf:
        # Check that at least one file has compression (ZIP_DEFLATED)
        for info in zf.infolist():
            if info.compress_type == zipfile.ZIP_DEFLATED:
                break
        else:
            # If we get here, no files were compressed
            pytest.fail("No compressed files found in archive")


def test_extract_archive_to_tempdir(tmp_path: Path) -> None:
    """Test extract_archive_to_tempdir function."""
    # Create a test archive
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def hello():\n    pass\n")

    archive = tmp_path / "test.pyz"
    mod_build.build_zipapp(
        output=archive,
        packages=[pkg_dir],
        entry_point=None,
        shebang="#!/usr/bin/env python3",
    )

    # Extract archive
    temp_dir = mod_build.extract_archive_to_tempdir(archive)

    try:
        # Verify temp directory exists
        assert temp_dir.exists()
        assert temp_dir.is_dir()

        # Verify files were extracted
        extracted_files = list(temp_dir.rglob("*.py"))
        assert len(extracted_files) > 0

        # Verify expected files are present
        file_names = [f.name for f in extracted_files]
        assert "__init__.py" in file_names or any(
            "__init__.py" in str(f) for f in extracted_files
        )
        assert "module.py" in file_names or any(
            "module.py" in str(f) for f in extracted_files
        )
    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)
