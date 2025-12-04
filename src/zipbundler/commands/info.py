# src/zipbundler/commands/info.py

"""Handle the --info flag for displaying interpreter and metadata from archive."""

import argparse

from zipbundler.build import get_interpreter, get_metadata_from_archive
from zipbundler.logs import getAppLogger


def handle_info_command(
    source: str | None,
    parser: argparse.ArgumentParser,
) -> int:
    """Handle the --info flag for displaying interpreter and metadata from archive.

    Args:
        source: Path to the archive file
        parser: Argument parser for error handling

    Returns:
        Exit code (0 for success, 1 for error).
    """
    logger = getAppLogger()

    if not source:
        parser.error("--info requires SOURCE archive path")
        return 1  # pragma: no cover

    try:
        # Display interpreter
        interpreter = get_interpreter(source)
        if interpreter is None:
            logger.info("No interpreter specified in archive")
        else:
            logger.info("Interpreter: %s", interpreter)

        # Display metadata if present
        metadata = get_metadata_from_archive(source)
        if metadata:
            logger.info("")
            logger.info("Metadata:")
            if "display_name" in metadata:
                logger.info("  Name: %s", metadata["display_name"])
            if "version" in metadata:
                logger.info("  Version: %s", metadata["version"])
            if "description" in metadata:
                logger.info("  Description: %s", metadata["description"])
            if "author" in metadata:
                logger.info("  Author: %s", metadata["author"])
            if "license" in metadata:
                logger.info("  License: %s", metadata["license"])
    except (FileNotFoundError, ValueError):
        logger.exception("Failed to get info from archive")
        return 1
    except Exception as e:  # noqa: BLE001
        logger.criticalIfNotDebug("Unexpected error: %s", e)
        return 1
    else:
        return 0
