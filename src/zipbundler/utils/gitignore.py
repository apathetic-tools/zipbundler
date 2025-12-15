"""Utilities for gitignore handling and respect configuration."""

import argparse
from pathlib import Path

from apathetic_utils import cast_hint

from zipbundler.constants import DEFAULT_RESPECT_GITIGNORE
from zipbundler.logs import getAppLogger


def load_gitignore_patterns(gitignore_path: Path) -> list[str]:
    """Load patterns from .gitignore file.

    Reads .gitignore and returns non-comment patterns. Skips blank lines
    and lines starting with '#'.

    Args:
        gitignore_path: Path to .gitignore file

    Returns:
        List of gitignore pattern strings
    """
    logger = getAppLogger()
    patterns: list[str] = []

    if gitignore_path.exists():
        try:
            content = gitignore_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                clean_line = line.strip()
                if clean_line and not clean_line.startswith("#"):
                    patterns.append(clean_line)
        except OSError as e:
            logger.warning("Failed to read .gitignore: %s", e)

    return patterns


def resolve_gitignore(
    raw_config: dict[str, object] | None,
    *,
    args: argparse.Namespace,
) -> bool:
    """Determine whether to respect .gitignore patterns.

    Handles the following precedence (highest to lowest):
    1. CLI flag: --gitignore or --no-gitignore
    2. Config file: options.respect_gitignore
    3. Default: DEFAULT_RESPECT_GITIGNORE

    Args:
        raw_config: Raw configuration dict from config file (may be None)
        args: Parsed command-line arguments

    Returns:
        Boolean indicating whether to respect .gitignore patterns
    """
    logger = getAppLogger()

    # Case 1: CLI flag (highest priority)
    cli_flag: object = getattr(args, "respect_gitignore", None)
    if cli_flag is not None and isinstance(cli_flag, bool):
        logger.trace(
            "[resolve_gitignore] Using CLI flag: respect_gitignore=%s",
            cli_flag,
        )
        return cli_flag

    # Case 2: Config file (options.respect_gitignore)
    if raw_config:
        options: object = raw_config.get("options")
        if isinstance(options, dict):
            opts_dict = cast_hint(dict[str, object], options)
            respect_gitignore: object = opts_dict.get("respect_gitignore")
            if isinstance(respect_gitignore, bool):
                logger.trace(
                    "[resolve_gitignore] Using config: respect_gitignore=%s",
                    respect_gitignore,
                )
                return respect_gitignore

    # Case 3: Default
    logger.trace(
        "[resolve_gitignore] Using default: respect_gitignore=%s",
        DEFAULT_RESPECT_GITIGNORE,
    )
    return DEFAULT_RESPECT_GITIGNORE
