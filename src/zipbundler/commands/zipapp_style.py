# src/zipbundler/commands/zipapp_style.py
# ruff: noqa: PLR0911, PLR0912

"""Handle zipapp-style CLI usage: zipbundler SOURCE [OPTIONS]."""

import argparse
import shutil
from pathlib import Path

from zipbundler.build import build_zipapp, extract_archive_to_tempdir
from zipbundler.commands.build import extract_entry_point_code
from zipbundler.logs import getAppLogger


def _is_archive_file(source: Path) -> bool:
    """Check if source is a zipapp archive file.

    Args:
        source: Path to check

    Returns:
        True if source appears to be a .pyz archive file
    """
    if not source.exists() or not source.is_file():
        return False
    # Check extension
    if source.suffix == ".pyz":
        return True
    # Check if it starts with shebang and contains zip data
    try:
        with source.open("rb") as f:
            first_two = f.read(2)
            if first_two == b"#!":
                # Skip shebang line
                f.readline()
                # Check if remaining data looks like a zip file
                # ZIP files start with PK\x03\x04 or PK\x05\x06 or PK\x07\x08
                zip_magic = f.read(2)
                return zip_magic in (b"PK\x03", b"PK\x05", b"PK\x07")
    except Exception as e:  # noqa: BLE001
        # Log exception for debugging but don't fail
        logger = getAppLogger()
        logger.trace("Error checking if file is archive: %s", e)
    return False


def handle_zipapp_style_command(args: argparse.Namespace) -> int:  # noqa: PLR0915
    """Handle zipapp-style CLI: zipbundler SOURCE [OPTIONS].

    This implements the zipapp-compatible interface where SOURCE can be:
    - A directory (normal case)
    - A .pyz archive file (extracts to temp dir first)

    Args:
        args: Parsed arguments with 'source' and zipapp-style options

    Returns:
        Exit code (0 for success, 1 for error)
    """
    logger = getAppLogger()

    source_str = getattr(args, "source", None)
    if not source_str:
        logger.error("SOURCE is required")
        return 1

    source = Path(source_str).resolve()
    if not source.exists():
        logger.error("SOURCE not found: %s", source)
        return 1

    # Check if source is an archive
    temp_dir: Path | None = None
    if _is_archive_file(source):
        logger.debug("SOURCE is an archive file, extracting to temporary directory")
        try:
            temp_dir = extract_archive_to_tempdir(source)
            # Use extracted directory as source
            packages = [temp_dir]
        except (FileNotFoundError, ValueError):
            logger.exception("Failed to extract archive")
            return 1
    elif source.is_dir():
        packages = [source]
    else:
        logger.error("SOURCE must be a directory or .pyz archive file: %s", source)
        return 1

    # Extract options from args
    output_str = getattr(args, "output", None)
    if not output_str:
        logger.error("Output file (-o/--output) is required when using SOURCE")
        return 1

    output = Path(output_str).resolve()

    # Extract entry point
    entry_point_str = getattr(args, "entry_point", None)
    entry_point_code: str | None = None
    if entry_point_str:
        entry_point_code = extract_entry_point_code(entry_point_str)

    # Extract shebang
    shebang: str | None = None
    if hasattr(args, "shebang"):
        if args.shebang is False:
            shebang = None
        elif args.shebang:
            if args.shebang.startswith("#!"):
                shebang = args.shebang
            else:
                shebang = f"#!{args.shebang}"
        else:
            # Default shebang if not explicitly disabled
            shebang = "#!/usr/bin/env python3"

    # Extract compression
    compress = getattr(args, "compress", False)
    compression = "deflate" if compress else "stored"

    # Build the zipapp
    try:
        build_zipapp(
            output=output,
            packages=packages,
            entry_point=entry_point_code,
            shebang=shebang,
            compression=compression,
        )
    except Exception:
        logger.exception("Failed to build zipapp")
        return 1
    else:
        return 0
    finally:
        # Clean up temporary directory if we created one
        if temp_dir and temp_dir.exists():
            logger.debug("Cleaning up temporary directory: %s", temp_dir)
            shutil.rmtree(temp_dir, ignore_errors=True)
