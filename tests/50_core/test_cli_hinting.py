# tests/50_core/test_cli_hinting.py
"""Tests for CLI argument hinting functionality."""

import argparse

import zipbundler.cli as mod_cli


def test_hinting_parser_exists() -> None:
    """Test that HintingArgumentParser class exists and is used in CLI."""
    # Verify the class exists
    assert hasattr(mod_cli, "HintingArgumentParser")
    assert issubclass(mod_cli.HintingArgumentParser, argparse.ArgumentParser)

    # Verify it can be instantiated
    parser = mod_cli.HintingArgumentParser()
    assert isinstance(parser, mod_cli.HintingArgumentParser)


def test_hinting_parser_error_method() -> None:
    """Test that HintingArgumentParser has the error method that provides hints."""
    parser = mod_cli.HintingArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--output", "-o")

    # Verify the error method exists and is callable
    assert hasattr(parser, "error")
    assert callable(parser.error)

    # The error method should be the overridden version from HintingArgumentParser
    # Verify by checking the method's qualname
    assert "HintingArgumentParser" in parser.error.__qualname__
