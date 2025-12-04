# tests/50_core/test_cli_info.py
"""Tests for --info CLI flag (zipapp-style)."""

import zipfile
from pathlib import Path

import pytest

import zipbundler.build as mod_build
import zipbundler.cli as mod_main


def test_cli_info_with_shebang(tmp_path: Path) -> None:
    """Test --info displays interpreter from archive with shebang."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    output = tmp_path / "app.pyz"
    shebang = "#!/usr/bin/env python3"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=None,
        shebang=shebang,
    )

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func([str(output), "--info"])

    # Verify exit code is 0
    assert code == 0


def test_cli_info_no_shebang(tmp_path: Path) -> None:
    """Test --info displays message when archive has no shebang."""
    # Create a zip file without shebang manually
    output = tmp_path / "app.pyz"
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    # Create zip without shebang
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(pkg_dir / "__init__.py", "mypackage/__init__.py")

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func([str(output), "--info"])

    # Verify exit code is 0 (no error, just no interpreter)
    assert code == 0


def test_cli_info_file_not_found(tmp_path: Path) -> None:
    """Test --info fails with error for non-existent file."""
    non_existent = tmp_path / "nonexistent.pyz"

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func([str(non_existent), "--info"])

    # Verify exit code is 1 (error)
    assert code == 1


def test_cli_info_missing_source() -> None:
    """Test --info fails when SOURCE is not provided."""
    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main

    # argparse.error() raises SystemExit(2)
    argparse_error_code = 2
    with pytest.raises(SystemExit) as exc_info:
        main_func(["--info"])
    assert exc_info.value.code == argparse_error_code


def test_cli_info_custom_shebang(tmp_path: Path) -> None:
    """Test --info displays custom interpreter from archive."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    output = tmp_path / "app.pyz"
    custom_shebang = "#!/usr/bin/env python3.12"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=None,
        shebang=custom_shebang,
    )

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func([str(output), "--info"])

    # Verify exit code is 0
    assert code == 0


def test_cli_info_with_metadata(tmp_path: Path) -> None:
    """Test --info displays metadata from archive with PKG-INFO."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    output = tmp_path / "app.pyz"
    metadata = {
        "display_name": "Test Package",
        "description": "A test package",
        "version": "1.2.3",
        "author": "Test Author",
        "license": "MIT",
    }

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=None,
        shebang="#!/usr/bin/env python3",
        metadata=metadata,
    )

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func([str(output), "--info"])

    # Verify exit code is 0
    assert code == 0


def test_cli_info_with_partial_metadata(tmp_path: Path) -> None:
    """Test --info displays partial metadata from archive."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    output = tmp_path / "app.pyz"
    metadata = {
        "display_name": "Partial Package",
        "version": "2.0.0",
    }

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=None,
        shebang="#!/usr/bin/env python3",
        metadata=metadata,
    )

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func([str(output), "--info"])

    # Verify exit code is 0
    assert code == 0


def test_cli_info_without_metadata(tmp_path: Path) -> None:
    """Test --info works correctly when archive has no metadata."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    output = tmp_path / "app.pyz"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=None,
        shebang="#!/usr/bin/env python3",
        metadata=None,
    )

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    code = main_func([str(output), "--info"])

    # Verify exit code is 0 (should still work, just no metadata displayed)
    assert code == 0
