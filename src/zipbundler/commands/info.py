# src/zipbundler/commands/info.py

"""Handle the --info flag for displaying interpreter and metadata from archive."""

import argparse
from pathlib import Path

from apathetic_logging import Logger

from zipbundler.build import get_interpreter, get_metadata_from_archive
from zipbundler.logs import getAppLogger


def _display_metadata(logger: Logger, metadata: dict[str, str]) -> None:
    """Display metadata from archive."""
    logger.info("")
    logger.info("Metadata:")
    fields = [
        ("display_name", "Name"),
        ("version", "Version"),
        ("description", "Description"),
        ("author", "Author"),
        ("license", "License"),
    ]
    for key, label in fields:
        if key in metadata:
            logger.info("  %s: %s", label, metadata[key])


def handle_info_command(
    source: str | None,
    parser: argparse.ArgumentParser,
) -> int:
    """Handle the --info flag for displaying interpreter and metadata from archive.

    If source is a directory, auto-derives the output filename (source.stem + .pyz)
    and looks for the built archive in that location.

    Args:
        source: Path to the archive file or directory
        parser: Argument parser for error handling

    Returns:
        Exit code (0 for success, 1 for error).
    """
    logger = getAppLogger()

    if not source:
        parser.error("--info requires SOURCE archive path")
        return 1  # pragma: no cover

    source_path = Path(source).resolve()

    # If source is a directory, derive the output filename
    if source_path.is_dir():
        # Auto-derive output name: directory name + .pyz
        archive_path = source_path / f"{source_path.name}.pyz"
        logger.debug("Source is a directory, looking for archive: %s", archive_path)
    else:
        archive_path = source_path

    try:
        # Display interpreter
        interpreter = get_interpreter(archive_path)
        if interpreter is None:
            logger.info("No interpreter specified in archive")
        else:
            logger.info("Interpreter: %s", interpreter)

        # Display metadata if present
        metadata = get_metadata_from_archive(archive_path)
        if metadata:
            _display_metadata(logger, metadata)
    except (FileNotFoundError, ValueError):
        logger.exception("Failed to get info from archive")
        return 1
    except Exception as e:  # noqa: BLE001
        logger.criticalIfNotDebug("Unexpected error: %s", e)
        return 1
    else:
        return 0
