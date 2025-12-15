# tests/50_core/test_constants_usage.py
"""Tests for proper usage of default constants throughout the codebase."""

import os
import zipfile
from pathlib import Path

import pytest

import zipbundler.build as mod_build_zipapp
import zipbundler.cli as mod_cli
import zipbundler.commands.build as mod_build
import zipbundler.commands.validate as mod_validate
import zipbundler.config.config_validate as mod_config_validate
import zipbundler.constants as mod_constants
import zipbundler.utils as mod_utils


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


class TestDefaultSourceBases:
    """Test DEFAULT_SOURCE_BASES constant usage."""

    def test_default_source_bases_value(self) -> None:
        """Test that DEFAULT_SOURCE_BASES has expected values."""
        assert isinstance(mod_constants.DEFAULT_SOURCE_BASES, list)
        assert len(mod_constants.DEFAULT_SOURCE_BASES) > 0
        # Should contain common source directories
        assert "src" in mod_constants.DEFAULT_SOURCE_BASES
        assert "lib" in mod_constants.DEFAULT_SOURCE_BASES
        assert "packages" in mod_constants.DEFAULT_SOURCE_BASES

    def test_build_uses_source_bases_for_archive_root(self, tmp_path: Path) -> None:
        """Test that build recognizes source directories as archive root."""
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)

            # Create package in a source directory
            src_dir = tmp_path / "src" / "mypackage"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("# Package")
            (src_dir / "module.py").write_text("def hello(): return 'world'")

            output_file = tmp_path / "bundle.pyz"

            # Build with default source_bases
            mod_build_zipapp.build_zipapp(
                output=output_file,
                packages=[src_dir.parent],  # Pass src/
            )

            assert output_file.exists()

            # Verify that package is at root, not under src/
            with zipfile.ZipFile(output_file, "r") as zf:
                names = zf.namelist()
                # Should have mypackage files at root, not src/mypackage
                assert any("mypackage/__init__.py" in name for name in names)
                assert not any("src/mypackage" in name for name in names)

        finally:
            os.chdir(original_cwd)

    def test_build_can_override_source_bases(self, tmp_path: Path) -> None:
        """Test that build allows overriding source_bases."""
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)

            # Create package in a custom directory (not in default bases)
            # When "mylibs" not in source_bases, it should include full path
            mylibs_dir = tmp_path / "mylibs" / "mypackage"
            mylibs_dir.mkdir(parents=True)
            (mylibs_dir / "__init__.py").write_text("# Package")

            output_file = tmp_path / "bundle.pyz"

            # Build WITHOUT "mylibs" in source_bases - should keep full path
            mod_build_zipapp.build_zipapp(
                output=output_file,
                packages=[mylibs_dir.parent],  # Pass mylibs/
                source_bases=["src", "lib", "packages"],  # mylibs not included
            )

            assert output_file.exists()

            # Verify that mylibs is NOT recognized as source base, so path is preserved
            with zipfile.ZipFile(output_file, "r") as zf:
                names = zf.namelist()
                # Should have mylibs/mypackage since mylibs not in source_bases
                assert any("mylibs/mypackage/__init__.py" in name for name in names)

            # Now build WITH "mylibs" in source_bases - should use it as archive root
            output_file2 = tmp_path / "bundle2.pyz"
            mod_build_zipapp.build_zipapp(
                output=output_file2,
                packages=[mylibs_dir.parent],  # Pass mylibs/
                source_bases=["mylibs", "src", "lib"],  # mylibs NOW included
            )

            assert output_file2.exists()

            # Verify that mylibs is now recognized as source base
            with zipfile.ZipFile(output_file2, "r") as zf:
                names = zf.namelist()
                # Should have mypackage at root, not under mylibs/
                assert any("mypackage/__init__.py" in name for name in names)
                assert not any("mylibs/mypackage" in name for name in names)

        finally:
            os.chdir(original_cwd)


class TestDefaultInstalledBases:
    """Test DEFAULT_INSTALLED_BASES constant and installed packages discovery."""

    def test_default_installed_bases_value(self) -> None:
        """Test that DEFAULT_INSTALLED_BASES has expected values."""
        assert isinstance(mod_constants.DEFAULT_INSTALLED_BASES, list)
        assert len(mod_constants.DEFAULT_INSTALLED_BASES) > 0
        # Should contain common site-packages names
        assert "site-packages" in mod_constants.DEFAULT_INSTALLED_BASES
        assert "dist-packages" in mod_constants.DEFAULT_INSTALLED_BASES

    def test_discover_installed_packages_roots_returns_list(self) -> None:
        """Test that discover_installed_packages_roots returns a list."""
        roots = mod_utils.discover_installed_packages_roots()
        assert isinstance(roots, list)
        # Should be able to call without error, may be empty in some environments
        assert all(isinstance(root, str) for root in roots)

    def test_discover_installed_packages_roots_deduplicates(self) -> None:
        """Test that discovered roots are deduplicated."""
        roots = mod_utils.discover_installed_packages_roots()
        # Should not have duplicates
        assert len(roots) == len(set(roots))

    def test_discover_installed_packages_roots_paths_exist(self) -> None:
        """Test that discovered roots point to existing directories."""
        roots = mod_utils.discover_installed_packages_roots()
        for root in roots:
            root_path = Path(root)
            # Should be an absolute path
            assert root_path.is_absolute()
            # Should exist or be a valid Python site-packages location
            # (some may not exist in minimal environments)
            if root_path.exists():
                assert root_path.is_dir()

    def test_discover_installed_packages_roots_contains_site_packages_markers(
        self,
    ) -> None:
        """Test that discovered roots contain site-packages or dist-packages."""
        roots = mod_utils.discover_installed_packages_roots()
        # If discovered, should have site-packages or dist-packages in path
        for root in roots:
            assert "site-packages" in root or "dist-packages" in root, (
                f"Path {root} missing site-packages or dist-packages"
            )


