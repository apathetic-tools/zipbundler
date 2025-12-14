# src/zipbundler/build.py
"""Core build functionality for creating zipapp bundles."""

import io
import stat
import tempfile
import zipfile
from pathlib import Path

from apathetic_utils import is_excluded_raw

from .constants import DEFAULT_SOURCE_BASES
from .logs import getAppLogger


def _generate_pkg_info(metadata: dict[str, str] | None) -> str | None:
    """Generate PKG-INFO content from metadata dictionary.

    PKG-INFO follows the Python packaging metadata format (PEP 241/314).

    Args:
        metadata: Dictionary with optional keys: display_name, description,
            version, author, license

    Returns:
        PKG-INFO content as string, or None if no metadata provided
    """
    if not metadata:
        return None

    lines: list[str] = []
    # Required field: Name (use display_name or fallback)
    name = metadata.get("display_name") or metadata.get("name", "Unknown")
    lines.append(f"Name: {name}")

    # Optional fields
    if "version" in metadata:
        lines.append(f"Version: {metadata['version']}")
    if "description" in metadata:
        # PKG-INFO description can be multi-line, but we'll keep it simple
        desc = metadata["description"].replace("\n", " ")
        lines.append(f"Summary: {desc}")
    if "author" in metadata:
        lines.append(f"Author: {metadata['author']}")
    if "license" in metadata:
        lines.append(f"License: {metadata['license']}")

    # Add metadata version (PEP 314 format)
    lines.append("Metadata-Version: 2.1")

    return "\n".join(lines) + "\n"


def _matches_exclude_pattern(
    file_path: Path, _arcname: Path, exclude_patterns: list[str], root: Path
) -> bool:
    """Check if a path matches any exclude pattern.

    Uses apathetic_utils.is_excluded_raw for portable, cross-platform pattern matching.

    Args:
        file_path: Absolute file path
        _arcname: Relative path that will be used in the zip archive
            (unused, kept for API consistency)
        exclude_patterns: List of glob patterns to match against
        root: Root directory for resolving relative patterns

    Returns:
        True if the path matches any exclude pattern, False otherwise
    """
    if not exclude_patterns:
        return False

    # Use apathetic_utils for portable pattern matching
    # It handles ** patterns, cross-platform path separators, and root-relative patterns
    return is_excluded_raw(file_path, exclude_patterns, root)


def _get_compression_method(compression: str | None) -> tuple[int, str]:
    """Get zipfile compression constant and method name from compression string.

    Args:
        compression: Compression method string ("deflate", "stored", "bzip2", "lzma")

    Returns:
        Tuple of (compression_constant, method_name)

    Raises:
        ValueError: If compression method is not supported or required modules
            unavailable
    """
    if compression is None or compression == "stored":
        return zipfile.ZIP_STORED, "stored"

    if compression == "deflate":
        return zipfile.ZIP_DEFLATED, "deflate"

    if compression == "bzip2":
        if not hasattr(zipfile, "ZIP_BZIP2"):
            msg = "bzip2 compression not available in this Python version"
            raise ValueError(msg)
        try:
            import bz2  # noqa: F401, PLC0415  # pyright: ignore[reportUnusedImport]
        except ImportError:
            msg = "bzip2 compression requires the bz2 module"
            raise ValueError(msg) from None
        return zipfile.ZIP_BZIP2, "bzip2"

    if compression == "lzma":
        if not hasattr(zipfile, "ZIP_LZMA"):
            msg = "lzma compression not available in this Python version"
            raise ValueError(msg)
        try:
            import lzma  # noqa: F401, PLC0415  # pyright: ignore[reportUnusedImport]
        except ImportError:
            msg = "lzma compression requires the lzma module"
            raise ValueError(msg) from None
        return zipfile.ZIP_LZMA, "lzma"

    valid_methods = ["deflate", "stored", "bzip2", "lzma"]
    methods_str = ", ".join(valid_methods)
    msg = f"Unknown compression method: {compression}. Valid options: {methods_str}"
    raise ValueError(msg)


