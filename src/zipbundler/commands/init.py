# src/zipbundler/commands/init.py

"""Handle the init subcommand."""

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from apathetic_utils import load_jsonc, load_toml

from zipbundler.constants import DEFAULT_USE_PYPROJECT_METADATA
from zipbundler.logs import getAppLogger
from zipbundler.meta import PROGRAM_CONFIG


# Default configuration template
DEFAULT_CONFIG_TEMPLATE = """{
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


def _extract_entry_point_from_pyproject(cwd: Path) -> str | None:  # noqa: PLR0911
    """Extract entry point from pyproject.toml if it exists.

    Looks for [project.scripts] section and extracts the first script's
    module:function format.

    Args:
        cwd: Current working directory to search for pyproject.toml

    Returns:
        Entry point string in format "module:function" or "module", or None
        if pyproject.toml not found or no scripts section
    """
    logger = getAppLogger()
    pyproject_path = cwd / "pyproject.toml"

    if not pyproject_path.exists():
        return None

    try:
        data = load_toml(pyproject_path)
        if not isinstance(data, dict):
            return None

        # Extract from [project.scripts] section (PEP 621)
        project: Any = data.get("project")  # pyright: ignore[reportUnknownVariableType]
        if not isinstance(project, dict):
            return None

        scripts: Any = project.get("scripts")  # pyright: ignore[reportUnknownVariableType,reportUnknownMemberType]
        if not isinstance(scripts, dict) or not scripts:
            return None

        # Take the first script entry
        first_script_value: Any = next(iter(scripts.values()))  # pyright: ignore[reportUnknownVariableType,reportUnknownArgumentType]
        if not isinstance(first_script_value, str):
            return None

        # Script format is "module:function" or "module"
        logger.debug(
            "Extracted entry_point from pyproject.toml: %s",
            first_script_value,
        )
        return first_script_value  # noqa: TRY300
    except Exception as e:  # noqa: BLE001
        logger.trace("Error extracting entry_point from pyproject.toml: %s", e)
        return None


def _extract_metadata_from_pyproject(cwd: Path) -> dict[str, str] | None:  # noqa: C901, PLR0912
    """Extract metadata from pyproject.toml if it exists.

    Args:
        cwd: Current working directory to search for pyproject.toml

    Returns:
        Dictionary with metadata fields (display_name, description, version,
        author, license), or None if pyproject.toml not found or no metadata
    """
    logger = getAppLogger()
    pyproject_path = cwd / "pyproject.toml"

    if not pyproject_path.exists():
        return None

    try:
        data = load_toml(pyproject_path)
        if not isinstance(data, dict):
            return None

        metadata: dict[str, str] = {}

        # Extract from [project] section (PEP 621)
        project = data.get("project")
        if isinstance(project, dict):
            # Name -> display_name
            if "name" in project:
                name_val: Any = project["name"]  # pyright: ignore[reportUnknownVariableType]
                if isinstance(name_val, str):
                    metadata["display_name"] = name_val

            # Version
            if "version" in project:
                version_val: Any = project["version"]  # pyright: ignore[reportUnknownVariableType]
                if isinstance(version_val, str):
                    metadata["version"] = version_val

            # Description
            if "description" in project:
                desc_val: Any = project["description"]  # pyright: ignore[reportUnknownVariableType]
                if isinstance(desc_val, str):
                    metadata["description"] = desc_val

            # Authors (take first author's name)
            if "authors" in project:
                authors_val: Any = project["authors"]  # pyright: ignore[reportUnknownVariableType]
                if isinstance(authors_val, list) and len(authors_val) > 0:  # pyright: ignore[reportUnknownArgumentType]
                    first_author: Any = authors_val[0]  # pyright: ignore[reportUnknownVariableType]
                    if isinstance(first_author, dict) and "name" in first_author:
                        author_name: Any = first_author["name"]  # pyright: ignore[reportUnknownVariableType]
                        if isinstance(author_name, str):
                            metadata["author"] = author_name
                    elif isinstance(first_author, str):
                        metadata["author"] = first_author

            # License
            if "license" in project:
                license_val: Any = project["license"]  # pyright: ignore[reportUnknownVariableType]
                if isinstance(license_val, dict) and "text" in license_val:
                    license_text: Any = license_val["text"]  # pyright: ignore[reportUnknownVariableType]
                    if isinstance(license_text, str):
                        metadata["license"] = license_text
                elif isinstance(license_val, str):
                    metadata["license"] = license_val

        if metadata:
            logger.debug(
                "Extracted metadata from pyproject.toml: %s", list(metadata.keys())
            )
            return metadata
        return None  # noqa: TRY300
    except Exception as e:  # noqa: BLE001
        logger.trace("Error extracting metadata from pyproject.toml: %s", e)
        return None


def _inject_entry_point_into_config(config_content: str, entry_point: str) -> str:
    """Inject entry_point into config content.

    Replaces commented entry_point or existing entry_point with
    actual entry_point from pyproject.toml.

    Args:
        config_content: Original config content (JSONC string)
        entry_point: Entry point string to inject

    Returns:
        Config content with entry_point injected
    """
    # Use a temporary file to leverage load_jsonc which handles JSONC comments
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonc", delete=False
        ) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_file.write(config_content)
            tmp_file.flush()

        # Load the JSONC config
        config_dict = load_jsonc(tmp_path)
        tmp_path.unlink()  # Clean up temp file

        if not isinstance(config_dict, dict):
            return config_content

        # Inject entry_point
        config_dict["entry_point"] = entry_point

        # Convert back to JSON with indentation
        # Note: This loses comments, but preserves structure and is cleaner
        formatted = json.dumps(config_dict, indent=2)

        # Add trailing newline to match original format
        return formatted + "\n"
    except Exception:  # noqa: BLE001
        # Fallback: simple string replacement for commented entry_point
        lines = config_content.splitlines()
        result_lines: list[str] = []
        in_entry_point_comment = False
        entry_point_indent = 0
        entry_point_inserted = False
        entry_point_escaped = json.dumps(entry_point)

        for line in lines:
            stripped = line.lstrip()

            # Check if this is the start of commented entry_point
            if (
                stripped.startswith(('// "entry_point":', '//"entry_point":'))
                and not in_entry_point_comment
                and not entry_point_inserted
            ):
                in_entry_point_comment = True
                entry_point_indent = len(line) - len(stripped)
                # Add actual entry_point
                result_lines.append(
                    " " * entry_point_indent + f'"entry_point": {entry_point_escaped},'
                )
                entry_point_inserted = True
                continue

            # Skip commented entry_point lines
            if in_entry_point_comment:
                # Check if we've reached the end of the commented line
                if stripped and not stripped.startswith("//"):
                    in_entry_point_comment = False
                    result_lines.append(line)
                continue

            result_lines.append(line)

        # If no commented entry_point found and not inserted,
        # append before last closing brace
        if (
            not entry_point_inserted
            and result_lines
            and result_lines[-1].strip() == "}"
        ):
            # Find indent of last line
            last_line = result_lines[-1]
            indent = len(last_line) - len(last_line.lstrip())
            # Insert entry_point before last closing brace
            entry_point_line = f'"entry_point": {entry_point_escaped},'
            result_lines.insert(-1, " " * indent + entry_point_line)

        return "\n".join(result_lines) + "\n"


def _inject_metadata_into_config(config_content: str, metadata: dict[str, str]) -> str:  # noqa: PLR0912
    """Inject metadata into config content.

    Replaces commented metadata section or existing metadata section with
    actual metadata from pyproject.toml.

    Args:
        config_content: Original config content (JSONC string)
        metadata: Metadata dictionary to inject

    Returns:
        Config content with metadata injected
    """
    # Use a temporary file to leverage load_jsonc which handles JSONC comments
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonc", delete=False
        ) as tmp_file:
            tmp_path = Path(tmp_file.name)
            tmp_file.write(config_content)
            tmp_file.flush()

        # Load the JSONC config
        config_dict = load_jsonc(tmp_path)
        tmp_path.unlink()  # Clean up temp file

        if not isinstance(config_dict, dict):
            return config_content

        # Inject metadata
        config_dict["metadata"] = metadata

        # Convert back to JSON with indentation
        # Note: This loses comments, but preserves structure and is cleaner
        formatted = json.dumps(config_dict, indent=2)

        # Add trailing newline to match original format
        return formatted + "\n"
    except Exception:  # noqa: BLE001
        # Fallback: simple string replacement for commented metadata
        lines = config_content.splitlines()
        result_lines: list[str] = []
        in_metadata_comment = False
        metadata_indent = 0
        metadata_inserted = False

        for line in lines:
            stripped = line.lstrip()

            # Check if this is the start of commented metadata
            if (
                stripped.startswith(('// "metadata":', '// "metadata":'))
                and not in_metadata_comment
                and not metadata_inserted
            ):
                in_metadata_comment = True
                metadata_indent = len(line) - len(stripped)
                # Add actual metadata
                result_lines.append(" " * metadata_indent + '"metadata": {')
                metadata_lines: list[str] = []
                for key, value in metadata.items():
                    # Escape value for JSON
                    value_escaped = json.dumps(value)
                    metadata_lines.append(  # pyright: ignore[reportUnknownMemberType]
                        " " * (metadata_indent + 2) + f'"{key}": {value_escaped},'
                    )
                # Remove trailing comma from last line
                if metadata_lines:
                    metadata_lines[-1] = metadata_lines[-1].rstrip(",")  # pyright: ignore[reportUnknownMemberType]
                result_lines.extend(metadata_lines)  # pyright: ignore[reportUnknownArgumentType]
                result_lines.append(" " * metadata_indent + "}")
                metadata_inserted = True
                continue

            # Skip commented metadata lines
            if in_metadata_comment:
                # Check if we've reached the end of the commented block
                if stripped.startswith(("// }", "//}")):
                    in_metadata_comment = False
                elif stripped and not stripped.startswith("//"):
                    in_metadata_comment = False
                    result_lines.append(line)
                continue

            result_lines.append(line)

        # If no commented metadata found and not inserted,
        # append before last closing brace
        if not metadata_inserted and result_lines and result_lines[-1].strip() == "}":
            # Find indent of last line
            last_line = result_lines[-1]
            indent = len(last_line) - len(last_line.lstrip())
            # Insert metadata before last closing brace
            metadata_lines = ['"metadata": {']
            for key, value in metadata.items():
                value_escaped = json.dumps(value)
                metadata_lines.append(" " * 2 + f'"{key}": {value_escaped},')
            if metadata_lines:
                metadata_lines[-1] = metadata_lines[-1].rstrip(",")
            metadata_lines.append("}")
            # Insert with proper indentation
            for meta_line in reversed(metadata_lines):
                result_lines.insert(-1, " " * indent + meta_line)

        return "\n".join(result_lines) + "\n"


def handle_init_command(args: argparse.Namespace) -> int:
    """Handle the init subcommand."""
    logger = getAppLogger()

    # Use default config template
    config_content = DEFAULT_CONFIG_TEMPLATE

    config_path = Path(args.config or f".{PROGRAM_CONFIG}.jsonc")

    if config_path.exists() and not args.force:
        logger.error(
            "Configuration file already exists: %s\nUse --force to overwrite.",
            config_path,
        )
        return 1

    # Try to auto-detect metadata and entry_point from pyproject.toml
    # (controlled by DEFAULT_USE_PYPROJECT_METADATA)
    cwd = Path.cwd().resolve()
    metadata = (
        _extract_metadata_from_pyproject(cwd)
        if DEFAULT_USE_PYPROJECT_METADATA
        else None
    )
    if metadata:
        logger.debug(
            "Auto-detected metadata from pyproject.toml, injecting into config"
        )
        config_content = _inject_metadata_into_config(config_content, metadata)

    entry_point = _extract_entry_point_from_pyproject(cwd)
    if entry_point:
        logger.debug(
            "Auto-detected entry_point from pyproject.toml, injecting into config"
        )
        config_content = _inject_entry_point_into_config(config_content, entry_point)

    # Write config file
    result = 0
    try:
        config_path.write_text(config_content, encoding="utf-8")
        logger.info("Created configuration file: %s", config_path)
    except OSError:
        logger.exception("Failed to create configuration file")
        result = 1
    except Exception as e:  # noqa: BLE001
        logger.criticalIfNotDebug("Unexpected error: %s", e)
        result = 1

    return result
