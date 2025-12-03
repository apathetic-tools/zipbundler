# src/zipbundler/build.py
"""Core build functionality for creating zipapp bundles."""

import stat
import zipfile
from pathlib import Path

from apathetic_utils import is_excluded_raw

from .logs import getAppLogger


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


def build_zipapp(  # noqa: PLR0912, PLR0915
    output: Path,
    packages: list[Path],
    entry_point: str | None = None,
    shebang: str = "#!/usr/bin/env python3",
    *,
    compress: bool = False,
    compression_level: int | None = None,
    dry_run: bool = False,
    exclude: list[str] | None = None,
) -> None:
    """Build a zipapp-compatible zip file.

    Args:
        output: Output file path for the zipapp
        packages: List of package directories to include
        entry_point: Entry point code to write to __main__.py.
            If None, no __main__.py is created.
        shebang: Shebang line to prepend to the zip file
        compress: Whether to compress the zip file using deflate method.
            Defaults to False (no compression) to match zipapp behavior.
        compression_level: Compression level for deflate method (0-9).
            Only used when compress=True. Defaults to 6 if not specified.
            Higher values = more compression but slower.
        dry_run: If True, preview what would be bundled without creating zip.
        exclude: Optional list of glob patterns for files/directories to exclude.

    Raises:
        ValueError: If output path is invalid or packages are empty
    """
    logger = getAppLogger()

    if not packages:
        xmsg = "At least one package must be provided"
        raise ValueError(xmsg)

    compression = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
    # Default compression level is 6 (zlib default) if not specified
    if compression_level is None:
        compression_level = 6
    exclude_patterns = exclude or []
    logger.debug("Building zipapp: %s", output)
    logger.debug("Packages: %s", [str(p) for p in packages])
    logger.debug("Entry point: %s", entry_point)
    if compress:
        logger.debug("Compression: deflate (level %d)", compression_level)
    else:
        logger.debug("Compression: stored")
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
            logger.trace("Added file: %s -> %s", f, arcname)

    # Count entry point in file count if provided
    file_count = len(files_to_include) + (1 if entry_point is not None else 0)

    # Dry-run mode: show summary and exit
    if dry_run:
        logger.info("🧪 Dry-run mode: no files will be written or deleted.\n")
        summary_parts: list[str] = []
        summary_parts.append(f"Output: {output}")
        summary_parts.append(f"Packages: {len(packages)}")
        summary_parts.append(f"Files: {file_count}")
        if entry_point is not None:
            summary_parts.append("Entry point: yes")
        if compress:
            summary_parts.append(f"Compression: deflate (level {compression_level})")
        else:
            summary_parts.append("Compression: stored")
        summary_parts.append(f"Shebang: {shebang}")
        logger.info("🧪 (dry-run) Would create zipapp: %s", " • ".join(summary_parts))
        return

    # Normal build mode: create the zip file
    output.parent.mkdir(parents=True, exist_ok=True)

    # Use compresslevel parameter when compression is ZIP_DEFLATED
    compresslevel: int | None = (
        compression_level if compression == zipfile.ZIP_DEFLATED else None
    )

    with zipfile.ZipFile(output, "w", compression, compresslevel=compresslevel) as zf:
        # Write entry point if provided
        if entry_point is not None:
            zf.writestr("__main__.py", entry_point)
            logger.debug("Wrote __main__.py with entry point")

        # Add all Python files from packages
        for file_path, arcname in files_to_include:
            zf.write(file_path, arcname)

    # Prepend shebang
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
