# src/zipbundler/commands/info.py

"""Handle the --info flag for displaying interpreter from archive."""

import argparse

from zipbundler.build import get_interpreter
from zipbundler.logs import getAppLogger


def handle_info_command(
    source: str | None,
    parser: argparse.ArgumentParser,
) -> int:
    """Handle the --info flag for displaying interpreter from archive.

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
        interpreter = get_interpreter(source)
        if interpreter is None:
            logger.info("No interpreter specified in archive")
        else:
            logger.info(interpreter)
    except (FileNotFoundError, ValueError):
        logger.exception("Failed to get interpreter from archive")
        return 1
    except Exception as e:  # noqa: BLE001
        logger.criticalIfNotDebug("Unexpected error: %s", e)
        return 1
    else:
        return 0
