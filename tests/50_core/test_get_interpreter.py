# tests/50_core/test_get_interpreter.py
"""Tests for get_interpreter functionality."""

import zipfile
from pathlib import Path

import pytest

import zipbundler.build as mod_build


def test_get_interpreter_with_shebang(tmp_path: Path) -> None:
    """Test getting interpreter from zipapp with shebang."""
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

    # Get interpreter
    interpreter = mod_build.get_interpreter(output)
    assert interpreter == "/usr/bin/env python3"


def test_get_interpreter_custom_shebang(tmp_path: Path) -> None:
    """Test getting interpreter from zipapp with custom shebang."""
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

    # Get interpreter
    interpreter = mod_build.get_interpreter(output)
    assert interpreter == "/usr/bin/env python3.12"


def test_get_interpreter_no_shebang(tmp_path: Path) -> None:
    """Test getting interpreter from zipapp without shebang."""
    # Create a zip file without shebang manually
    output = tmp_path / "app.pyz"
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    # Create zip without shebang
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(pkg_dir / "__init__.py", "mypackage/__init__.py")

    # Get interpreter should return None
    interpreter = mod_build.get_interpreter(output)
    assert interpreter is None


def test_get_interpreter_file_not_found(tmp_path: Path) -> None:
    """Test get_interpreter raises FileNotFoundError for non-existent file."""
    non_existent = tmp_path / "nonexistent.pyz"

    with pytest.raises(FileNotFoundError, match="Archive not found"):
        mod_build.get_interpreter(non_existent)


def test_get_interpreter_with_entry_point(tmp_path: Path) -> None:
    """Test getting interpreter from zipapp with entry point."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "main.py").write_text("def main():\n    pass\n")

    output = tmp_path / "app.pyz"
    shebang = "#!/usr/bin/env python3"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point="from mypackage.main import main; main()",
        shebang=shebang,
    )

    # Get interpreter should still work
    interpreter = mod_build.get_interpreter(output)
    assert interpreter == "/usr/bin/env python3"


# CLI tests removed - old zipapp-style CLI no longer exists
