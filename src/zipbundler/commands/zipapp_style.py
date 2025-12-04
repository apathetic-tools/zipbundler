# src/zipbundler/commands/zipapp_style.py
# ruff: noqa: PLR0911, PLR0912

"""Handle zipapp-style CLI usage: zipbundler SOURCE [OPTIONS]."""

import argparse
import shutil
from pathlib import Path

from apathetic_utils import find_all_packages_under_path

from zipbundler.build import build_zipapp, extract_archive_to_tempdir
from zipbundler.commands.build import extract_entry_point_code
from zipbundler.logs import getAppLogger


def is_archive_file(source: Path) -> bool:
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


def handle_zipapp_style_command(args: argparse.Namespace) -> int:  # noqa: C901, PLR0915
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
    packages: list[Path] = []
    if is_archive_file(source):
        logger.debug("SOURCE is an archive file, extracting to temporary directory")
        try:
            temp_dir = extract_archive_to_tempdir(source)
            # Use extracted directory as source
            packages = [temp_dir]
        except (FileNotFoundError, ValueError):
            logger.exception("Failed to extract archive")
            return 1
    elif source.is_dir():
        # Check if the directory itself is a package (has __init__.py)
        is_package = (source / "__init__.py").exists()
        if is_package:
            # Directory is itself a package, use it directly
            logger.debug("SOURCE directory is a package: %s", source)
            packages = [source]
        else:
            # Automatically discover Python packages in the directory
            try:
                found_packages = find_all_packages_under_path(source)
                if found_packages:
                    # Convert package names to paths
                    for pkg_name in found_packages:
                        pkg_path = source / pkg_name.replace(".", "/")
                        if pkg_path.exists() and pkg_path.is_dir():
                            packages.append(pkg_path.resolve())
                            logger.debug("Discovered package: %s", pkg_path)
                    if not packages:
                        # Fallback: use the directory itself if no packages found
                        logger.debug(
                            "No packages discovered, using directory as package: %s",
                            source,
                        )
                        packages = [source]
                else:
                    # No packages found, use the directory itself
                    logger.debug(
                        "No packages discovered, using directory as package: %s", source
                    )
                    packages = [source]
            except (IndexError, ValueError):
                # If discovery fails, fall back to using directory itself
                logger.debug(
                    "Package discovery failed, using directory as package: %s", source
                )
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
    # Match Python's zipapp behavior: no shebang by default, only when -p is specified
    shebang: str | None = None
    if hasattr(args, "shebang"):
        if args.shebang is False:
            # --no-shebang explicitly disables shebang
            shebang = None
        elif args.shebang:
            # -p/--python was specified, use it
            if args.shebang.startswith("#!"):
                shebang = args.shebang
            else:
                shebang = f"#!{args.shebang}"
        # else: args.shebang is None (default), no shebang (matches zipapp behavior)

    # Extract compression
    compress = getattr(args, "compress", False)
    compression = "deflate" if compress else "stored"

    # Extract compression level
    compression_level: int | None = getattr(args, "compression_level", None)
    if compression_level is not None and compression != "deflate":
        # compression_level only applies to deflate, ensure compression is deflate
        compression = "deflate"

    # Build the zipapp
    try:
        build_zipapp(
            output=output,
            packages=packages,
            entry_point=entry_point_code,
            shebang=shebang,
            compression=compression,
            compression_level=compression_level,
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
