# src/zipbundler/build.py
"""Core build functionality for creating zipapp bundles."""

import stat
import zipfile
from pathlib import Path

from .logs import getAppLogger


def build_zipapp(
    output: Path,
    packages: list[Path],
    entry_point: str | None = None,
    shebang: str = "#!/usr/bin/env python3",
    *,
    compress: bool = False,
    dry_run: bool = False,
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
        dry_run: If True, preview what would be bundled without creating zip.

    Raises:
        ValueError: If output path is invalid or packages are empty
    """
    logger = getAppLogger()

    if not packages:
        xmsg = "At least one package must be provided"
        raise ValueError(xmsg)

    compression = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
    logger.debug("Building zipapp: %s", output)
    logger.debug("Packages: %s", [str(p) for p in packages])
    logger.debug("Entry point: %s", entry_point)
    logger.debug("Compression: %s", "deflate" if compress else "stored")
    logger.debug("Dry run: %s", dry_run)

    # Collect files that would be included
    files_to_include: list[tuple[Path, Path]] = []

    # Add all Python files from packages
    for pkg in packages:
        pkg_path = Path(pkg).resolve()
        if not pkg_path.exists():
            logger.warning("Package path does not exist: %s", pkg_path)
            continue

        for f in pkg_path.rglob("*.py"):
            # Calculate relative path from package parent
            arcname = f.relative_to(pkg_path.parent)
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
        summary_parts.append(f"Compression: {'deflate' if compress else 'stored'}")
        summary_parts.append(f"Shebang: {shebang}")
        logger.info("🧪 (dry-run) Would create zipapp: %s", " • ".join(summary_parts))
        return

    # Normal build mode: create the zip file
    output.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output, "w", compression) as zf:
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
