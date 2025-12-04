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
        compression="stored",  # Initial archive not compressed
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


def test_zipapp_style_from_archive_compression_level(tmp_path: Path) -> None:
    """Test zipapp-style CLI building from archive with compression level."""
    # Create initial archive
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    # Create a file with repetitive content that compresses well
    content = "def func():\n    " + "x" * 1000 + "\n    pass\n"
    (pkg_dir / "module.py").write_text(content)

    initial_archive = tmp_path / "initial.pyz"
    mod_build.build_zipapp(
        output=initial_archive,
        packages=[pkg_dir],
        entry_point=None,
        compression="stored",  # Initial archive not compressed
    )

    # Build new archive with compression and compression level
    output = tmp_path / "new.pyz"

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func(
        [str(initial_archive), "-o", str(output), "-c", "--compression-level", "9"]
    )

    # Verify exit code is 0
    assert code == 0

    # Verify output file was created
    assert output.exists()

    # Verify compression was applied with deflate
    with zipfile.ZipFile(output, "r") as zf:
        for info in zf.infolist():
            assert info.compress_type == zipfile.ZIP_DEFLATED


def test_zipapp_style_from_directory_compression_level(tmp_path: Path) -> None:
    """Test zipapp-style CLI building from directory with compression level."""
    # Create a test package with content that compresses well
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    content = "def func():\n    " + "x" * 1000 + "\n    pass\n"
    (pkg_dir / "module.py").write_text(content)

    output = tmp_path / "app.pyz"

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func(
        [str(pkg_dir), "-o", str(output), "-c", "--compression-level", "9"]
    )

    # Verify exit code is 0
    assert code == 0

    # Verify output file was created
    assert output.exists()

    # Verify compression was applied with deflate
    with zipfile.ZipFile(output, "r") as zf:
        for info in zf.infolist():
            assert info.compress_type == zipfile.ZIP_DEFLATED


def test_zipapp_style_package_discovery(tmp_path: Path) -> None:
    """Test zipapp-style CLI automatically discovers packages in a directory."""
    # Create a directory with multiple packages
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    # Create first package
    pkg1_dir = src_dir / "package1"
    pkg1_dir.mkdir()
    (pkg1_dir / "__init__.py").write_text("")
    (pkg1_dir / "module1.py").write_text("def func1():\n    pass\n")

    # Create second package
    pkg2_dir = src_dir / "package2"
    pkg2_dir.mkdir()
    (pkg2_dir / "__init__.py").write_text("")
    (pkg2_dir / "module2.py").write_text("def func2():\n    pass\n")

    # Create a non-package directory (no __init__.py)
    non_pkg_dir = src_dir / "not_a_package"
    non_pkg_dir.mkdir()
    (non_pkg_dir / "script.py").write_text("def script():\n    pass\n")

    output = tmp_path / "app.pyz"

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func([str(src_dir), "-o", str(output)])

    # Verify exit code is 0
    assert code == 0

    # Verify output file was created
    assert output.exists()

    # Verify zip file contains files from both discovered packages
    with zipfile.ZipFile(output, "r") as zf:
        names = zf.namelist()
        # Both packages should be discovered and included
        assert any("package1/__init__.py" in name for name in names)
        assert any("package1/module1.py" in name for name in names)
        assert any("package2/__init__.py" in name for name in names)
        assert any("package2/module2.py" in name for name in names)
        # Non-package directory should not be included (no __init__.py)
        assert not any("not_a_package" in name for name in names)


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
