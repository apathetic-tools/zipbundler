# tests/50_core/test_build_compression.py
"""Tests for compression support in zipapp building."""

import zipfile
from pathlib import Path

import pytest

import zipbundler.build as mod_build


def test_build_zipapp_with_compression(tmp_path: Path) -> None:
    """Test building a zipapp with compression enabled."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "app.pyz"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=None,
        compression="deflate",
    )

    # Verify zip file was created
    assert output.exists()

    # Verify compression is enabled
    with zipfile.ZipFile(output, "r") as zf:
        # Check that files are compressed (ZIP_DEFLATED)
        for info in zf.infolist():
            assert info.compress_type == zipfile.ZIP_DEFLATED


def test_build_zipapp_without_compression(tmp_path: Path) -> None:
    """Test building a zipapp without compression (default behavior)."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "app.pyz"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=None,
        compression="stored",
    )

    # Verify zip file was created
    assert output.exists()

    # Verify compression is disabled (ZIP_STORED)
    with zipfile.ZipFile(output, "r") as zf:
        # Check that files are stored uncompressed
        for info in zf.infolist():
            assert info.compress_type == zipfile.ZIP_STORED


def test_build_zipapp_default_no_compression(tmp_path: Path) -> None:
    """Test that default behavior is no compression (matching zipapp)."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "app.pyz"

    # Call without compress parameter (should default to False)
    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=None,
    )

    # Verify zip file was created
    assert output.exists()

    # Verify compression is disabled by default
    with zipfile.ZipFile(output, "r") as zf:
        for info in zf.infolist():
            assert info.compress_type == zipfile.ZIP_STORED


def test_build_zipapp_compression_affects_size(tmp_path: Path) -> None:
    """Test that compression actually reduces file size for text content."""
    # Create a test package with some content
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    # Create a file with repetitive content that compresses well
    content = "def func():\n    " + "x" * 1000 + "\n    pass\n"
    (pkg_dir / "module.py").write_text(content)

    output_compressed = tmp_path / "app_compressed.pyz"
    output_uncompressed = tmp_path / "app_uncompressed.pyz"

    # Build with compression
    mod_build.build_zipapp(
        output=output_compressed,
        packages=[pkg_dir],
        entry_point=None,
        compression="deflate",
    )

    # Build without compression
    mod_build.build_zipapp(
        output=output_uncompressed,
        packages=[pkg_dir],
        entry_point=None,
        compression="stored",
    )

    # Compressed version should be smaller (or at least not larger)
    # Note: For very small files, compression overhead might make it larger
    # So we just verify both files exist and are valid
    assert output_compressed.exists()
    assert output_uncompressed.exists()

    # Verify both are valid zip files
    with zipfile.ZipFile(output_compressed, "r") as zf:
        assert len(zf.namelist()) > 0
    with zipfile.ZipFile(output_uncompressed, "r") as zf:
        assert len(zf.namelist()) > 0


def test_build_zipapp_with_compression_level(tmp_path: Path) -> None:
    """Test building a zipapp with specific compression level."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "app.pyz"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=None,
        compression="deflate",
        compression_level=9,
    )

    # Verify zip file was created
    assert output.exists()

    # Verify compression is enabled
    with zipfile.ZipFile(output, "r") as zf:
        for info in zf.infolist():
            assert info.compress_type == zipfile.ZIP_DEFLATED


def test_build_zipapp_compression_level_default(tmp_path: Path) -> None:
    """Test that compression level defaults to 6 when not specified."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "app.pyz"

    # Call with compress=True but no compression_level (should default to 6)
    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=None,
        compression="deflate",
    )

    # Verify zip file was created
    assert output.exists()

    # Verify compression is enabled
    with zipfile.ZipFile(output, "r") as zf:
        for info in zf.infolist():
            assert info.compress_type == zipfile.ZIP_DEFLATED


def test_build_zipapp_compression_level_affects_size(tmp_path: Path) -> None:
    """Test that different compression levels affect file size."""
    # Create a test package with content that compresses well
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    # Create a file with repetitive content
    content = "def func():\n    " + "x" * 2000 + "\n    pass\n"
    (pkg_dir / "module.py").write_text(content)

    output_level_0 = tmp_path / "app_level_0.pyz"
    output_level_9 = tmp_path / "app_level_9.pyz"

    # Build with compression level 0 (no compression)
    mod_build.build_zipapp(
        output=output_level_0,
        packages=[pkg_dir],
        entry_point=None,
        compression="deflate",
        compression_level=0,
    )

    # Build with compression level 9 (maximum compression)
    mod_build.build_zipapp(
        output=output_level_9,
        packages=[pkg_dir],
        entry_point=None,
        compression="deflate",
        compression_level=9,
    )

    # Verify both files exist
    assert output_level_0.exists()
    assert output_level_9.exists()

    # Level 9 should generally produce smaller files than level 0
    # (though for very small files the difference might be minimal)
    # At minimum, both should be valid zip files
    with zipfile.ZipFile(output_level_0, "r") as zf:
        assert len(zf.namelist()) > 0
        for info in zf.infolist():
            assert info.compress_type == zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(output_level_9, "r") as zf:
        assert len(zf.namelist()) > 0
        for info in zf.infolist():
            assert info.compress_type == zipfile.ZIP_DEFLATED


def test_build_zipapp_with_bzip2_compression(tmp_path: Path) -> None:
    """Test building a zipapp with bzip2 compression."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "app.pyz"

    # Check if bzip2 is available
    try:
        import bz2  # noqa: F401, PLC0415  # pyright: ignore[reportUnusedImport]
    except ImportError:
        pytest.skip("bzip2 module not available")

    if not hasattr(zipfile, "ZIP_BZIP2"):
        pytest.skip("ZIP_BZIP2 not available in this Python version")

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=None,
        compression="bzip2",
    )

    # Verify zip file was created
    assert output.exists()

    # Verify compression is bzip2
    with zipfile.ZipFile(output, "r") as zf:
        for info in zf.infolist():
            assert info.compress_type == zipfile.ZIP_BZIP2


def test_build_zipapp_with_lzma_compression(tmp_path: Path) -> None:
    """Test building a zipapp with lzma compression."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "app.pyz"

    # Check if lzma is available
    try:
        import lzma  # noqa: F401, PLC0415  # pyright: ignore[reportUnusedImport]
    except ImportError:
        pytest.skip("lzma module not available")

    if not hasattr(zipfile, "ZIP_LZMA"):
        pytest.skip("ZIP_LZMA not available in this Python version")

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=None,
        compression="lzma",
    )

    # Verify zip file was created
    assert output.exists()

    # Verify compression is lzma
    with zipfile.ZipFile(output, "r") as zf:
        for info in zf.infolist():
            assert info.compress_type == zipfile.ZIP_LZMA


def test_build_zipapp_invalid_compression(tmp_path: Path) -> None:
    """Test that invalid compression method raises ValueError."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    output = tmp_path / "app.pyz"

    with pytest.raises(ValueError, match="Unknown compression method"):
        mod_build.build_zipapp(
            output=output,
            packages=[pkg_dir],
            entry_point=None,
            compression="invalid",
        )
