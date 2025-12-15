# tests/50_core/test_priv__cli_parser.py
# we import `_` private for testing purposes only
# ruff: noqa: SLF001
# pyright: reportPrivateUsage=false
"""Tests for private CLI parser function.

This module tests private CLI parser functions and intentionally accesses
private members that are not part of the public API. These tests validate
the internal structure of the CLI argument parsing.
"""

import zipbundler.cli as mod_cli
import zipbundler.constants as mod_constants


class TestCliDryRunParser:
    """Test --dry-run flag parsing via private _setup_parser."""

    def test_cli_dry_run_flag_has_correct_default(self) -> None:
        """Test that --dry-run flag uses DEFAULT_DRY_RUN as default."""
        parser = mod_cli._setup_parser()
        args = parser.parse_args(["--build"])
        # dry_run should match DEFAULT_DRY_RUN when not explicitly set
        assert args.dry_run == mod_constants.DEFAULT_DRY_RUN

    def test_cli_dry_run_flag_can_be_enabled(self) -> None:
        """Test that --dry-run flag can be explicitly enabled."""
        parser = mod_cli._setup_parser()
        args = parser.parse_args(["--build", "--dry-run"])
        assert args.dry_run is True


class TestCliMainModeParser:
    """Test --main-mode argument parsing via private _setup_parser."""

    def test_cli_main_mode_argument_exists(self) -> None:
        """Test that --main-mode CLI argument is available."""
        parser = mod_cli._setup_parser()
        args = parser.parse_args(["--build", "--main-mode", "auto"])
        assert hasattr(args, "main_mode")
        assert args.main_mode == "auto"

    def test_cli_main_mode_default_is_none(self) -> None:
        """Test that --main-mode defaults to None (uses config or constant)."""
        parser = mod_cli._setup_parser()
        args = parser.parse_args(["--build"])
        # When not specified, should be None (letting config/defaults take over)
        assert args.main_mode is None


class TestCliMainNameParser:
    """Test --main-name argument parsing via private _setup_parser."""

    def test_cli_main_name_argument_exists(self) -> None:
        """Test that --main-name CLI argument is available."""
        parser = mod_cli._setup_parser()
        args = parser.parse_args(["--build", "--main-name", "main"])
        assert hasattr(args, "main_name")
        assert args.main_name == "main"

    def test_cli_main_name_default_is_none(self) -> None:
        """Test that --main-name defaults to None (auto-detect)."""
        parser = mod_cli._setup_parser()
        args = parser.parse_args(["--build"])
        # When not specified, should be None
        assert args.main_name is None
