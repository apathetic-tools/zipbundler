"""Utilities for compression configuration resolution."""

import argparse

from apathetic_utils import cast_hint

from zipbundler.constants import DEFAULT_COMPRESS
from zipbundler.logs import getAppLogger


def resolve_compress(
    raw_config: dict[str, object] | None,
    *,
    args: argparse.Namespace,
) -> bool:
    """Determine whether to compress the zip file.

    Handles the following precedence (highest to lowest):
    1. CLI flag: --compress or --no-compress
    2. Config file: options.compress
    3. Default: DEFAULT_COMPRESS

    Args:
        raw_config: Raw configuration dict from config file (may be None)
        args: Parsed command-line arguments

    Returns:
        Boolean indicating whether to compress the zip file
    """
    logger = getAppLogger()

    # Case 1: CLI flag (highest priority)
    cli_flag: object = getattr(args, "compress", None)
    if cli_flag is not None and isinstance(cli_flag, bool):
        logger.trace(
            "[resolve_compress] Using CLI flag: compress=%s",
            cli_flag,
        )
        return cli_flag

    # Case 2: Config file (options.compress)
    if raw_config:
        options: object = raw_config.get("options")
        if isinstance(options, dict):
            opts_dict = cast_hint(dict[str, object], options)
            compress: object = opts_dict.get("compress")
            if isinstance(compress, bool):
                logger.trace(
                    "[resolve_compress] Using config: compress=%s",
                    compress,
                )
                return compress

    # Case 3: Default
    logger.trace(
        "[resolve_compress] Using default: compress=%s",
        DEFAULT_COMPRESS,
    )
    return DEFAULT_COMPRESS