def _needs_rebuild(
    output: Path,
    source_files: list[tuple[Path, Path]],
) -> bool:
    """Check if rebuild is needed based on file modification times.

    Args:
        output: Output file path
        source_files: List of tuples (file_path, arcname) for source files

    Returns:
        True if rebuild is needed, False if output is up-to-date

    Note:
        We don't check entry_point content here since it's a string, not a file.
        If entry_point changes, the caller should force rebuild.
        This is a limitation but acceptable for incremental builds.
    """
    # If output doesn't exist, rebuild is needed
    if not output.exists():
        return True

    # Get output file modification time
    output_mtime = output.stat().st_mtime

    # Check if any source file is newer than output
    for file_path, _arcname in source_files:
        if not file_path.exists():
            # File was deleted, rebuild needed
            return True
        if file_path.stat().st_mtime > output_mtime:
            return True

    return False


def build_zipapp(  # noqa: C901, PLR0912, PLR0913, PLR0915
    output: Path,
    packages: list[Path],
    entry_point: str | None = None,
    shebang: str | None = "#!/usr/bin/env python3",
    *,
    compression: str | None = None,
    compression_level: int | None = None,
    dry_run: bool = False,
    exclude: list[str] | None = None,
    main_guard: bool = True,
    metadata: dict[str, str] | None = None,
    force: bool = False,
    additional_includes: list[tuple[Path, Path | None]] | None = None,
) -> None:
    """Build a zipapp-compatible zip file.

    Args:
        output: Output file path for the zipapp
        packages: List of package directories to include
        entry_point: Entry point code to write to __main__.py.
            If None, no __main__.py is created.
        shebang: Shebang line to prepend to the zip file.
            If None or empty string, no shebang is added.
        compression: Compression method ("deflate", "stored", "bzip2", "lzma").
            Defaults to None which maps to "stored" (no compression).
        compression_level: Compression level for deflate method (0-9).
            Only used when compression="deflate". Defaults to 6 if not specified.
            Higher values = more compression but slower.
        dry_run: If True, preview what would be bundled without creating zip.
        exclude: Optional list of glob patterns for files/directories to exclude.
        main_guard: If True, wrap entry point in `if __name__ == "__main__":` guard.
            Defaults to True. Only applies when entry_point is provided.
        metadata: Optional dictionary with metadata fields (display_name, description,
            version, author, license). If provided, a PKG-INFO file will be written
            to the zip archive.
        force: If True, always rebuild even if output is up-to-date.
            Defaults to False. When False, skips rebuild if output is newer
            than all sources.
        additional_includes: Optional list of (file_path, destination) tuples
            for individual files to include in the zip. If destination is None,
            uses the file's basename. Useful for including data files or configs.

    Raises:
        ValueError: If output path is invalid or packages are empty
    """
    logger = getAppLogger()

    if not packages:
        xmsg = "At least one package must be provided"
        raise ValueError(xmsg)

    compression_const, compression_name = _get_compression_method(compression)
    # Default compression level is 6 (zlib default) if not specified for deflate
    if compression_level is None and compression_name == "deflate":
        compression_level = 6
    exclude_patterns = exclude or []
    logger.debug("Building zipapp: %s", output)
    logger.debug("Packages: %s", [str(p) for p in packages])
    logger.debug("Entry point: %s", entry_point)
    if compression_level is not None and compression_name == "deflate":
        logger.debug("Compression: %s (level %d)", compression_name, compression_level)
    else:
        logger.debug("Compression: %s", compression_name)
    logger.debug("Dry run: %s", dry_run)
    if exclude_patterns:
        logger.debug("Exclude patterns: %s", exclude_patterns)

    # Collect files that would be included
    files_to_include: list[tuple[Path, Path]] = []

    # Add all Python files from packages
    for pkg in packages:
        pkg_path = Path(pkg).resolve()
        if not pkg_path.exists():
            logger.warning("Package path does not exist: %s", pkg_path)
            continue

        # Determine the exclude root:
        # If the package is a common source directory (src, lib, packages),
        # use it as the exclude root so packages end up at the root of the zip.
        # Otherwise, use the package parent.
        # This ensures src/zipbundler ends up as zipbundler/ not src/zipbundler/
        exclude_root = pkg_path.parent
        if pkg_path.name in DEFAULT_SOURCE_BASES:
            # This is a source directory - use it as root so packages extract to root
            exclude_root = pkg_path
            logger.trace(
                "Detected source directory '%s', using it as exclude root",
                pkg_path.name,
            )

        for f in pkg_path.rglob("*.py"):
            # Calculate relative path from exclude root
            arcname = f.relative_to(exclude_root)
            # Check if file matches exclude patterns
            if _matches_exclude_pattern(f, arcname, exclude_patterns, exclude_root):
                logger.trace("Excluded file: %s (matched pattern)", f)
                continue
            files_to_include.append((f, arcname))
            logger.trace("Added file: %s -> %s", f, arcname)

    # Add additional individual files (from --add-include)
    if additional_includes:
        for file_path, dest in additional_includes:
            if not file_path.exists():
                logger.warning("Additional include file does not exist: %s", file_path)
                continue
            # Use provided destination or file's basename
            arcname = Path(dest) if dest else Path(file_path.name)
            files_to_include.append((file_path, arcname))
            logger.trace("Added additional file: %s -> %s", file_path, arcname)

    # Count entry point in file count if provided
    file_count = len(files_to_include) + (1 if entry_point is not None else 0)

    # Incremental build check: skip if output is up-to-date
    if (
        not force
        and not dry_run
        and output.exists()
        and not _needs_rebuild(output, files_to_include)
    ):
        logger.info("⏭️  Skipping rebuild: %s is up-to-date", output)
        return

    # Dry-run mode: show summary and exit
    if dry_run:
        logger.info("🧪 Dry-run mode: no files will be written or deleted.\n")
        summary_parts: list[str] = []
        summary_parts.append(f"Output: {output}")
        summary_parts.append(f"Packages: {len(packages)}")
        summary_parts.append(f"Files: {file_count}")
        if entry_point is not None:
            summary_parts.append("Entry point: yes")
        if compression_level is not None and compression_name == "deflate":
            summary_parts.append(
                f"Compression: {compression_name} (level {compression_level})"
            )
        else:
            summary_parts.append(f"Compression: {compression_name}")
        if shebang:
            summary_parts.append(f"Shebang: {shebang}")
        else:
            summary_parts.append("Shebang: none")
        logger.info("🧪 (dry-run) Would create zipapp: %s", " • ".join(summary_parts))
        return

    # Normal build mode: create the zip file
    output.parent.mkdir(parents=True, exist_ok=True)

    # Use compresslevel parameter when compression is ZIP_DEFLATED
    compresslevel: int | None = (
        compression_level if compression_const == zipfile.ZIP_DEFLATED else None
    )

    with zipfile.ZipFile(
        output, "w", compression=compression_const, compresslevel=compresslevel
    ) as zf:
        # Write PKG-INFO if metadata is provided
        pkg_info = _generate_pkg_info(metadata)
        if pkg_info:
            zf.writestr("PKG-INFO", pkg_info)
            logger.debug("Wrote PKG-INFO with metadata")

        # Write entry point if provided
        if entry_point is not None:
            # Wrap entry point in main guard if requested
            if main_guard:
                # Indent each line of entry_point by 4 spaces
                indented_lines = [
                    "    " + line if line.strip() else line
                    for line in entry_point.splitlines(keepends=True)
                ]
                indented_code = "".join(indented_lines)
                # Remove trailing newline from indented code if present
                indented_code = indented_code.removesuffix("\n")
                main_content = f"if __name__ == '__main__':\n{indented_code}"
            else:
                main_content = entry_point
            zf.writestr("__main__.py", main_content)
            logger.debug(
                "Wrote __main__.py with entry point (main_guard=%s)", main_guard
            )

        # Add all Python files from packages
        for file_path, arcname in files_to_include:
            zf.write(file_path, arcname)

    # Prepend shebang if provided
    if shebang:
        data = output.read_bytes()
        output.write_bytes(shebang.encode() + b"\n" + data)

    # Make executable
    output.chmod(output.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    logger.info("Created zipapp: %s", output)


def list_files(
    packages: list[Path],
    *,
    count: bool = False,
    exclude: list[str] | None = None,
) -> list[tuple[Path, Path]]:
    """List files that would be included in a zipapp bundle.

    Args:
        packages: List of package directories to scan
        count: If True, only return count (empty list, count in logger)
        exclude: Optional list of glob patterns for files/directories to exclude.

    Returns:
        List of tuples (file_path, arcname) for files that would be included
    """
    logger = getAppLogger()

    if not packages:
        xmsg = "At least one package must be provided"
        raise ValueError(xmsg)

    exclude_patterns = exclude or []
    if exclude_patterns:
        logger.debug("Exclude patterns: %s", exclude_patterns)

    files_to_include: list[tuple[Path, Path]] = []

    # Add all Python files from packages
    for pkg in packages:
        pkg_path = Path(pkg).resolve()
        if not pkg_path.exists():
            logger.warning("Package path does not exist: %s", pkg_path)
            continue

        # Use package parent as root for exclude pattern matching
        exclude_root = pkg_path.parent

        for f in pkg_path.rglob("*.py"):
            # Calculate relative path from package parent
            arcname = f.relative_to(exclude_root)
            # Check if file matches exclude patterns
            if _matches_exclude_pattern(f, arcname, exclude_patterns, exclude_root):
                logger.trace("Excluded file: %s (matched pattern)", f)
                continue
            files_to_include.append((f, arcname))
            logger.trace("Found file: %s -> %s", f, arcname)

    if count:
        logger.info("Files: %d", len(files_to_include))
        return []

    return files_to_include


def extract_archive_to_tempdir(archive: Path | str) -> Path:
    """Extract a zipapp archive to a temporary directory.

    This function extracts all files from a .pyz archive (skipping the shebang)
    to a temporary directory, which can then be used as a source for building.

    Args:
        archive: Path to the zipapp archive (.pyz file)

    Returns:
        Path to the temporary directory containing extracted files

    Raises:
        FileNotFoundError: If the archive file does not exist
        ValueError: If the archive is not a valid zip file
        zipfile.BadZipFile: If the archive is corrupted
    """
    logger = getAppLogger()
    archive_path = Path(archive).resolve()

    if not archive_path.exists():
        msg = f"Archive not found: {archive_path}"
        raise FileNotFoundError(msg)

    if not archive_path.is_file():
        msg = f"Archive path is not a file: {archive_path}"
        raise ValueError(msg)

    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix="zipbundler_extract_"))
    logger.debug(
        "Extracting archive %s to temporary directory: %s", archive_path, temp_dir
    )

    # Read the archive, skipping shebang if present
    with archive_path.open("rb") as f:
        # Check for shebang (first 2 bytes are #!)
        first_two = f.read(2)
        if first_two == b"#!":
            # Skip shebang line
            f.readline()
        else:
            # No shebang, rewind to start
            f.seek(0)

        # Read remaining data (the zip file)
        zip_data = f.read()

    # Write zip data to temporary file
    temp_zip = temp_dir / "archive.zip"
    temp_zip.write_bytes(zip_data)

    # Extract zip file
    try:
        with zipfile.ZipFile(temp_zip, "r") as zf:
            zf.extractall(temp_dir)
        # Remove temporary zip file
        temp_zip.unlink()
        logger.debug("Extracted %d files from archive", len(list(temp_dir.rglob("*"))))
    except zipfile.BadZipFile as e:
        msg = f"Invalid zip file in archive: {archive_path}"
        raise ValueError(msg) from e

    return temp_dir


