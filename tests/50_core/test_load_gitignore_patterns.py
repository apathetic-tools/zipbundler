# tests/50_core/test_load_gitignore_patterns.py
"""Tests for loading gitignore patterns from .gitignore files."""

from pathlib import Path

import zipbundler.utils as mod_utils


EXPECTED_BASIC_PATTERNS = 2
EXPECTED_PATTERNS_WITH_COMMENTS = 2
EXPECTED_EMPTY_LIST = 0
EXPECTED_THREE_PATTERNS = 3
EXPECTED_SEVEN_PATTERNS = 7
FILE_PERMISSIONS_NONE = 0o000


def test_load_gitignore_patterns_basic(tmp_path: Path) -> None:
    """Test loading basic .gitignore patterns."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.pyc\n__pycache__/\n")

    patterns = mod_utils.load_gitignore_patterns(gitignore)

    assert len(patterns) == EXPECTED_BASIC_PATTERNS
    assert patterns[0] == "*.pyc"
    assert patterns[1] == "__pycache__/"


def test_load_gitignore_patterns_with_comments(tmp_path: Path) -> None:
    """Test that comments in .gitignore are skipped."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text(
        """# Comment at start
*.pyc
# Another comment
__pycache__/
"""
    )

    patterns = mod_utils.load_gitignore_patterns(gitignore)

    assert len(patterns) == EXPECTED_PATTERNS_WITH_COMMENTS
    assert patterns[0] == "*.pyc"
    assert patterns[1] == "__pycache__/"


def test_load_gitignore_patterns_with_blank_and_whitespace_lines(
    tmp_path: Path,
) -> None:
    """Test that blank and whitespace-only lines in .gitignore are skipped."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text(
        """*.pyc

__pycache__/

*.log
\t
"""
    )

    patterns = mod_utils.load_gitignore_patterns(gitignore)

    assert len(patterns) == EXPECTED_THREE_PATTERNS
    assert patterns[0] == "*.pyc"
    assert patterns[1] == "__pycache__/"
    assert patterns[2] == "*.log"


def test_load_gitignore_patterns_missing_file(tmp_path: Path) -> None:
    """Test loading from non-existent .gitignore file returns empty list."""
    gitignore = tmp_path / ".gitignore"
    # Don't create the file

    patterns = mod_utils.load_gitignore_patterns(gitignore)

    assert patterns == []
    assert len(patterns) == EXPECTED_EMPTY_LIST


def test_load_gitignore_patterns_empty_file(tmp_path: Path) -> None:
    """Test loading empty .gitignore file returns empty list."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("")

    patterns = mod_utils.load_gitignore_patterns(gitignore)

    assert patterns == []
    assert len(patterns) == EXPECTED_EMPTY_LIST


def test_load_gitignore_patterns_only_comments(tmp_path: Path) -> None:
    """Test .gitignore with only comments returns empty list."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("# Comment 1\n# Comment 2\n# Comment 3\n")

    patterns = mod_utils.load_gitignore_patterns(gitignore)

    assert patterns == []
    assert len(patterns) == EXPECTED_EMPTY_LIST


def test_load_gitignore_patterns_read_error(tmp_path: Path) -> None:
    """Test that read errors are handled gracefully."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.pyc\n__pycache__/\n")

    # Remove read permissions
    original_mode = gitignore.stat().st_mode
    try:
        gitignore.chmod(FILE_PERMISSIONS_NONE)

        patterns = mod_utils.load_gitignore_patterns(gitignore)

        # Should return empty list on read error
        assert patterns == []
    finally:
        # Restore permissions for cleanup
        gitignore.chmod(original_mode)


def test_load_gitignore_patterns_leading_trailing_whitespace(
    tmp_path: Path,
) -> None:
    """Test that patterns with leading/trailing whitespace are trimmed."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("  *.pyc  \n\t__pycache__/\t\n")

    patterns = mod_utils.load_gitignore_patterns(gitignore)

    assert len(patterns) == EXPECTED_BASIC_PATTERNS
    assert patterns[0] == "*.pyc"
    assert patterns[1] == "__pycache__/"


def test_load_gitignore_patterns_complex_patterns(tmp_path: Path) -> None:
    """Test loading .gitignore with various pattern types."""
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text(
        """*.pyc
__pycache__/
test_*.py
*.log
.DS_Store
.env
node_modules/
"""
    )

    patterns = mod_utils.load_gitignore_patterns(gitignore)

    assert len(patterns) == EXPECTED_SEVEN_PATTERNS
    assert "*.pyc" in patterns
    assert "test_*.py" in patterns
    assert "node_modules/" in patterns
