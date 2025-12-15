# tests/50_core/test_constants_usage.py
"""Tests for proper usage of default constants throughout the codebase."""

import os
import zipfile
from pathlib import Path

import pytest

import zipbundler.cli as mod_cli
import zipbundler.commands.build as mod_build
import zipbundler.commands.validate as mod_validate
import zipbundler.constants as mod_constants


class TestDefaultOutDir:
    """Test DEFAULT_OUT_DIR constant usage."""

    def test_resolve_output_path_uses_default_out_dir_when_none_provided(
        self,
    ) -> None:
        """Test that resolve_output_path_from_config uses DEFAULT_OUT_DIR."""
        # When no output config is provided, should use DEFAULT_OUT_DIR
        result = mod_validate.resolve_output_path_from_config(None)
        assert str(result).startswith(mod_constants.DEFAULT_OUT_DIR)
        assert result == Path(f"{mod_constants.DEFAULT_OUT_DIR}/bundle.pyz")

    def test_resolve_output_path_uses_default_when_explicit_none(self) -> None:
        """Test that passing None as default_directory uses DEFAULT_OUT_DIR."""
        result = mod_validate.resolve_output_path_from_config(
            output_config=None, default_directory=None
        )
        assert str(result).startswith(mod_constants.DEFAULT_OUT_DIR)

    def test_resolve_output_path_respects_config_directory(self) -> None:
        """Test that config directory overrides DEFAULT_OUT_DIR."""
        config = {"directory": "custom_output"}
        result = mod_validate.resolve_output_path_from_config(
            config, default_directory=None
        )
        assert str(result).startswith("custom_output")
        assert result == Path("custom_output/bundle.pyz")

    def test_resolve_output_path_respects_config_path(self) -> None:
        """Test that config path takes precedence over DEFAULT_OUT_DIR."""
        config = {"path": "my_bundle.pyz"}
        result = mod_validate.resolve_output_path_from_config(
            config, default_directory=None
        )
        assert result == Path("my_bundle.pyz")

    def test_cli_build_uses_default_out_dir_fallback(self, tmp_path: Path) -> None:
        """Test that CLI build uses DEFAULT_OUT_DIR when no --output specified."""
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)

            # Create minimal package
            src_dir = tmp_path / "src" / "mypackage"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("")

            # Create config without output path
            config_file = tmp_path / ".zipbundler.jsonc"
            config_file.write_text(
                """{
  "packages": ["src/mypackage/**/*.py"]
}
""",
                encoding="utf-8",
            )

            # Build should create file in DEFAULT_OUT_DIR
            main_func = mod_cli if callable(mod_cli) else mod_cli.main
            code = main_func(["--build"])

            assert code == 0
            # Should be created in DEFAULT_OUT_DIR
            expected_path = tmp_path / mod_constants.DEFAULT_OUT_DIR / "bundle.pyz"
            assert expected_path.exists()
        finally:
            os.chdir(original_cwd)


class TestDefaultDryRun:
    """Test DEFAULT_DRY_RUN constant usage."""

    def test_default_dry_run_value_is_false(self) -> None:
        """Test that DEFAULT_DRY_RUN is False by default."""
        assert mod_constants.DEFAULT_DRY_RUN is False

    def test_cli_dry_run_flag_has_correct_default(self) -> None:
        """Test that --dry-run flag uses DEFAULT_DRY_RUN as default."""
        parser = mod_cli._setup_parser()  # noqa: SLF001
        args = parser.parse_args(["--build"])
        # dry_run should match DEFAULT_DRY_RUN when not explicitly set
        assert args.dry_run == mod_constants.DEFAULT_DRY_RUN

    def test_cli_dry_run_flag_can_be_enabled(self) -> None:
        """Test that --dry-run flag can be explicitly enabled."""
        parser = mod_cli._setup_parser()  # noqa: SLF001
        args = parser.parse_args(["--build", "--dry-run"])
        assert args.dry_run is True

    def test_dry_run_build_does_not_create_output(self, tmp_path: Path) -> None:
        """Test that dry-run mode doesn't create output file."""
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)

            # Create minimal package
            src_dir = tmp_path / "src" / "mypackage"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("")

            # Create config
            config_file = tmp_path / ".zipbundler.jsonc"
            config_file.write_text(
                """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.pyz"
  }
}
""",
                encoding="utf-8",
            )

            # Run with --dry-run
            main_func = mod_cli if callable(mod_cli) else mod_cli.main
            code = main_func(["--build", "--dry-run"])

            assert code == 0
            # File should NOT be created in dry-run mode
            output_file = tmp_path / "dist" / "bundle.pyz"
            assert not output_file.exists()
        finally:
            os.chdir(original_cwd)