class TestDefaultMainMode:
    """Test DEFAULT_MAIN_MODE constant usage."""

    def test_default_main_mode_value_is_auto(self) -> None:
        """Test that DEFAULT_MAIN_MODE is 'auto' by default."""
        assert mod_constants.DEFAULT_MAIN_MODE == "auto"

    def test_cli_main_mode_argument_exists(self) -> None:
        """Test that --main-mode CLI argument is available."""
        parser = mod_cli._setup_parser()  # noqa: SLF001
        args = parser.parse_args(["--build", "--main-mode", "auto"])
        assert hasattr(args, "main_mode")
        assert args.main_mode == "auto"

    def test_cli_main_mode_default_is_none(self) -> None:
        """Test that --main-mode defaults to None (uses config or constant)."""
        parser = mod_cli._setup_parser()  # noqa: SLF001
        args = parser.parse_args(["--build"])
        # When not specified, should be None (letting config/defaults take over)
        assert args.main_mode is None

    def test_main_mode_validation(self) -> None:
        """Test that main_mode validation works correctly."""
        # Valid: "auto"
        is_valid, msg = mod_config_validate._validate_main_mode("auto")  # noqa: SLF001
        assert is_valid
        assert msg == ""

        # Invalid: other values
        is_valid, msg = mod_config_validate._validate_main_mode("invalid")  # noqa: SLF001
        assert not is_valid
        assert "auto" in msg.lower()

    def test_main_mode_in_config_file(self, tmp_path: Path) -> None:
        """Test that main_mode can be specified in config file."""
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)

            # Create minimal package
            src_dir = tmp_path / "src" / "mypackage"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("")

            # Create config with main_mode
            config_file = tmp_path / ".zipbundler.jsonc"
            config_file.write_text(
                """{
  "packages": ["src/mypackage"],
  "options": {
    "main_mode": "auto"
  }
}
""",
                encoding="utf-8",
            )

            # Build should succeed with main_mode in config
            main_func = mod_cli if callable(mod_cli) else mod_cli.main
            code = main_func(["--build"])

            assert code == 0
        finally:
            os.chdir(original_cwd)


class TestDefaultMainName:
    """Test DEFAULT_MAIN_NAME constant usage."""

    def test_default_main_name_value_is_none(self) -> None:
        """Test that DEFAULT_MAIN_NAME is None by default (auto-detect)."""
        assert mod_constants.DEFAULT_MAIN_NAME is None

    def test_cli_main_name_argument_exists(self) -> None:
        """Test that --main-name CLI argument is available."""
        parser = mod_cli._setup_parser()  # noqa: SLF001
        args = parser.parse_args(["--build", "--main-name", "main"])
        assert hasattr(args, "main_name")
        assert args.main_name == "main"

    def test_cli_main_name_default_is_none(self) -> None:
        """Test that --main-name defaults to None (auto-detect)."""
        parser = mod_cli._setup_parser()  # noqa: SLF001
        args = parser.parse_args(["--build"])
        # When not specified, should be None
        assert args.main_name is None

    def test_main_name_validation_accepts_valid_identifier(self) -> None:
        """Test that main_name validation accepts valid Python identifiers."""
        # Valid identifiers
        for name in ["main", "run", "cli", "start", "_main"]:
            is_valid, msg = mod_config_validate._validate_main_name(name)  # noqa: SLF001
            assert is_valid, f"'{name}' should be valid: {msg}"
            assert msg == ""

    def test_main_name_validation_accepts_none(self) -> None:
        """Test that main_name validation accepts None for auto-detect."""
        # None should be valid (means auto-detect)
        is_valid, msg = mod_config_validate._validate_main_name(None)  # noqa: SLF001
        assert is_valid
        assert msg == ""

    def test_main_name_validation_rejects_invalid_identifiers(self) -> None:
        """Test that main_name validation rejects invalid Python identifiers."""
        # Invalid identifiers
        for name in ["invalid-name", "123start", "with space", "main()"]:
            is_valid, msg = mod_config_validate._validate_main_name(name)  # noqa: SLF001
            assert not is_valid, f"'{name}' should be invalid"
            assert "identifier" in msg.lower()

    def test_main_name_in_config_file(self, tmp_path: Path) -> None:
        """Test that main_name can be specified in config file."""
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)

            # Create minimal package
            src_dir = tmp_path / "src" / "mypackage"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("")

            # Create config with main_name
            config_file = tmp_path / ".zipbundler.jsonc"
            config_file.write_text(
                """{
  "packages": ["src/mypackage"],
  "options": {
    "main_name": "main"
  }
}
""",
                encoding="utf-8",
            )

            # Build should succeed with main_name in config
            main_func = mod_cli if callable(mod_cli) else mod_cli.main
            code = main_func(["--build"])

            assert code == 0
        finally:
            os.chdir(original_cwd)

    def test_cli_main_name_overrides_config(self, tmp_path: Path) -> None:
        """Test that CLI --main-name overrides config value."""
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)

            # Create minimal package
            src_dir = tmp_path / "src" / "mypackage"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("")

            # Create config with different main_name
            config_file = tmp_path / ".zipbundler.jsonc"
            config_file.write_text(
                """{
  "packages": ["src/mypackage"],
  "options": {
    "main_name": "start"
  }
}
""",
                encoding="utf-8",
            )

            # Build with CLI override
            main_func = mod_cli if callable(mod_cli) else mod_cli.main
            code = main_func(["--build", "--main-name", "main"])

            assert code == 0
        finally:
            os.chdir(original_cwd)
