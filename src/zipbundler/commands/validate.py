# src/zipbundler/commands/validate.py
# ruff: noqa: TRY300

"""Handle the validate subcommand."""

import argparse
import re
from pathlib import Path
from typing import Any

from apathetic_utils import load_jsonc, load_toml

from zipbundler.logs import getAppLogger


def find_config(config_path: str | None, cwd: Path) -> Path | None:
    """Find configuration file.

    Search order:
      1. Explicit path from CLI (--config)
      2. .zipbundler.jsonc in current directory
      3. pyproject.toml in current directory

    Returns the first matching path, or None if no config was found.
    """
    logger = getAppLogger()

    # --- 1. Explicit config path ---
    if config_path:
        config = Path(config_path).expanduser().resolve()
        logger.trace(f"[find_config] Checking explicit path: {config}")
        if not config.exists():
            msg = f"Specified config file not found: {config}"
            raise FileNotFoundError(msg)
        if config.is_dir():
            msg = f"Specified config path is a directory, not a file: {config}"
            raise ValueError(msg)
        return config

    # --- 2. Default candidate files ---
    candidates = [
        cwd / ".zipbundler.jsonc",
        cwd / "pyproject.toml",
    ]

    for candidate in candidates:
        if candidate.exists():
            logger.trace(f"[find_config] Found config: {candidate}")
            return candidate

    return None


def _load_jsonc_config(config_path: Path) -> dict[str, Any]:
    """Load JSONC configuration file."""
    logger = getAppLogger()
    logger.trace(f"[load_config] Loading JSONC from {config_path}")

    try:
        config = load_jsonc(config_path)
        if not isinstance(config, dict):
            msg = f"Config file must contain a JSON object, got {type(config).__name__}"
            raise TypeError(msg)  # noqa: TRY301
        return config
    except (ValueError, TypeError) as e:
        msg = f"Error loading config file '{config_path.name}': {e}"
        raise ValueError(msg) from e


def _load_toml_config(config_path: Path) -> dict[str, Any]:
    """Load TOML configuration file (from pyproject.toml)."""
    logger = getAppLogger()
    logger.trace(f"[load_config] Loading TOML from {config_path}")

    try:
        data = load_toml(config_path)
        if not isinstance(data, dict):
            msg = f"Config file must contain a TOML object, got {type(data).__name__}"
            raise TypeError(msg)  # noqa: TRY301
        tool_config: dict[str, Any] = data.get("tool", {}).get("zipbundler", {})
        if not tool_config:
            msg = "No [tool.zipbundler] section found in pyproject.toml"
            raise ValueError(msg)  # noqa: TRY301
        return tool_config
    except (ValueError, TypeError, OSError) as e:
        msg = f"Error loading TOML config from '{config_path.name}': {e}"
        raise ValueError(msg) from e


def load_config(config_path: Path) -> dict[str, Any]:
    """Load configuration from file."""
    if config_path.suffix == ".jsonc" or config_path.name == ".zipbundler.jsonc":
        return _load_jsonc_config(config_path)
    if config_path.suffix == ".toml" or config_path.name == "pyproject.toml":
        return _load_toml_config(config_path)
    # Try JSONC as fallback
    return _load_jsonc_config(config_path)


def _validate_entry_point(entry_point: str) -> tuple[bool, str]:
    """Validate entry point format.

    Format: module.path:function_name or module.path

    Returns:
        (is_valid, error_message)
    """
    if not isinstance(entry_point, str):  # pyright: ignore[reportUnnecessaryIsInstance]
        msg = f"Entry point must be a string, got {type(entry_point).__name__}"
        return False, msg

    # Entry point format: module.path:function or module.path
    # Module path should be valid Python identifier segments separated by dots
    # Function name should be a valid Python identifier
    pattern = (
        r"^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*"
        r"(?::[a-zA-Z_][a-zA-Z0-9_]*)?$"
    )
    if not re.match(pattern, entry_point):
        msg = (
            f"Invalid entry point format: '{entry_point}'. "
            "Expected format: 'module.path:function' or 'module.path'"
        )
        return False, msg

    return True, ""


def _validate_output_path(output_path: str, cwd: Path) -> tuple[bool, str]:
    """Validate output path accessibility.

    Returns:
        (is_valid, error_message)
    """
    try:
        path = Path(output_path)
        if not path.is_absolute():
            path = cwd / path

        # Check if parent directory is writable (or can be created)
        parent = path.parent
        if not parent.exists():
            # Try to create parent directory to check if it's possible
            try:
                parent.mkdir(parents=True, exist_ok=True)
                # Clean up if we created it
                if not any(parent.iterdir()):
                    parent.rmdir()
            except OSError as e:
                msg = f"Cannot create output directory '{parent}': {e}"
                return False, msg

        # Check if parent is writable
        if parent.exists() and not parent.is_dir():
            msg = f"Output path parent is not a directory: {parent}"
            return False, msg
        return True, ""
    except (OSError, ValueError) as e:
        msg = f"Error validating output path: {e}"
        return False, msg


