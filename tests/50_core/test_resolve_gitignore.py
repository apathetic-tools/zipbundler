# tests/50_core/test_resolve_gitignore.py
"""Tests for gitignore resolution with proper precedence handling."""

import argparse

import apathetic_utils as mod_apathetic_utils

import zipbundler.constants as mod_constants
import zipbundler.utils as mod_utils


def test_resolve_gitignore_default() -> None:
    """Test resolve_gitignore returns default when no config or CLI flag."""
    raw_config = mod_apathetic_utils.cast_hint(dict[str, object], {})
    args = argparse.Namespace(respect_gitignore=None)

    result = mod_utils.resolve_gitignore(raw_config, args=args)

    assert result is True
    assert result == mod_constants.DEFAULT_RESPECT_GITIGNORE


def test_resolve_gitignore_default_no_config() -> None:
    """Test resolve_gitignore with None config returns default."""
    args = argparse.Namespace(respect_gitignore=None)

    result = mod_utils.resolve_gitignore(None, args=args)

    assert result is True
    assert result == mod_constants.DEFAULT_RESPECT_GITIGNORE


def test_resolve_gitignore_precedence_cli_over_config_over_default() -> None:
    """Test complete precedence: CLI flag > config option > default."""
    # Case 1: Config True, default ignored
    raw_config = mod_apathetic_utils.cast_hint(
        dict[str, object], {"options": {"respect_gitignore": True}}
    )
    args = argparse.Namespace(respect_gitignore=None)
    assert mod_utils.resolve_gitignore(raw_config, args=args) is True

    # Case 2: Config False overrides default True
    raw_config = mod_apathetic_utils.cast_hint(
        dict[str, object], {"options": {"respect_gitignore": False}}
    )
    args = argparse.Namespace(respect_gitignore=None)
    result = mod_utils.resolve_gitignore(raw_config, args=args)
    assert result is False
    assert result != mod_constants.DEFAULT_RESPECT_GITIGNORE

    # Case 3: CLI True overrides config False
    raw_config = mod_apathetic_utils.cast_hint(
        dict[str, object], {"options": {"respect_gitignore": False}}
    )
    args = argparse.Namespace(respect_gitignore=True)
    assert mod_utils.resolve_gitignore(raw_config, args=args) is True

    # Case 4: CLI False overrides config True
    raw_config = mod_apathetic_utils.cast_hint(
        dict[str, object], {"options": {"respect_gitignore": True}}
    )
    args = argparse.Namespace(respect_gitignore=False)
    assert mod_utils.resolve_gitignore(raw_config, args=args) is False


def test_resolve_gitignore_empty_config_uses_default() -> None:
    """Test empty config falls back to default."""
    raw_config = mod_apathetic_utils.cast_hint(dict[str, object], {})
    args = argparse.Namespace(respect_gitignore=None)

    result = mod_utils.resolve_gitignore(raw_config, args=args)

    assert result is True
    assert result == mod_constants.DEFAULT_RESPECT_GITIGNORE


def test_resolve_gitignore_missing_options_key_uses_default() -> None:
    """Test config without options key falls back to default."""
    raw_config = mod_apathetic_utils.cast_hint(
        dict[str, object], {"packages": ["src/**/*.py"]}
    )
    args = argparse.Namespace(respect_gitignore=None)

    result = mod_utils.resolve_gitignore(raw_config, args=args)

    assert result is True
    assert result == mod_constants.DEFAULT_RESPECT_GITIGNORE


def test_resolve_gitignore_invalid_config_option_uses_default() -> None:
    """Test config with non-boolean value uses default."""
    raw_config = mod_apathetic_utils.cast_hint(
        dict[str, object], {"options": {"respect_gitignore": "yes"}}
    )
    args = argparse.Namespace(respect_gitignore=None)

    result = mod_utils.resolve_gitignore(raw_config, args=args)

    # Invalid type should fall back to default
    assert result is True
    assert result == mod_constants.DEFAULT_RESPECT_GITIGNORE


def test_resolve_gitignore_missing_respect_gitignore_option() -> None:
    """Test config without respect_gitignore uses default."""
    raw_config = mod_apathetic_utils.cast_hint(
        dict[str, object], {"options": {"other_option": True}}
    )
    args = argparse.Namespace(respect_gitignore=None)

    result = mod_utils.resolve_gitignore(raw_config, args=args)

    assert result is True
    assert result == mod_constants.DEFAULT_RESPECT_GITIGNORE
