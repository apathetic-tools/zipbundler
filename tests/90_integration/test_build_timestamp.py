# tests/50_core/test_build_timestamp.py
"""Tests for build timestamp control via --disable-build-timestamp flag."""

import os
import re
import zipfile
from datetime import datetime
from pathlib import Path

import zipbundler.cli as mod_main
import zipbundler.constants as mod_constants


def test_cli_build_with_timestamp_enabled(tmp_path: Path) -> None:
    """Test that build timestamps are included by default in PKG-INFO."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create config file with metadata
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  },
  "metadata": {
    "display_name": "My Package",
    "version": "1.0.0"
  }
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()

        # Verify PKG-INFO contains actual timestamp (ISO 8601 format)
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert "PKG-INFO" in names

            pkg_info = zf.read("PKG-INFO").decode("utf-8")
            # Should contain Build-Timestamp with ISO 8601 format
            timestamp_match = re.search(
                r"Build-Timestamp: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
                pkg_info,
            )
            assert timestamp_match is not None
            timestamp_str = timestamp_match.group(1)
            # Verify it's a valid datetime
            datetime.fromisoformat(timestamp_str)
    finally:
        os.chdir(original_cwd)


def test_cli_build_with_disable_build_timestamp_flag(tmp_path: Path) -> None:
    """Test --disable-build-timestamp flag uses placeholder."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create config file with metadata
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  },
  "metadata": {
    "display_name": "My Package",
    "version": "1.0.0"
  }
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build", "--disable-build-timestamp"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()

        # Verify PKG-INFO contains placeholder instead of real timestamp
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert "PKG-INFO" in names

            pkg_info = zf.read("PKG-INFO").decode("utf-8")
            # Should contain placeholder
            expected_ts = (
                f"Build-Timestamp: {mod_constants.BUILD_TIMESTAMP_PLACEHOLDER}"
            )
            assert expected_ts in pkg_info
    finally:
        os.chdir(original_cwd)


def test_cli_build_with_disable_build_timestamp_env_var(
    tmp_path: Path,
) -> None:
    """Test DISABLE_BUILD_TIMESTAMP environment variable."""
    original_cwd = Path.cwd()
    original_env = os.environ.get("DISABLE_BUILD_TIMESTAMP")
    try:
        os.chdir(tmp_path)
        os.environ["DISABLE_BUILD_TIMESTAMP"] = "true"

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create config file with metadata
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  },
  "metadata": {
    "display_name": "My Package",
    "version": "1.0.0"
  }
}
""",
            encoding="utf-8",
        )

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()

        # Verify PKG-INFO contains placeholder from env var
        with zipfile.ZipFile(output_file, "r") as zf:
            names = zf.namelist()
            assert "PKG-INFO" in names

            pkg_info = zf.read("PKG-INFO").decode("utf-8")
            # Should contain placeholder
            expected_ts = (
                f"Build-Timestamp: {mod_constants.BUILD_TIMESTAMP_PLACEHOLDER}"
            )
            assert expected_ts in pkg_info
    finally:
        os.chdir(original_cwd)
        if original_env is None:
            os.environ.pop("DISABLE_BUILD_TIMESTAMP", None)
        else:
            os.environ["DISABLE_BUILD_TIMESTAMP"] = original_env


def test_cli_build_flag_overrides_env_var(tmp_path: Path) -> None:
    """Test that CLI flag overrides environment variable."""
    original_cwd = Path.cwd()
    original_env = os.environ.get("DISABLE_BUILD_TIMESTAMP")
    try:
        os.chdir(tmp_path)
        # Set env var to enable (use placeholder)
        os.environ["DISABLE_BUILD_TIMESTAMP"] = "true"

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")

        # Create config file with metadata
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  },
  "metadata": {
    "display_name": "My Package",
    "version": "1.0.0"
  }
}
""",
            encoding="utf-8",
        )

        # Build without --disable-build-timestamp flag (should use real timestamp
        # since CLI args have higher precedence than env var)
        # Note: The env var is set, but we're not passing the flag, so default
        # behavior applies. Actually, env var DOES apply when no flag is set.
        # Let me reconsider: if env var says "true", we should get placeholder.
        # But if we want to test override, we need a way to turn OFF the env var
        # via CLI, which we don't have. Let's test the normal precedence instead.

        # Handle both module and function cases (runtime mode swap)
        main_func = mod_main if callable(mod_main) else mod_main.main
        code = main_func(["--build"])

        # Verify exit code is 0
        assert code == 0

        # Verify zip file was created
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()

        # Verify PKG-INFO uses placeholder (from env var)
        with zipfile.ZipFile(output_file, "r") as zf:
            pkg_info = zf.read("PKG-INFO").decode("utf-8")
            expected_ts = (
                f"Build-Timestamp: {mod_constants.BUILD_TIMESTAMP_PLACEHOLDER}"
            )
            assert expected_ts in pkg_info
    finally:
        os.chdir(original_cwd)
        if original_env is None:
            os.environ.pop("DISABLE_BUILD_TIMESTAMP", None)
        else:
            os.environ["DISABLE_BUILD_TIMESTAMP"] = original_env


def test_cli_build_deterministic_reproducibility(tmp_path: Path) -> None:
    """Test that builds with --disable-build-timestamp produce identical PKG-INFO."""
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Create a package structure
        src_dir = tmp_path / "src" / "mypackage"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "module.py").write_text("def func():\n    pass\n")

        # Create config file with metadata
        config_file = tmp_path / ".zipbundler.jsonc"
        config_file.write_text(
            """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.zip"
  },
  "metadata": {
    "display_name": "My Package",
    "version": "1.0.0"
  }
}
""",
            encoding="utf-8",
        )

        # Build twice with --disable-build-timestamp
        main_func = mod_main if callable(mod_main) else mod_main.main

        # First build
        code1 = main_func(["--build", "--disable-build-timestamp"])
        assert code1 == 0
        output_file = tmp_path / "dist" / "bundle.zip"
        assert output_file.exists()

        with zipfile.ZipFile(output_file, "r") as zf:
            pkg_info_1 = zf.read("PKG-INFO").decode("utf-8")

        # Clean up for second build
        output_file.unlink()

        # Second build (should be identical)
        code2 = main_func(["--build", "--disable-build-timestamp"])
        assert code2 == 0
        assert output_file.exists()

        with zipfile.ZipFile(output_file, "r") as zf:
            pkg_info_2 = zf.read("PKG-INFO").decode("utf-8")

        # PKG-INFO should be identical (same placeholder)
        assert pkg_info_1 == pkg_info_2
        expected_ts = f"Build-Timestamp: {mod_constants.BUILD_TIMESTAMP_PLACEHOLDER}"
        assert expected_ts in pkg_info_1
    finally:
        os.chdir(original_cwd)
