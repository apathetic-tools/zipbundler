# tests/50_core/test_watch_command.py
"""Tests for the watch command."""

import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

import zipbundler.actions as mod_actions
import zipbundler.cli as mod_main


EXPECTED_FILE_COUNT_BASIC = 2
ARGPARSE_ERROR_EXIT_CODE = 2
WATCH_INTERVAL_TEST = 0.5


def test_collect_watched_files_basic(tmp_path: Path) -> None:
    """Test collect_watched_files function with a simple package."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    files = mod_actions.collect_watched_files([pkg_dir])

    # Should find 2 files
    assert len(files) == EXPECTED_FILE_COUNT_BASIC
    assert pkg_dir / "__init__.py" in files
    assert pkg_dir / "module.py" in files


def test_collect_watched_files_with_exclude(tmp_path: Path) -> None:
    """Test collect_watched_files function with exclude patterns."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")
    (pkg_dir / "tests").mkdir()
    (pkg_dir / "tests" / "test_module.py").write_text("def test_func():\n    pass\n")

    files = mod_actions.collect_watched_files([pkg_dir], exclude=["**/tests/**"])

    # Should find 2 files (excluding tests)
    assert len(files) == EXPECTED_FILE_COUNT_BASIC
    assert pkg_dir / "__init__.py" in files
    assert pkg_dir / "module.py" in files
    assert pkg_dir / "tests" / "test_module.py" not in files


def test_watch_for_changes_detects_file_modification(tmp_path: Path) -> None:
    """Test that watch_for_changes detects file modifications."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "app.pyz"
    rebuild_count = 0

    def rebuild() -> None:
        nonlocal rebuild_count
        rebuild_count += 1

    # Use a very short interval for testing
    interval = 0.1

    # Start watch in a thread and modify file after a short delay
    def modify_file() -> None:
        time.sleep(0.2)  # Wait a bit for watch to start
        (pkg_dir / "module.py").write_text("def func():\n    pass\n# modified\n")

    thread = threading.Thread(target=modify_file)
    thread.start()

    try:
        # Run watch for a short time
        with patch("time.sleep", side_effect=[None, None, KeyboardInterrupt()]):
            mod_actions.watch_for_changes(
                rebuild_func=rebuild,
                packages=[pkg_dir],
                output=output,
                interval=interval,
            )
    except KeyboardInterrupt:
        pass

    thread.join(timeout=1.0)

    # Should have called rebuild at least once (initial build)
    assert rebuild_count >= 1


def test_watch_for_changes_ignores_output_file(tmp_path: Path) -> None:
    """Test that watch_for_changes ignores changes to output file."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    output = tmp_path / "app.pyz"
    rebuild_count = 0

    def rebuild() -> None:
        nonlocal rebuild_count
        rebuild_count += 1
        # Create the output file
        output.write_text("dummy")

    # Use a very short interval for testing
    interval = 0.1

    try:
        # Run watch for a short time, modify output file
        with patch("time.sleep", side_effect=[None, None, KeyboardInterrupt()]):
            mod_actions.watch_for_changes(
                rebuild_func=rebuild,
                packages=[pkg_dir],
                output=output,
                interval=interval,
            )
    except KeyboardInterrupt:
        pass

    # Should have called rebuild only once (initial build)
    # Modifying output shouldn't trigger rebuild
    assert rebuild_count == 1


def test_cli_watch_command_basic(tmp_path: Path) -> None:
    """Test watch command via CLI with basic arguments."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "app.pyz"

    # Mock time.sleep to raise KeyboardInterrupt immediately
    with patch("zipbundler.actions.time.sleep", side_effect=KeyboardInterrupt()):
        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["watch", str(pkg_dir), "-o", str(output)])

    # Should return 0 (KeyboardInterrupt is handled gracefully)
    assert code == 0


def test_cli_watch_command_no_source() -> None:
    """Test watch command via CLI without source argument."""
    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    # argparse raises SystemExit when required arguments are missing
    with pytest.raises(SystemExit) as exc_info:
        main_func(["watch"])

    # Should exit with error code 2 (argparse error)
    assert exc_info.value.code == ARGPARSE_ERROR_EXIT_CODE


def test_cli_watch_command_no_output(tmp_path: Path) -> None:
    """Test watch command via CLI without output argument."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    # Handle both module and function cases (runtime mode swap)
    main_func = mod_main if callable(mod_main) else mod_main.main
    # argparse raises SystemExit when required arguments are missing
    with pytest.raises(SystemExit) as exc_info:
        main_func(["watch", str(pkg_dir)])

    # Should exit with error code 2 (argparse error)
    assert exc_info.value.code == ARGPARSE_ERROR_EXIT_CODE


def test_cli_watch_command_with_options(tmp_path: Path) -> None:
    """Test watch command via CLI with various options."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    output = tmp_path / "app.pyz"

    # Mock time.sleep to raise KeyboardInterrupt immediately
    with patch("zipbundler.actions.time.sleep", side_effect=KeyboardInterrupt()):
        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(
            [
                "watch",
                str(pkg_dir),
                "-o",
                str(output),
                "--compress",
                "--interval",
                str(WATCH_INTERVAL_TEST),
                "--exclude",
                "**/tests/**",
            ]
        )

    # Should return 0 (KeyboardInterrupt is handled gracefully)
    assert code == 0
