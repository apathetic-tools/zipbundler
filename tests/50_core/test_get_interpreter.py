# tests/50_core/test_get_interpreter.py
"""Tests for get_interpreter functionality."""

import zipfile
from pathlib import Path

import pytest

import zipbundler.build as mod_build
import zipbundler.main as mod_main


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


def test_cli_info_flag(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test --info flag in CLI."""
    # Create a test package and build zipapp
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

    # Test --info flag
    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    result = main_func([str(output), "--info"])
    assert result == 0

    captured = capsys.readouterr()
    # Extract just the interpreter line (last line of output)
    output_lines = captured.out.strip().split("\n")
    assert output_lines[-1] == "/usr/bin/env python3"


def test_cli_info_flag_no_shebang(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test --info flag with zipapp that has no shebang."""
    # Create a zip file without shebang manually
    output = tmp_path / "app.pyz"
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(pkg_dir / "__init__.py", "mypackage/__init__.py")

    # Test --info flag
    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    result = main_func([str(output), "--info"])
    assert result == 1

    captured = capsys.readouterr()
    # Check if the error message is in the output (could be in stdout or stderr)
    assert (
        "No interpreter specified" in captured.out
        or "No interpreter specified" in captured.err
    )


def test_cli_info_flag_file_not_found(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test --info flag with non-existent file."""
    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    result = main_func(["nonexistent.pyz", "--info"])
    assert result == 1

    captured = capsys.readouterr()
    assert "Archive not found" in captured.err or "Archive not found" in captured.out
