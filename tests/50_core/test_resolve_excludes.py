# tests/50_core/test_resolve_excludes.py
"""Tests for exclude resolution with proper path semantics."""

import argparse
from pathlib import Path

import apathetic_utils as mod_apathetic_utils

import zipbundler.utils as mod_utils


EXPECTED_COUNT_1 = 1
EXPECTED_COUNT_2 = 2
EXPECTED_COUNT_3 = 3


def test_resolve_excludes_from_config(tmp_path: Path) -> None:
    """Test resolve_excludes with config-based excludes."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    cwd = tmp_path / "cwd"
    cwd.mkdir()

    # Config with excludes
    raw_config = mod_apathetic_utils.cast_hint(
        dict[str, object], {"exclude": ["**/test_*.py", "**/tmp_*.py"]}
    )
    args = argparse.Namespace(exclude=None, add_exclude=None)

    excludes = mod_utils.resolve_excludes(
        raw_config, args=args, config_dir=config_dir, cwd=cwd
    )

    # Should have 2 excludes from config
    assert len(excludes) == EXPECTED_COUNT_2
    # All should have config_dir as root
    for exc in excludes:
        assert exc["root"] == config_dir
        assert exc["origin"] == "config"
    # Check patterns
    assert excludes[0]["path"] == "**/test_*.py"
    assert excludes[1]["path"] == "**/tmp_*.py"


def test_resolve_excludes_cli_override(tmp_path: Path) -> None:
    """Test --exclude overrides config excludes."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    cwd = tmp_path / "cwd"
    cwd.mkdir()

    # Config with excludes (should be ignored)
    raw_config = mod_apathetic_utils.cast_hint(
        dict[str, object], {"exclude": ["**/test_*.py"]}
    )
    args = argparse.Namespace(exclude=["**/cli_*.py"], add_exclude=None)

    excludes = mod_utils.resolve_excludes(
        raw_config, args=args, config_dir=config_dir, cwd=cwd
    )

    # Should have only CLI exclude (config ignored)
    assert len(excludes) == EXPECTED_COUNT_1
    assert excludes[0]["path"] == "**/cli_*.py"
    assert excludes[0]["root"] == cwd
    assert excludes[0]["origin"] == "cli"


def test_resolve_excludes_add_exclude(tmp_path: Path) -> None:
    """Test --add-exclude extends config excludes."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    cwd = tmp_path / "cwd"
    cwd.mkdir()

    # Config with excludes
    raw_config = mod_apathetic_utils.cast_hint(
        dict[str, object], {"exclude": ["**/test_*.py"]}
    )
    args = argparse.Namespace(
        exclude=None, add_exclude=["**/cli_*.py", "**/extra_*.py"]
    )

    excludes = mod_utils.resolve_excludes(
        raw_config, args=args, config_dir=config_dir, cwd=cwd
    )

    # Should have 3 excludes: 1 from config + 2 from CLI
    assert len(excludes) == EXPECTED_COUNT_3

    # First from config
    assert excludes[0]["path"] == "**/test_*.py"
    assert excludes[0]["root"] == config_dir
    assert excludes[0]["origin"] == "config"

    # Next 2 from CLI
    assert excludes[1]["path"] == "**/cli_*.py"
    assert excludes[1]["root"] == cwd
    assert excludes[1]["origin"] == "cli"

    assert excludes[2]["path"] == "**/extra_*.py"
    assert excludes[2]["root"] == cwd
    assert excludes[2]["origin"] == "cli"


def test_resolve_excludes_root_context(tmp_path: Path) -> None:
    """Test that each exclude pattern uses its own root."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    cwd = tmp_path / "cwd"
    cwd.mkdir()

    # Config with excludes
    raw_config = mod_apathetic_utils.cast_hint(
        dict[str, object], {"exclude": ["**/test_*.py"]}
    )
    args = argparse.Namespace(exclude=None, add_exclude=["**/local_*.py"])

    excludes = mod_utils.resolve_excludes(
        raw_config, args=args, config_dir=config_dir, cwd=cwd
    )

    # Config exclude uses config_dir
    assert excludes[0]["root"] == config_dir

    # CLI exclude uses cwd
    assert excludes[1]["root"] == cwd

    # Roots should be different
    assert excludes[0]["root"] != excludes[1]["root"]


def test_resolve_excludes_precedence(tmp_path: Path) -> None:
    """Test three-case precedence: --exclude > config > --add-exclude."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    cwd = tmp_path / "cwd"
    cwd.mkdir()

    raw_config = mod_apathetic_utils.cast_hint(
        dict[str, object], {"exclude": ["**/test_*.py"]}
    )

    # Case 1: --exclude provided (full override)
    args = argparse.Namespace(exclude=["**/override_*.py"], add_exclude=["**/add_*.py"])
    excludes = mod_utils.resolve_excludes(
        raw_config, args=args, config_dir=config_dir, cwd=cwd
    )
    # Should only have --exclude, not config or --add-exclude
    assert len(excludes) == EXPECTED_COUNT_1
    assert excludes[0]["path"] == "**/override_*.py"

    # Case 2: Only config excludes
    args = argparse.Namespace(exclude=None, add_exclude=None)
    excludes = mod_utils.resolve_excludes(
        raw_config, args=args, config_dir=config_dir, cwd=cwd
    )
    # Should only have config
    assert len(excludes) == EXPECTED_COUNT_1
    assert excludes[0]["path"] == "**/test_*.py"

    # Case 3: Config + --add-exclude
    args = argparse.Namespace(exclude=None, add_exclude=["**/add_*.py"])
    excludes = mod_utils.resolve_excludes(
        raw_config, args=args, config_dir=config_dir, cwd=cwd
    )
    # Should have both config and --add-exclude
    assert len(excludes) == EXPECTED_COUNT_2
    assert excludes[0]["path"] == "**/test_*.py"
    assert excludes[1]["path"] == "**/add_*.py"


def test_resolve_excludes_empty(tmp_path: Path) -> None:
    """Test resolve_excludes with no excludes returns empty list."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    cwd = tmp_path / "cwd"
    cwd.mkdir()

    raw_config: dict[str, object] = {}  # No exclude field
    args = argparse.Namespace(exclude=None, add_exclude=None)

    excludes = mod_utils.resolve_excludes(
        raw_config, args=args, config_dir=config_dir, cwd=cwd
    )

    assert len(excludes) == 0
    assert excludes == []


def test_resolve_excludes_no_config(tmp_path: Path) -> None:
    """Test resolve_excludes with no config file."""
    cwd = tmp_path / "cwd"
    cwd.mkdir()

    # No config, only CLI args
    args = argparse.Namespace(exclude=["**/test_*.py"], add_exclude=["**/extra_*.py"])

    excludes = mod_utils.resolve_excludes(None, args=args, config_dir=cwd, cwd=cwd)

    # --exclude takes precedence, --add-exclude is ignored
    assert len(excludes) == 1
    assert excludes[0]["path"] == "**/test_*.py"
