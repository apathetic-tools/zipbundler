# src/zipbundler/commands/validate.py

"""Handle the validate subcommand."""

import argparse
from pathlib import Path
from typing import Any

from zipbundler.config import load_and_validate_config
from zipbundler.logs import getAppLogger


def resolve_output_path_from_config(
    output_config: dict[str, Any] | None,
    default_directory: str = "dist",
    default_name: str = "bundle",
) -> Path:
    """Resolve output path from config output section.

    Handles:
    - output.path: Full path (takes precedence)
    - output.directory + output.name: Directory and filename
    - output.name: Filename only (uses default_directory)
    - None: Uses default_directory and default_name

    Args:
        output_config: Output configuration dict with optional 'path', 'directory',
            'name'
        default_directory: Default directory if not specified (default: "dist")
        default_name: Default filename (without extension) if not specified
            (default: "bundle")

    Returns:
        Resolved Path object
    """
    if not output_config:
        return Path(f"{default_directory}/{default_name}.pyz")

    output_path_str: str | None = output_config.get("path")
    if output_path_str:
        return Path(output_path_str)

    output_directory: str | None = output_config.get("directory")
    output_name: str | None = output_config.get("name")

    # Use directory from config or default, name from config or default
    directory = output_directory if output_directory is not None else default_directory
    name = output_name if output_name is not None else default_name

    return Path(f"{directory}/{name}.pyz")


def handle_validate_command(args: argparse.Namespace) -> int:
    """Handle the validate subcommand."""
    logger = getAppLogger()

    cwd = Path.cwd().resolve()
    config_path_str = getattr(args, "config", None)
    strict = getattr(args, "strict", False)

    try:
        result = load_and_validate_config(
            config_path=config_path_str,
            cwd=cwd,
            strict=strict,
        )

        if result is None:
            msg = (
                "No configuration file found. "
                "Looking for .zipbundler.py, .zipbundler.jsonc, or pyproject.toml"
            )
            logger.error(msg)
            return 1

        # Validation summary is already logged by load_and_validate_config
        # Just check if valid
        _config_path, _root_cfg, validation = result

        if validation.valid:
            return 0
        return 1  # noqa: TRY300

    except (FileNotFoundError, ValueError, TypeError, RuntimeError) as e:
        logger.errorIfNotDebug(str(e))
        return 1
    except Exception as e:  # noqa: BLE001
        logger.criticalIfNotDebug("Unexpected error: %s", e)
        return 1
