# tests/50_core/test_watch_gitignore.py
"""Tests for gitignore integration with watch command."""

from pathlib import Path

import zipbundler.actions as mod_actions
import zipbundler.config.config_types as mod_config_types
import zipbundler.utils as mod_utils


EXPECTED_FILES_BASIC = 2
EXPECTED_FILES_WITH_EXCLUDE = 1
EXPECTED_THREE_FILES = 3


def test_watch_respects_gitignore_by_default(tmp_path: Path) -> None:
    """Test that watch respects .gitignore patterns by default."""
    # Create a test package with files to be ignored
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    # Create .gitignore
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.pyc\n")

    # Load gitignore patterns and create excludes
    patterns = mod_utils.load_gitignore_patterns(gitignore)
    assert len(patterns) == 1
    assert patterns[0] == "*.pyc"

    # Create excludes from gitignore patterns
    excludes: list[mod_config_types.PathResolved] = [
        mod_utils.make_exclude_resolved(p, tmp_path, "gitignore") for p in patterns
    ]

    # Collect watched files with gitignore excludes
    files = mod_actions.collect_watched_files([pkg_dir], exclude=excludes)

    # Should find only 2 .py files (gitignore patterns don't affect .py files)
    assert len(files) == EXPECTED_FILES_BASIC
    assert pkg_dir / "__init__.py" in files
    assert pkg_dir / "module.py" in files


def test_watch_with_empty_gitignore(tmp_path: Path) -> None:
    """Test that watch works with empty .gitignore."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    # Create empty .gitignore
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("")

    # Load gitignore patterns
    patterns = mod_utils.load_gitignore_patterns(gitignore)
    assert patterns == []

    # No excludes since gitignore is empty
    excludes: list[mod_config_types.PathResolved] = []

    # Collect watched files
    files = mod_actions.collect_watched_files([pkg_dir], exclude=excludes)

    # Should find all files
    assert len(files) == EXPECTED_FILES_BASIC
    assert pkg_dir / "__init__.py" in files
    assert pkg_dir / "module.py" in files


def test_load_gitignore_patterns_from_file(tmp_path: Path) -> None:
    """Test that gitignore patterns are correctly loaded from file."""
    # Create .gitignore
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.pyc\n__pycache__/\ntest_*.py\n")

    # Load gitignore patterns
    patterns = mod_utils.load_gitignore_patterns(gitignore)

    # Should have 3 patterns
    assert len(patterns) == EXPECTED_THREE_FILES
    assert "*.pyc" in patterns
    assert "__pycache__/" in patterns
    assert "test_*.py" in patterns


def test_watch_with_no_gitignore_file(tmp_path: Path) -> None:
    """Test that watch works when .gitignore doesn't exist."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    # Don't create .gitignore

    # Load gitignore patterns (from non-existent file)
    gitignore = tmp_path / ".gitignore"
    patterns = mod_utils.load_gitignore_patterns(gitignore)
    assert patterns == []

    # No excludes
    excludes: list[mod_config_types.PathResolved] = []

    # Collect watched files
    files = mod_actions.collect_watched_files([pkg_dir], exclude=excludes)

    # Should find only .py files (no gitignore to filter)
    assert len(files) == EXPECTED_FILES_BASIC
    assert pkg_dir / "__init__.py" in files
    assert pkg_dir / "module.py" in files


def test_gitignore_patterns_integration(tmp_path: Path) -> None:
    """Test gitignore patterns work end-to-end with exclude resolution."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    # Create .gitignore with multiple patterns
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.pyc\n*.log\n__pycache__/\n")

    # Load gitignore patterns
    patterns = mod_utils.load_gitignore_patterns(gitignore)
    assert len(patterns) == EXPECTED_THREE_FILES

    # Create excludes from all patterns
    excludes: list[mod_config_types.PathResolved] = [
        mod_utils.make_exclude_resolved(p, tmp_path, "gitignore") for p in patterns
    ]

    # Verify we can create excludes from gitignore patterns
    assert len(excludes) == EXPECTED_THREE_FILES
    for exc in excludes:
        assert exc["origin"] == "gitignore"

    # Collect watched files (patterns don't affect .py collection)
    files = mod_actions.collect_watched_files([pkg_dir], exclude=excludes)

    # Should find our .py files
    assert len(files) == EXPECTED_FILES_BASIC
    assert pkg_dir / "__init__.py" in files
    assert pkg_dir / "module.py" in files
