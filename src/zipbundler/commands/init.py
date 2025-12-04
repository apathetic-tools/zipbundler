# src/zipbundler/commands/init.py

"""Handle the init subcommand."""

import argparse
from pathlib import Path

from zipbundler.logs import getAppLogger


# Preset templates for common project structures
PRESETS: dict[str, dict[str, str]] = {
    "basic": {
        "name": "Basic",
        "description": "Standard configuration for a typical Python package",
        "content": """{
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
""",
    },
    "cli": {
        "name": "CLI Tool",
        "description": "Configuration for a command-line application with entry point",
        "content": """{
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
    "path": "dist/my_package.pyz"
  },

  // Entry point for executable zip
  "entry_point": "my_package.__main__:main",

  // Control code generation
  "options": {
    "shebang": "/usr/bin/env python3",
    "main_guard": true,
    "compression": "deflate"
  },

  // Metadata
  "metadata": {
    "display_name": "My CLI Tool",
    "description": "A command-line application",
    "version": "1.0.0"
  }
}
""",
    },
    "library": {
        "name": "Library",
        "description": "Configuration for an importable library (no entry point)",
        "content": """{
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

  // No entry point - this is an importable library

  // Control code generation
  "options": {
    "shebang": false,
    "main_guard": false,
    "compression": "deflate"
  },

  // Metadata
  "metadata": {
    "display_name": "My Library",
    "description": "An importable Python library",
    "version": "1.0.0"
  }
}
""",
    },
    "minimal": {
        "name": "Minimal",
        "description": "Minimal configuration with just the essentials",
        "content": """{
  // Packages to include (glob patterns or package names)
  "packages": [
    "src/my_package/**/*.py"
  ],

  // Output configuration
  "output": {
    "path": "dist/my_package.zip"
  }
}
""",
    },
}


def get_preset_names() -> list[str]:
    """Get list of available preset names."""
    return sorted(PRESETS.keys())


def get_preset_content(preset_name: str) -> str | None:
    """Get config content for a preset.

    Args:
        preset_name: Name of the preset

    Returns:
        Config content string, or None if preset not found
    """
    preset = PRESETS.get(preset_name)
    if preset:
        return preset["content"]
    return None


def list_presets() -> str:
    """Get formatted list of available presets."""
    lines: list[str] = []
    lines.append("Available presets:")
    lines.append("")
    for preset_name in get_preset_names():
        preset = PRESETS[preset_name]
        lines.append(f"  {preset_name}")
        lines.append(f"    {preset['name']}: {preset['description']}")
        lines.append("")
    return "\n".join(lines)


def handle_init_command(args: argparse.Namespace) -> int:
    """Handle the init subcommand."""
    logger = getAppLogger()

    # Handle --list-presets flag
    if getattr(args, "list_presets", False):
        logger.info(list_presets())
        return 0

    # Determine which preset to use
    preset_name = getattr(args, "preset", None) or "basic"
    config_content = get_preset_content(preset_name)

    if config_content is None:
        available = ", ".join(get_preset_names())
        logger.error(
            "Unknown preset: %s\nAvailable presets: %s",
            preset_name,
            available,
        )
        return 1

    config_path = Path(args.output or ".zipbundler.jsonc")

    if config_path.exists() and not args.force:
        logger.error(
            "Configuration file already exists: %s\nUse --force to overwrite.",
            config_path,
        )
        return 1

    # Write config file
    result = 0
    try:
        config_path.write_text(config_content, encoding="utf-8")
        if preset_name != "basic":
            logger.info(
                "Created configuration file: %s (using '%s' preset)",
                config_path,
                preset_name,
            )
        else:
            logger.info("Created configuration file: %s", config_path)
    except OSError:
        logger.exception("Failed to create configuration file")
        result = 1
    except Exception as e:  # noqa: BLE001
        logger.criticalIfNotDebug("Unexpected error: %s", e)
        result = 1

    return result