def _validate_packages_field(
    config: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    """Validate packages field."""
    if "packages" not in config:
        errors.append("Missing required field: 'packages'")
        return

    if not isinstance(config["packages"], list):
        errors.append("Field 'packages' must be a list")
        return

    packages_list: list[Any] = config["packages"]  # pyright: ignore[reportUnknownVariableType]
    if len(packages_list) == 0:
        warnings.append("Field 'packages' is empty (no packages will be included)")
        return

    # Validate each package entry
    for i, pkg in enumerate(packages_list):  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
        if not isinstance(pkg, str):  # pyright: ignore[reportUnknownArgumentType]
            msg = f"packages[{i}] must be a string, got {type(pkg).__name__}"
            errors.append(msg)


def _validate_exclude_field(
    config: dict[str, Any],
    errors: list[str],
) -> None:
    """Validate exclude field."""
    if "exclude" not in config:
        return

    if not isinstance(config["exclude"], list):
        errors.append("Field 'exclude' must be a list")
        return

    exclude_list: list[Any] = config["exclude"]  # pyright: ignore[reportUnknownVariableType]
    for i, excl in enumerate(exclude_list):  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
        if not isinstance(excl, str):  # pyright: ignore[reportUnknownArgumentType]
            msg = f"exclude[{i}] must be a string, got {type(excl).__name__}"
            errors.append(msg)


def _validate_output_field(
    config: dict[str, Any],
    cwd: Path,
    *,
    strict: bool,
    errors: list[str],
    warnings: list[str],
) -> None:
    """Validate output field."""
    if "output" not in config:
        return

    output = config["output"]
    if not isinstance(output, dict):
        errors.append("Field 'output' must be an object")
        return

    if "path" not in output:
        return

    output_path: Any = output["path"]  # pyright: ignore[reportUnknownVariableType]
    if not isinstance(output_path, str):
        errors.append("Field 'output.path' must be a string")
        return

    is_valid, error_msg = _validate_output_path(output_path, cwd)
    if not is_valid:
        if strict:
            errors.append(error_msg)
        else:
            warnings.append(error_msg)


def _validate_options_field(
    config: dict[str, Any],
    warnings: list[str],
) -> None:
    """Validate options field."""
    if "options" not in config:
        return

    options = config["options"]
    if not isinstance(options, dict):
        return

    # Validate compression method
    compression: Any = None
    if "compression" in options:
        compression = options["compression"]  # pyright: ignore[reportUnknownVariableType]
        valid_compression = {"deflate", "stored", "bzip2", "lzma"}
        if compression not in valid_compression:
            valid_str = ", ".join(sorted(valid_compression))
            msg = (
                f"Unknown compression method '{compression}'. "
                f"Valid options: {valid_str}"
            )
            warnings.append(msg)

    # Validate compression_level
    max_compression_level = 9
    if "compression_level" in options:
        compression_level: Any = options["compression_level"]  # pyright: ignore[reportUnknownVariableType]
        if not isinstance(compression_level, int):
            msg = "Field 'options.compression_level' must be an integer"
            warnings.append(msg)
        elif compression_level < 0 or compression_level > max_compression_level:
            msg = (
                f"Field 'options.compression_level' must be between 0 and "
                f"{max_compression_level}"
            )
            warnings.append(msg)
        elif compression is not None and compression != "deflate":
            msg = (
                "Field 'options.compression_level' is only valid when "
                f"'options.compression' is 'deflate' (got '{compression}')"
            )
            warnings.append(msg)


def validate_config_structure(
    config: dict[str, Any],
    cwd: Path,
    *,
    strict: bool,
) -> tuple[bool, list[str], list[str]]:
    """Validate configuration structure.

    Returns:
        (is_valid, errors, warnings)
    """
    errors: list[str] = []
    warnings: list[str] = []

    # --- Validate required fields ---
    _validate_packages_field(config, errors, warnings)

    # --- Validate exclude field ---
    _validate_exclude_field(config, errors)

    # --- Validate entry_point field ---
    if "entry_point" in config:
        entry_point = config["entry_point"]
        is_valid, error_msg = _validate_entry_point(entry_point)
        if not is_valid:
            errors.append(error_msg)

    # --- Validate output field ---
    _validate_output_field(config, cwd, strict=strict, errors=errors, warnings=warnings)

    # --- Validate options field ---
    _validate_options_field(config, warnings)

    # --- Determine validity ---
    is_valid = len(errors) == 0 and (not strict or len(warnings) == 0)

    return is_valid, errors, warnings


def handle_validate_command(args: argparse.Namespace) -> int:
    """Handle the validate subcommand."""
    logger = getAppLogger()

    cwd = Path.cwd().resolve()
    config_path = find_config(getattr(args, "config", None), cwd)

    if not config_path:
        msg = (
            "No configuration file found. "
            "Looking for .zipbundler.jsonc or pyproject.toml"
        )
        logger.error(msg)
        return 1

    try:
        logger.info("Validating configuration file: %s", config_path)
        config = load_config(config_path)

        strict = getattr(args, "strict", False)
        is_valid, errors, warnings = validate_config_structure(
            config, cwd, strict=strict
        )

        # --- Report errors ---
        if errors:
            logger.error("Validation failed with %d error(s):", len(errors))
            for error in errors:
                logger.error("  • %s", error)

        # --- Report warnings ---
        if warnings:
            if strict:
                msg = (
                    f"Validation failed with {len(warnings)} warning(s) (strict mode):"
                )
                logger.warning(msg)
            else:
                logger.warning("Validation found %d warning(s):", len(warnings))
            for warning in warnings:
                logger.warning("  • %s", warning)

        # --- Success message ---
        if is_valid:
            if warnings and not strict:
                logger.info("Configuration is valid (with warnings)")
            else:
                logger.info("Configuration is valid")
            return 0
        return 1

    except (FileNotFoundError, ValueError) as e:
        logger.errorIfNotDebug(str(e))
        return 1
    except Exception as e:  # noqa: BLE001
        logger.criticalIfNotDebug("Unexpected error: %s", e)
        return 1
