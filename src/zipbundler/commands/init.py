# src/zipbundler/commands/init.py

"""Handle the init subcommand."""

import argparse
from pathlib import Path

from zipbundler.logs import getAppLogger


def _get_default_config_content() -> str:
    """Generate default .zipbundler.jsonc config file content."""
    return """{
  // Packages to include (glob patterns or package names)
  "packages": [
    "src/my_package/**/*.py"
  ],

  // Files/directories to exclude (glob patterns)
  "exclude": [
    "**/__pycache__/**",
    "**/*.pyc",
    "**/*.pyo",
    "**/tests/**",
    "**/.git/**"
  ],

  // Output configuration
  "output": {
    "path": "dist/my_package.zip"
  },

  // Entry point for executable zip (optional)
  // "entry_point": "my_package.__main__:main",

  // Control code generation
  "options": {
    "shebang": "/usr/bin/env python3",
    "main_guard": true,
    "compression": "deflate"
  },

  // Metadata (optional)
  // "metadata": {
  //   "display_name": "My Package",
  //   "description": "Package description",
  //   "version": "1.0.0"
  // }
}
"""


def handle_init_command(args: argparse.Namespace) -> int:
    """Handle the init subcommand."""
    logger = getAppLogger()

    config_path = Path(args.output or ".zipbundler.jsonc")

    if config_path.exists() and not args.force:
        logger.error(
            "Configuration file already exists: %s\nUse --force to overwrite.",
            config_path,
        )
        return 1

    try:
        config_content = _get_default_config_content()
        config_path.write_text(config_content, encoding="utf-8")
        logger.info("Created configuration file: %s", config_path)
    except OSError:
        logger.exception("Failed to create configuration file")
        return 1
    except Exception as e:  # noqa: BLE001
        logger.criticalIfNotDebug("Unexpected error: %s", e)
        return 1
    else:
        return 0