class TestDefaultUseProjectMetadata:
    """Test DEFAULT_USE_PYPROJECT_METADATA constant usage."""

    def test_default_use_pyproject_metadata_value_is_true(self) -> None:
        """Test that DEFAULT_USE_PYPROJECT_METADATA is True by default."""
        assert mod_constants.DEFAULT_USE_PYPROJECT_METADATA is True

    def test_build_extracts_pyproject_metadata_by_default(self, tmp_path: Path) -> None:
        """Test that build extracts metadata from pyproject.toml by default."""
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)

            # Create minimal package
            src_dir = tmp_path / "src" / "mypackage"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("")

            # Create pyproject.toml with metadata
            pyproject_file = tmp_path / "pyproject.toml"
            pyproject_file.write_text(
                """[project]
name = "test-package"
version = "1.2.3"
description = "Test package"
authors = [{name = "Test Author"}]
license = {text = "MIT"}
""",
                encoding="utf-8",
            )

            # Create config without explicit metadata
            config_file = tmp_path / ".zipbundler.jsonc"
            config_file.write_text(
                """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.pyz"
  }
}
""",
                encoding="utf-8",
            )

            # Build should extract metadata from pyproject.toml
            main_func = mod_cli if callable(mod_cli) else mod_cli.main
            code = main_func(["--build"])

            assert code == 0

            # Verify PKG-INFO was created with pyproject metadata
            output_file = tmp_path / "dist" / "bundle.pyz"
            assert output_file.exists()

            with zipfile.ZipFile(output_file, "r") as zf:
                names = zf.namelist()
                assert "PKG-INFO" in names

                pkg_info = zf.read("PKG-INFO").decode("utf-8")
                # Should have extracted metadata from pyproject.toml
                assert "Name: test-package" in pkg_info
                assert "Version: 1.2.3" in pkg_info
        finally:
            os.chdir(original_cwd)

    def test_build_respects_config_metadata_over_pyproject(
        self, tmp_path: Path
    ) -> None:
        """Test that explicit config metadata takes precedence."""
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)

            # Create minimal package
            src_dir = tmp_path / "src" / "mypackage"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("")

            # Create pyproject.toml
            pyproject_file = tmp_path / "pyproject.toml"
            pyproject_file.write_text(
                """[project]
name = "pyproject-package"
version = "1.0.0"
""",
                encoding="utf-8",
            )

            # Create config with explicit metadata (should take precedence)
            config_file = tmp_path / ".zipbundler.jsonc"
            config_file.write_text(
                """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.pyz"
  },
  "metadata": {
    "display_name": "config-package",
    "version": "2.0.0"
  }
}
""",
                encoding="utf-8",
            )

            main_func = mod_cli if callable(mod_cli) else mod_cli.main
            code = main_func(["--build"])

            assert code == 0

            output_file = tmp_path / "dist" / "bundle.pyz"
            assert output_file.exists()

            with zipfile.ZipFile(output_file, "r") as zf:
                pkg_info = zf.read("PKG-INFO").decode("utf-8")
                # Should use config metadata, not pyproject
                assert "Name: config-package" in pkg_info
                assert "Version: 2.0.0" in pkg_info
                assert "pyproject-package" not in pkg_info
        finally:
            os.chdir(original_cwd)

    def test_init_command_extracts_pyproject_metadata_by_default(
        self, tmp_path: Path
    ) -> None:
        """Test that init command extracts metadata from pyproject.toml."""
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)

            # Create pyproject.toml with metadata
            pyproject_file = tmp_path / "pyproject.toml"
            pyproject_file.write_text(
                """[project]
name = "my-package"
version = "1.0.0"
description = "My package"
authors = [{name = "Test Author"}]
""",
                encoding="utf-8",
            )

            # Run init command
            main_func = mod_cli if callable(mod_cli) else mod_cli.main
            code = main_func(["--init"])

            assert code == 0

            # Verify config file was created
            config_file = tmp_path / ".zipbundler.jsonc"
            assert config_file.exists()

            content = config_file.read_text()
            # Should have auto-detected metadata from pyproject.toml
            assert '"metadata"' in content
            assert "my-package" in content or "display_name" in content
        finally:
            os.chdir(original_cwd)

    def test_build_skips_pyproject_when_disabled(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that metadata extraction is skipped when disabled."""
        # Patch the constant to False
        monkeypatch.setattr(mod_build, "DEFAULT_USE_PYPROJECT_METADATA", False)

        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)

            # Create minimal package
            src_dir = tmp_path / "src" / "mypackage"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("")

            # Create pyproject.toml (should be ignored)
            pyproject_file = tmp_path / "pyproject.toml"
            pyproject_file.write_text(
                """[project]
name = "test-package"
version = "1.2.3"
""",
                encoding="utf-8",
            )

            # Create config without explicit metadata
            config_file = tmp_path / ".zipbundler.jsonc"
            config_file.write_text(
                """{
  "packages": ["src/mypackage/**/*.py"],
  "output": {
    "path": "dist/bundle.pyz"
  }
}
""",
                encoding="utf-8",
            )

            main_func = mod_cli if callable(mod_cli) else mod_cli.main
            code = main_func(["--build"])

            assert code == 0

            output_file = tmp_path / "dist" / "bundle.pyz"
            assert output_file.exists()

            with zipfile.ZipFile(output_file, "r") as zf:
                names = zf.namelist()
                # PKG-INFO should not be created without metadata
                # or should have minimal info
                if "PKG-INFO" in names:
                    pkg_info = zf.read("PKG-INFO").decode("utf-8")
                    # Should not have extracted pyproject metadata
                    assert "test-package" not in pkg_info
        finally:
            os.chdir(original_cwd)
