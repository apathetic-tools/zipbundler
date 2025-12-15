# tests/50_core/test_cli_color.py
"""Tests for --color and --no-color CLI flags."""

import pytest

import zipbundler.cli as mod_cli


def test_color_flags_defined_and_mutually_exclusive() -> None:
    """Test that --color and --no-color flags are defined and mutually exclusive."""
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

    # Test that both flags together fail (mutually exclusive)
    with pytest.raises(SystemExit):
        parser.parse_args(["--color", "--no-color"])
