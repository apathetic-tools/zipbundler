# tests/50_core/test_priv__config_validation.py
# we import `_` private for testing purposes only
# ruff: noqa: SLF001
# pyright: reportPrivateUsage=false
"""Tests for private config validation functions.

This module tests private config validation functions and intentionally accesses
private members that are not part of the public API. These tests validate
the internal validation logic for configuration options.
"""

import zipbundler.config.config_validate as mod_config_validate


class TestValidateMainMode:
    """Test _validate_main_mode private function."""

    def test_main_mode_validation(self) -> None:
        """Test that main_mode validation works correctly."""
        # Valid: "auto"
        is_valid, msg = mod_config_validate._validate_main_mode("auto")
        assert is_valid
        assert msg == ""

        # Invalid: other values
        is_valid, msg = mod_config_validate._validate_main_mode("invalid")
        assert not is_valid
        assert "auto" in msg.lower()


class TestValidateMainName:
    """Test _validate_main_name private function."""

    def test_main_name_validation_accepts_valid_identifier(self) -> None:
        """Test that main_name validation accepts valid Python identifiers."""
        # Valid identifiers
        for name in ["main", "run", "cli", "start", "_main"]:
            is_valid, msg = mod_config_validate._validate_main_name(name)
            assert is_valid, f"'{name}' should be valid: {msg}"
            assert msg == ""

    def test_main_name_validation_accepts_none(self) -> None:
        """Test that main_name validation accepts None for auto-detect."""
        # None should be valid (means auto-detect)
        is_valid, msg = mod_config_validate._validate_main_name(None)
        assert is_valid
        assert msg == ""

    def test_main_name_validation_rejects_invalid_identifiers(self) -> None:
        """Test that main_name validation rejects invalid Python identifiers."""
        # Invalid identifiers
        for name in ["invalid-name", "123start", "with space", "main()"]:
            is_valid, msg = mod_config_validate._validate_main_name(name)
            assert not is_valid, f"'{name}' should be invalid"
            assert "identifier" in msg.lower()
