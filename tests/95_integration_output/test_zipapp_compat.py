"""Integration tests for zipapp CLI compatibility.

Tests that zipbundler maintains compatibility with Python's stdlib zipapp
command-line interface for the main use cases.
"""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def simple_package(tmp_path: Path) -> Path:
    """Create a simple Python package for testing."""
    pkg_dir = tmp_path / "myapp"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text('__version__ = "1.0.0"')
    (pkg_dir / "__main__.py").write_text('print("Hello from myapp")')
    return pkg_dir


@pytest.fixture
def zipbundler_cli() -> list[str]:
    """Return the zipbundler CLI command."""
    return [sys.executable, "-m", "zipbundler"]


class TestZipappCliCompat:
    """Test zipapp CLI compatibility."""

    def test_basic_build_with_output(
        self, simple_package: Path, tmp_path: Path, zipbundler_cli: list[str]
    ) -> None:
        """Test basic build: SOURCE -o OUTPUT."""
        output = tmp_path / "myapp.pyz"
        cmd = [
            *zipbundler_cli,
            str(simple_package),
            "-o",
            str(output),
            "--compat",
        ]
        result = subprocess.run(  # noqa: S603
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output.exists(), "Output file was not created"
        assert output.suffix == ".pyz"

    def test_build_with_shebang(
        self, simple_package: Path, tmp_path: Path, zipbundler_cli: list[str]
    ) -> None:
        """Test build with shebang."""
        output = tmp_path / "myapp.pyz"
        cmd = [
            *zipbundler_cli,
            str(simple_package),
            "-o",
            str(output),
            "-p",
            "/usr/bin/env python3",
            "--compat",
        ]
        result = subprocess.run(  # noqa: S603
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output.exists()

        # Verify shebang is in the file
        with output.open("rb") as f:
            first_line = f.readline()
            assert b"#!" in first_line

    def test_build_with_python_flag(
        self, simple_package: Path, tmp_path: Path, zipbundler_cli: list[str]
    ) -> None:
        """Test build with --python flag."""
        output = tmp_path / "myapp.pyz"
        cmd = [
            *zipbundler_cli,
            str(simple_package),
            "-o",
            str(output),
            "--python",
            "/usr/bin/env python3",
            "--compat",
        ]
        result = subprocess.run(  # noqa: S603
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output.exists()

    def test_build_with_main(
        self, simple_package: Path, tmp_path: Path, zipbundler_cli: list[str]
    ) -> None:
        """Test build with main entry point."""
        output = tmp_path / "myapp.pyz"
        cmd = [
            *zipbundler_cli,
            str(simple_package),
            "-o",
            str(output),
            "-m",
            "myapp:main",
            "--compat",
        ]
        result = subprocess.run(  # noqa: S603
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output.exists()

    def test_build_with_compress(
        self, simple_package: Path, tmp_path: Path, zipbundler_cli: list[str]
    ) -> None:
        """Test build with compression."""
        output = tmp_path / "myapp.pyz"
        cmd = [
            *zipbundler_cli,
            str(simple_package),
            "-o",
            str(output),
            "-c",
            "--compat",
        ]
        result = subprocess.run(  # noqa: S603
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output.exists()

    def test_build_all_zipapp_flags(
        self, simple_package: Path, tmp_path: Path, zipbundler_cli: list[str]
    ) -> None:
        """Test build with all main zipapp flags."""
        output = tmp_path / "myapp.pyz"
        cmd = [
            *zipbundler_cli,
            str(simple_package),
            "-o",
            str(output),
            "-p",
            "/usr/bin/env python3",
            "-m",
            "myapp:main",
            "-c",
            "--compat",
        ]
        result = subprocess.run(  # noqa: S603
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output.exists()

    def test_info_with_archive_file(
        self, simple_package: Path, tmp_path: Path, zipbundler_cli: list[str]
    ) -> None:
        """Test --info with archive file."""
        # First build an archive
        output = tmp_path / "myapp.pyz"
        build_cmd = [
            *zipbundler_cli,
            str(simple_package),
            "-o",
            str(output),
            "-p",
            "/usr/bin/env python3",
            "--compat",
        ]
        build_result = subprocess.run(  # noqa: S603
            build_cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        assert build_result.returncode == 0, f"Build failed: {build_result.stderr}"

        # Now test --info on the archive
        info_cmd = [
            *zipbundler_cli,
            "--info",
            str(output),
            "--compat",
        ]
        info_result = subprocess.run(  # noqa: S603
            info_cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        assert info_result.returncode == 0, f"Info failed: {info_result.stderr}"
        assert "Interpreter:" in info_result.stdout

    def test_info_with_directory(
        self, simple_package: Path, zipbundler_cli: list[str]
    ) -> None:
        """Test --info with directory (auto-derives)."""
        # First build an archive in the source directory
        output = simple_package / f"{simple_package.name}.pyz"
        build_cmd = [
            *zipbundler_cli,
            str(simple_package),
            "-o",
            str(output),
            "-p",
            "/usr/bin/env python3",
            "--compat",
        ]
        build_result = subprocess.run(  # noqa: S603
            build_cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        assert build_result.returncode == 0, f"Build failed: {build_result.stderr}"

        # Now test --info with just the directory (should auto-derive)
        info_cmd = [
            *zipbundler_cli,
            "--info",
            str(simple_package),
            "--compat",
        ]
        info_result = subprocess.run(  # noqa: S603
            info_cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        assert info_result.returncode == 0, f"Info failed: {info_result.stderr}"
        assert "Interpreter:" in info_result.stdout

    def test_output_default_extension(
        self, simple_package: Path, tmp_path: Path, zipbundler_cli: list[str]
    ) -> None:
        """Test output extension handling."""
        # Test with a name that doesn't have .pyz extension
        output = tmp_path / "myapp"
        cmd = [
            *zipbundler_cli,
            str(simple_package),
            "-o",
            str(output),
            "--compat",
        ]
        result = subprocess.run(  # noqa: S603
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # The output should be created as-is (zipbundler doesn't auto-add .pyz)
        assert output.exists()

    def test_positional_source_argument(
        self, simple_package: Path, tmp_path: Path, zipbundler_cli: list[str]
    ) -> None:
        """Test positional SOURCE argument."""
        output = tmp_path / "myapp.pyz"
        cmd = [
            *zipbundler_cli,
            str(simple_package),
            "-o",
            str(output),
            "--compat",
        ]
        result = subprocess.run(  # noqa: S603
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output.exists()

    def test_long_form_flags(
        self, simple_package: Path, tmp_path: Path, zipbundler_cli: list[str]
    ) -> None:
        """Test long-form flags."""
        output = tmp_path / "myapp.pyz"
        cmd = [
            *zipbundler_cli,
            str(simple_package),
            "--output",
            str(output),
            "--python",
            "/usr/bin/env python3",
            "--main",
            "myapp:main",
            "--compress",
            "--compat",
        ]
        result = subprocess.run(  # noqa: S603
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output.exists()

    def test_missing_output_error(
        self, simple_package: Path, zipbundler_cli: list[str]
    ) -> None:
        """Test that missing --output is an error."""
        cmd = [
            *zipbundler_cli,
            str(simple_package),
            "--compat",
        ]
        result = subprocess.run(  # noqa: S603
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        # Should error because output is required for zipapp-style
        assert result.returncode != 0

    def test_no_compress_flag(
        self, simple_package: Path, tmp_path: Path, zipbundler_cli: list[str]
    ) -> None:
        """Test --no-compress flag."""
        output = tmp_path / "myapp.pyz"
        cmd = [
            *zipbundler_cli,
            str(simple_package),
            "-o",
            str(output),
            "--no-compress",
            "--compat",
        ]
        result = subprocess.run(  # noqa: S603
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output.exists()

    def test_no_shebang_flag(
        self, simple_package: Path, tmp_path: Path, zipbundler_cli: list[str]
    ) -> None:
        """Test --no-shebang flag."""
        output = tmp_path / "myapp.pyz"
        cmd = [
            *zipbundler_cli,
            str(simple_package),
            "-o",
            str(output),
            "--no-shebang",
            "--compat",
        ]
        result = subprocess.run(  # noqa: S603
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output.exists()

    def test_no_main_flag(
        self, simple_package: Path, tmp_path: Path, zipbundler_cli: list[str]
    ) -> None:
        """Test --no-main flag."""
        output = tmp_path / "myapp.pyz"
        cmd = [
            *zipbundler_cli,
            str(simple_package),
            "-o",
            str(output),
            "--no-main",
            "--compat",
        ]
        result = subprocess.run(  # noqa: S603
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert output.exists()
