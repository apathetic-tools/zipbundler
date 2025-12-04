# src/zipbundler/config/config_loader.py

"""Configuration loading and parsing for zipbundler."""

import sys
import traceback
from pathlib import Path
from typing import Any, cast

from apathetic_schema.types import (
    ApatheticSchema_ValidationSummary as ValidationSummary,
)
from apathetic_utils import cast_hint, load_jsonc, load_toml, plural

from zipbundler.logs import getAppLogger

from .config_types import RootConfig
from .config_validate import validate_config


def find_config(
    config_path: str | None,
    cwd: Path,
    *,
    missing_level: str = "error",
) -> Path | None:
    """Find configuration file.

    Search order:
      1. Explicit path from CLI (--config)
      2. Default candidate files in current directory and parent directories:
         - .zipbundler.py
         - .zipbundler.jsonc
         - pyproject.toml
         Searches from cwd up to filesystem root, returning first match
         (closest to cwd).
         Priority: .py > .jsonc > .toml

    Args:
        config_path: Explicit config path from CLI
        cwd: Current working directory
        missing_level: Log level for missing config ("error" or "warning")

    Returns:
        The first matching path, or None if no config was found.
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

    # --- 2. Default candidate files (search current dir and parents) ---
    # Search from cwd up to filesystem root, returning first match (closest to cwd)
    current = cwd
    candidate_names = [
        ".zipbundler.py",
        ".zipbundler.jsonc",
        "pyproject.toml",
    ]
    found: list[Path] = []
    while True:
        for name in candidate_names:
            candidate = current / name
            if candidate.exists():
                found.append(candidate)
        if found:
            # Found at least one config file at this level
            break
        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent

    if not found:
        logger.logDynamic(missing_level, f"No config file found in {cwd} or parents")
        return None

    # --- 3. Handle multiple matches at same level ---
    # Prefer .zipbundler.py > .zipbundler.jsonc > pyproject.toml
    if len(found) > 1:
        # Prefer .py, then .jsonc, then .toml
        priority = {".zipbundler.py": 0, ".zipbundler.jsonc": 1, "pyproject.toml": 2}
        found_sorted = sorted(found, key=lambda p: priority.get(p.name, 99))
        names = ", ".join(p.name for p in found_sorted)
        logger.warning(
            "Multiple config files detected (%s); using %s.",
            names,
            found_sorted[0].name,
        )
        return found_sorted[0]
    logger.trace(f"[find_config] Found config: {found[0]}")
    return found[0]


def _load_jsonc_config(config_path: Path) -> dict[str, Any]:
    """Load JSONC configuration file."""
    logger = getAppLogger()
    logger.trace(f"[load_config] Loading JSONC from {config_path}")

    try:
        config = load_jsonc(config_path)
        if not isinstance(config, dict):
            msg = f"Config file must contain a JSON object, got {type(config).__name__}"
            raise TypeError(msg)  # noqa: TRY301
        return config  # noqa: TRY300
    except (ValueError, TypeError) as e:
        msg = f"Error loading config file '{config_path.name}': {e}"
        raise ValueError(msg) from e


def _load_python_config(config_path: Path) -> dict[str, Any]:
    """Load Python configuration file (.zipbundler.py)."""
    logger = getAppLogger()
    logger.trace(f"[load_config] Loading Python config from {config_path}")

    config_globals: dict[str, Any] = {}

    # Allow local imports in Python configs (e.g. from ./helpers import foo)
    # This is safe because configs are trusted user code.
    parent_dir = str(config_path.parent)
    added_to_sys_path = parent_dir not in sys.path
    if added_to_sys_path:
        sys.path.insert(0, parent_dir)

    # Execute the python config file
    try:
        source = config_path.read_text(encoding="utf-8")
        exec(compile(source, str(config_path), "exec"), config_globals)  # noqa: S102
        logger.trace(
            f"[EXEC] globals after exec: {list(config_globals.keys())}",
        )
    except Exception as e:
        tb = traceback.format_exc()
        xmsg = (
            f"Error while executing Python config: {config_path.name}\n"
            f"{type(e).__name__}: {e}\n{tb}"
        )
        # Raise a generic runtime error for main() to catch and print cleanly
        raise RuntimeError(xmsg) from e
    finally:
        # Only remove if we actually inserted it
        if added_to_sys_path and sys.path[0] == parent_dir:
            sys.path.pop(0)

    # Check for config variable
    if "config" in config_globals:
        result = config_globals["config"]
        if not isinstance(result, (dict, type(None))):
            xmsg = (
                f"config in {config_path.name} must be a dict or None"
                f", not {type(result).__name__}"
            )
            raise TypeError(xmsg)
        if result is None:
            xmsg = f"config in {config_path.name} is None (empty config)"
            raise ValueError(xmsg)
        # Explicitly narrow the loaded config to its expected type.
        return cast("dict[str, Any]", result)

    xmsg = f"{config_path.name} did not define `config`"
    raise ValueError(xmsg)


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
        return tool_config  # noqa: TRY300
    except (ValueError, TypeError, OSError) as e:
        msg = f"Error loading TOML config from '{config_path.name}': {e}"
        raise ValueError(msg) from e


def load_config(config_path: Path) -> dict[str, Any] | None:
    """Load configuration from file.

    Supports:
      - Python configs: .py files exporting `config`
      - JSON/JSONC configs: .jsonc files
      - TOML configs: pyproject.toml with [tool.zipbundler] section

    Returns:
        The raw config dict, or None for intentionally empty configs.

    Raises:
        ValueError: If config file is invalid or cannot be loaded
        RuntimeError: If Python config execution fails
    """
    if config_path.suffix == ".py" or config_path.name == ".zipbundler.py":
        return _load_python_config(config_path)
    if config_path.suffix == ".jsonc" or config_path.name == ".zipbundler.jsonc":
        return _load_jsonc_config(config_path)
    if config_path.suffix == ".toml" or config_path.name == "pyproject.toml":
        return _load_toml_config(config_path)
    # Try JSONC as fallback
    return _load_jsonc_config(config_path)


def parse_config(
    raw_config: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Normalize user config into canonical RootConfig shape (no filesystem work).

    Accepted forms:
      - None / {}                → None (empty config)
      - {...}                    → flat config (all fields at root level)

    After normalization:
      - Returns flat dict with all fields at root level, or None for empty config.
      - Preserves all unknown keys for later validation.

    Args:
        raw_config: Raw config dict from file

    Returns:
        Normalized config dict or None for empty config
    """
    logger = getAppLogger()
    logger.trace(f"[parse_config] Parsing {type(raw_config).__name__}")

    # --- Case 1: empty config → None ---
    if not raw_config or raw_config == {}:  # handles None, {}
        return None

    # --- Case 2: dict config (already flat) ---
    if not isinstance(raw_config, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
        xmsg = (
            f"Invalid top-level value: {type(raw_config).__name__} (expected object)",
        )
        raise TypeError(xmsg)

    # --- Flat config: all fields at root level ---
    return dict(raw_config)


def _validation_summary(
    summary: ValidationSummary,
    config_path: Path,
) -> None:
    """Pretty-print a validation summary using the standard log() interface."""
    logger = getAppLogger()
    mode = "strict mode" if summary.strict else "lenient mode"

    # --- Build concise counts line ---
    counts: list[str] = []
    if summary.errors:
        counts.append(f"{len(summary.errors)} error{plural(summary.errors)}")
    if summary.strict_warnings:
        counts.append(
            f"{len(summary.strict_warnings)} strict warning"
            f"{plural(summary.strict_warnings)}",
        )
    if summary.warnings:
        counts.append(
            f"{len(summary.warnings)} normal warning{plural(summary.warnings)}",
        )
    counts_msg = f"\nFound {', '.join(counts)}." if counts else ""

    # --- Header (single icon) ---
    if not summary.valid:
        logger.error(
            "Failed to validate configuration file %s (%s).%s",
            config_path.name,
            mode,
            counts_msg,
        )
    elif counts:
        logger.warning(
            "Validated configuration file  %s (%s) with warnings.%s",
            config_path.name,
            mode,
            counts_msg,
        )
    else:
        logger.debug("Validated  %s (%s) successfully.", config_path.name, mode)

    # --- Detailed sections ---
    if summary.errors:
        msg_summary = "\n  • ".join(summary.errors)
        logger.error("\nErrors:\n  • %s", msg_summary)
    if summary.strict_warnings:
        msg_summary = "\n  • ".join(summary.strict_warnings)
        logger.error("\nStrict warnings (treated as errors):\n  • %s", msg_summary)
    if summary.warnings:
        msg_summary = "\n  • ".join(summary.warnings)
        logger.warning("\nWarnings (non-fatal):\n  • %s", msg_summary)


def load_and_validate_config(
    config_path: str | Path | None = None,
    *,
    cwd: Path | None = None,
    strict: bool | None = None,
) -> tuple[Path, RootConfig, ValidationSummary] | None:
    """Find, load, parse, and validate the user's configuration.

    Args:
        config_path: Explicit config path (searches for default if None)
        cwd: Current working directory (default: current dir)
        strict: Override strict mode (None uses default)

    Returns:
        (config_path, root_cfg, validation_summary) if config found and valid,
        or None if no config was found.

    Raises:
        FileNotFoundError: If explicit config path not found
        ValueError: If config is invalid (with validation details)
        TypeError: If config cannot be parsed
        RuntimeError: If Python config execution fails
    """
    if cwd is None:
        cwd = Path.cwd().resolve()

    # --- Find config file ---
    missing_level = "warning"  # Allow configless operation
    found_config_path = find_config(
        str(config_path) if config_path else None,
        cwd,
        missing_level=missing_level,
    )
    if found_config_path is None:
        return None

    # --- Load the raw config ---
    raw_config = load_config(found_config_path)
    if raw_config is None:
        return None

    # --- Parse structure into final form without types ---
    try:
        parsed_cfg = parse_config(raw_config)
    except TypeError as e:
        xmsg = f"Could not parse config {found_config_path.name}: {e}"
        raise TypeError(xmsg) from e
    if parsed_cfg is None:
        return None

    # --- Validate schema ---
    validation_result = validate_config(parsed_cfg, strict=strict, cwd=cwd)
    if not validation_result.valid:
        # Build comprehensive error message with all details
        mode = "strict mode" if validation_result.strict else "lenient mode"
        counts: list[str] = []
        if validation_result.errors:
            error_count = len(validation_result.errors)
            counts.append(f"{error_count} error{plural(validation_result.errors)}")
        if validation_result.strict_warnings:
            warning_count = len(validation_result.strict_warnings)
            counts.append(
                f"{warning_count} strict warning"
                f"{plural(validation_result.strict_warnings)}"
            )
        counts_msg = f"\nFound {', '.join(counts)}." if counts else ""

        # Build detailed error message with newlines
        error_parts: list[str] = []
        error_parts.append(
            f"Failed to validate configuration file {found_config_path.name} "
            f"({mode}).{counts_msg}"
        )

        if validation_result.errors:
            msg_summary = "\n  • ".join(validation_result.errors)
            error_parts.append(f"\nErrors:\n  • {msg_summary}")

        if validation_result.strict_warnings:
            msg_summary = "\n  • ".join(validation_result.strict_warnings)
            error_parts.append(
                f"\nStrict warnings (treated as errors):\n  • {msg_summary}"
            )

        xmsg = "".join(error_parts)
        exception = ValueError(xmsg)
        exception.data = validation_result  # type: ignore[attr-defined]
        raise exception

    # Log validation summary (only if valid or has warnings)
    _validation_summary(validation_result, found_config_path)

    # --- Upgrade to RootConfig type ---
    root_cfg: RootConfig = cast_hint(RootConfig, parsed_cfg)
    return found_config_path, root_cfg, validation_result