def get_interpreter(archive: Path | str) -> str | None:
    """Get the interpreter from an existing zipapp archive.

    This function is compatible with Python's zipapp.get_interpreter().

    Args:
        archive: Path to the zipapp archive (.pyz file)

    Returns:
        The interpreter string (shebang line without #!), or None if no
        shebang is present

    Raises:
        FileNotFoundError: If the archive file does not exist
        ValueError: If the archive is not a valid zipapp file
    """
    archive_path = Path(archive)
    if not archive_path.exists():
        msg = f"Archive not found: {archive_path}"
        raise FileNotFoundError(msg)

    # Read first 2 bytes to check for shebang
    with archive_path.open("rb") as f:
        if f.read(2) != b"#!":
            return None

        # Read the rest of the shebang line
        # Use 'utf-8' encoding with error handling, matching zipapp behavior
        line = f.readline().strip()
        try:
            return line.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback to latin-1 if utf-8 fails (matches zipapp behavior)
            return line.decode("latin-1")


def list_files_from_archive(
    archive: Path | str,
    *,
    count: bool = False,
) -> list[tuple[Path, Path]]:
    """List files contained in a zipapp archive.

    Args:
        archive: Path to the zipapp archive (.pyz file)
        count: If True, only return count (empty list, count in logger)

    Returns:
        List of tuples (file_path, arcname) for files in the archive.
        file_path is a placeholder Path object (not a real file system path).
        arcname is the path within the archive.

    Raises:
        FileNotFoundError: If the archive file does not exist
        ValueError: If the archive is not a valid zipapp file
        zipfile.BadZipFile: If the archive is corrupted
    """
    logger = getAppLogger()
    archive_path = Path(archive)
    if not archive_path.exists():
        msg = f"Archive not found: {archive_path}"
        raise FileNotFoundError(msg)

    # Read the archive, skipping shebang if present
    with archive_path.open("rb") as f:
        # Check for shebang (first 2 bytes are #!)
        first_two = f.read(2)
        if first_two == b"#!":
            # Skip shebang line
            f.readline()
        else:
            # No shebang, rewind to start
            f.seek(0)

        # Read remaining data (the zip file)
        zip_data = f.read()

    # Open zip file from memory
    try:
        with zipfile.ZipFile(io.BytesIO(zip_data), "r") as zf:
            # Get all file names from the archive
            file_names = zf.namelist()

            # Filter to only Python files (and special files like __main__.py, PKG-INFO)
            # This matches the behavior of list_files which only includes .py files
            python_files = [
                name
                for name in file_names
                if name.endswith(".py") or name in ("__main__.py", "PKG-INFO")
            ]

            if count:
                logger.info("Files: %d", len(python_files))
                return []

            # Create tuples with placeholder Path and arcname
            files: list[tuple[Path, Path]] = []
            for name in python_files:
                # Use archive path as placeholder for file_path
                # arcname is the path within the archive
                arcname = Path(name)
                files.append((archive_path, arcname))
                logger.trace("Found file in archive: %s", arcname)

            return files
    except zipfile.BadZipFile as e:
        msg = f"Invalid zip file in archive: {archive_path}"
        raise ValueError(msg) from e


