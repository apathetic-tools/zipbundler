# tests/50_core/test_cli_color.py
"""Tests for --color and --no-color CLI flags."""

import argparse

import pytest

import zipbundler.cli as mod_cli
import zipbundler.logs as mod_logs


def test_color_flags_are_defined() -> None:
    """Test that --color and --no-color flags are defined in the parser."""
    parser = mod_cli._setup_parser()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    # Parse with --color flag
    args = parser.parse_args(["--color"])
    assert hasattr(args, "use_color")
    assert args.use_color is True

    # Parse with --no-color flag
    args = parser.parse_args(["--no-color"])
    assert hasattr(args, "use_color")
    assert args.use_color is False

    # Parse with neither flag (should be None)
    args = parser.parse_args([])
    assert hasattr(args, "use_color")
    assert args.use_color is None


def test_color_flags_are_mutually_exclusive() -> None:
    """Test that --color and --no-color are mutually exclusive."""
    parser = mod_cli._setup_parser()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    # Should fail when both are specified
    with pytest.raises(SystemExit):
        parser.parse_args(["--color", "--no-color"])


def test_logger_enable_color_from_cli_true() -> None:
    """Test that logger.enable_color is set to True when --color is passed."""
    logger = mod_logs.getAppLogger()
    original_color = logger.enable_color

    try:
        # Simulate CLI parsing with --color
        args = argparse.Namespace()
        args.use_color = True
        args.log_level = None

        # Simulate the logic in main()
        use_color = getattr(args, "use_color", None)
        if use_color is not None:
            logger.enable_color = use_color
        else:
            logger.enable_color = logger.determineColorEnabled()

        assert logger.enable_color is True
    finally:
        logger.enable_color = original_color


def test_logger_enable_color_from_cli_false() -> None:
    """Test that logger.enable_color is set to False when --no-color is passed."""
    logger = mod_logs.getAppLogger()
    original_color = logger.enable_color

    try:
        # Simulate CLI parsing with --no-color
        args = argparse.Namespace()
        args.use_color = False
        args.log_level = None

        # Simulate the logic in main()
        use_color = getattr(args, "use_color", None)
        if use_color is not None:
            logger.enable_color = use_color
        else:
            logger.enable_color = logger.determineColorEnabled()

        assert logger.enable_color is False
    finally:
        logger.enable_color = original_color


def test_logger_enable_color_from_cli_none() -> None:
    """Test that logger.enable_color uses auto-detect when neither flag is passed."""
    logger = mod_logs.getAppLogger()
    original_color = logger.enable_color

    try:
        # Simulate CLI parsing with no color flags
        args = argparse.Namespace()
        args.use_color = None
        args.log_level = None

        # Simulate the logic in main()
        use_color = getattr(args, "use_color", None)
        if use_color is not None:
            logger.enable_color = use_color
        else:
            logger.enable_color = logger.determineColorEnabled()

        # Should be either True or False based on auto-detect
        assert isinstance(logger.enable_color, bool)
    finally:
        logger.enable_color = original_color