def get_metadata_from_archive(archive: Path | str) -> dict[str, str] | None:
    """Get metadata from PKG-INFO in an existing zipapp archive.

    Args:
        archive: Path to the zipapp archive (.pyz file)

    Returns:
        Dictionary with metadata fields (display_name, description, version,
        author, license), or None if PKG-INFO is not present

    Raises:
        FileNotFoundError: If the archive file does not exist
        ValueError: If the archive is not a valid zipapp file
        zipfile.BadZipFile: If the archive is corrupted
    """
    archive_path = Path(archive)
    if not archive_path.exists():
        msg = f"Archive not found: {archive_path}"
        raise FileNotFoundError(msg)

    # Read the archive, skipping shebang if present
    with archive_path.open("rb") as f:
        # Check for shebang (first 2 bytes are #!)
        first_two = f.read(2)
        if first_two == b"#!":
            # Skip shebang line
            f.readline()
        else:
            # No shebang, rewind to start
            f.seek(0)

        # Read remaining data (the zip file)
        zip_data = f.read()

    # Open zip file from memory
    try:
        with zipfile.ZipFile(io.BytesIO(zip_data), "r") as zf:
            if "PKG-INFO" not in zf.namelist():
                return None

            # Read PKG-INFO content
            pkg_info_bytes = zf.read("PKG-INFO")
            pkg_info_text = pkg_info_bytes.decode("utf-8")

            # Parse PKG-INFO format (key: value lines)
            metadata: dict[str, str] = {}
            for line in pkg_info_text.splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    # Map PKG-INFO fields to our metadata format
                    if key == "Name":
                        metadata["display_name"] = value
                    elif key == "Version":
                        metadata["version"] = value
                    elif key == "Summary":
                        metadata["description"] = value
                    elif key == "Author":
                        metadata["author"] = value
                    elif key == "License":
                        metadata["license"] = value

            return metadata if metadata else None
    except zipfile.BadZipFile as e:
        msg = f"Invalid zip file in archive: {archive_path}"
        raise ValueError(msg) from e
