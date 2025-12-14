# src/zipbundler/config/config_validate.py

"""Configuration validation using apathetic-schema."""

import re
from pathlib import Path
from typing import Any

from apathetic_schema import (
    check_schema_conformance,
    collect_msg,
    flush_schema_aggregators,
)
from apathetic_schema.types import ApatheticSchema_ValidationSummary
from apathetic_schema.warn_keys_once import ApatheticSchema_SchemaErrorAggregator
from apathetic_utils import schema_from_typeddict

from zipbundler.constants import DEFAULT_STRICT_CONFIG
from zipbundler.logs import getAppLogger

from .config_types import RootConfig


ValidationSummary = ApatheticSchema_ValidationSummary
SchemaErrorAggregator = ApatheticSchema_SchemaErrorAggregator


# --- constants ------------------------------------------------------

MAX_COMPRESSION_LEVEL = 9

# Field-specific type examples for better error messages
FIELD_EXAMPLES: dict[str, str] = {
    "root.packages": '["src/my_package", "lib/utils"]',
    "root.exclude": '["**/__pycache__/**", "**/*.pyc"]',
    "root.entry_point": '"my_package.__main__:main"',
    "root.output.path": '"dist/bundle.pyz"',
    "root.output.directory": '"dist"',
    "root.output.name": '"bundle"',
    "root.options.shebang": 'true or "/usr/bin/env python3"',
    "root.options.main_guard": "true",
    "root.options.compression": '"deflate"',
    "root.options.compression_level": "9",
    "root.metadata.display_name": '"My Package"',
    "root.metadata.description": '"A description"',
    "root.metadata.version": '"1.0.0"',
}


# --- helper functions for custom validations ---


def _validate_entry_point_format(entry_point: str) -> tuple[bool, str]:
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


def _validate_output_path_accessibility(
    output_path: str,
    cwd: Path,
) -> tuple[bool, str]:
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
        return True, ""  # noqa: TRY300
    except (OSError, ValueError) as e:
        msg = f"Error validating output path: {e}"
        return False, msg


# ---------------------------------------------------------------------------
# main validator
# ---------------------------------------------------------------------------


def _set_valid_and_return(
    *,
    flush: bool = True,
    summary: ValidationSummary,  # could be modified
    agg: SchemaErrorAggregator,  # could be modified
) -> ValidationSummary:
    """Set valid flag and return summary."""
    if flush:
        flush_schema_aggregators(summary=summary, agg=agg)
    summary.valid = not summary.errors and not summary.strict_warnings
    return summary


def _validate_custom_rules(  # noqa: PLR0912
    parsed_cfg: dict[str, Any],
    *,
    cwd: Path,
    strict_config: bool,
    summary: ValidationSummary,  # modified
) -> None:
    """Apply custom validation rules beyond schema validation."""
    logger = getAppLogger()
    logger.trace("[validate_custom] Applying custom validation rules")

    # --- Validate entry_point format ---
    if "entry_point" in parsed_cfg:
        entry_point = parsed_cfg["entry_point"]
        is_valid, error_msg = _validate_entry_point_format(entry_point)
        if not is_valid:
            collect_msg(
                error_msg,
                strict=True,
                summary=summary,
                is_error=True,
            )

    # --- Validate output path accessibility ---
    output = parsed_cfg.get("output")
    if isinstance(output, dict) and "path" in output:  # pyright: ignore[reportUnnecessaryIsInstance]
        output_path: str = output["path"]  # pyright: ignore[reportUnknownVariableType]
        if isinstance(output_path, str):
            is_valid, error_msg = _validate_output_path_accessibility(output_path, cwd)
            if not is_valid:
                collect_msg(
                    error_msg,
                    strict=strict_config,
                    summary=summary,
                    is_error=strict_config,
                )

    # --- Validate compression options ---
    options = parsed_cfg.get("options")
    if isinstance(options, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
        # Validate shebang (empty string is invalid)
        shebang = options.get("shebang")  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        if isinstance(shebang, str) and not shebang.strip():
            collect_msg(
                "Field 'options.shebang' must be a non-empty string, boolean, or false",
                strict=True,
                summary=summary,
                is_error=True,
            )

        compression: str | None = options.get("compression")  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        compression_level: int | None = options.get("compression_level")  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]

        # Validate compression level range
        if compression_level is not None:
            if not isinstance(compression_level, int):
                collect_msg(
                    "Field 'options.compression_level' must be an integer",
                    strict=strict_config,
                    summary=summary,
                    is_error=False,
                )
            elif compression_level < 0 or compression_level > MAX_COMPRESSION_LEVEL:
                collect_msg(
                    f"Field 'options.compression_level' must be between 0 and "
                    f"{MAX_COMPRESSION_LEVEL} (got {compression_level})",
                    strict=strict_config,
                    summary=summary,
                    is_error=False,
                )
            elif compression is not None and compression != "deflate":
                collect_msg(
                    f"Field 'options.compression_level' is only valid when "
                    f"'options.compression' is 'deflate' (got '{compression}')",
                    strict=strict_config,
                    summary=summary,
                    is_error=False,
                )

        # Validate compression method
        valid_compression = {"deflate", "stored", "bzip2", "lzma"}
        if compression is not None and compression not in valid_compression:
            valid_str = ", ".join(sorted(valid_compression))
            collect_msg(
                f"Unknown compression method '{compression}'. "
                f"Valid options: {valid_str}",
                strict=strict_config,
                summary=summary,
                is_error=False,
            )

    # --- Validate empty packages warning ---
    packages = parsed_cfg.get("packages")
    if isinstance(packages, list) and len(packages) == 0:  # pyright: ignore[reportUnknownArgumentType]
        collect_msg(
            "Field 'packages' is empty (no packages will be included)",
            strict=strict_config,
            summary=summary,
            is_error=False,
        )


def _validate_root(
    parsed_cfg: dict[str, Any],
    *,
    strict_arg: bool | None,
    cwd: Path,
    summary: ValidationSummary,  # modified
    _agg: SchemaErrorAggregator,  # modified (unused but required for API consistency)
) -> ValidationSummary | None:
    """Validate root-level configuration."""
    logger = getAppLogger()
    logger.trace(f"[validate_root] Validating root with {len(parsed_cfg)} keys")

    # --- Determine strictness from arg or default ---
    strict_config: bool = (
        strict_arg if strict_arg is not None else DEFAULT_STRICT_CONFIG
    )

    if strict_config:
        summary.strict = True

    # --- Check required fields first (before schema validation) ---
    if "packages" not in parsed_cfg:
        collect_msg(
            "Missing required field: 'packages'",
            strict=True,
            summary=summary,
            is_error=True,
        )
        return None  # Don't continue validation if packages is missing

    # --- Validate root-level keys using schema ---
    root_schema = schema_from_typeddict(RootConfig)
    ok = check_schema_conformance(
        parsed_cfg,
        root_schema,
        "in top-level configuration",
        strict_config=strict_config,
        summary=summary,
        base_path="root",
        field_examples=FIELD_EXAMPLES,
    )
    if not ok and not (summary.errors or summary.strict_warnings):
        collect_msg(
            "Top-level configuration invalid.",
            strict=True,
            summary=summary,
            is_error=True,
        )

    # --- Apply custom validation rules ---
    _validate_custom_rules(
        parsed_cfg,
        cwd=cwd,
        strict_config=strict_config,
        summary=summary,
    )

    return None


def validate_config(
    parsed_cfg: dict[str, Any],
    *,
    strict: bool | None = None,
    cwd: Path | None = None,
) -> ValidationSummary:
    """Validate normalized config using apathetic-schema.

    Args:
        parsed_cfg: Normalized configuration dictionary
        strict: Override strict mode (None uses default)
        cwd: Current working directory for path validation

    Returns:
        ValidationSummary object with validation results
    """
    logger = getAppLogger()
    logger.trace(f"[validate_config] Starting validation (strict={strict})")

    if cwd is None:
        cwd = Path.cwd().resolve()

    summary = ValidationSummary(
        valid=True,
        errors=[],
        strict_warnings=[],
        warnings=[],
        strict=DEFAULT_STRICT_CONFIG,
    )
    agg: SchemaErrorAggregator = {}

    # --- Validate root structure ---
    ret = _validate_root(
        parsed_cfg,
        strict_arg=strict,
        cwd=cwd,
        summary=summary,
        _agg=agg,
    )
    if ret is not None:
        return ret

    # --- finalize result ---
    return _set_valid_and_return(
        summary=summary,
        agg=agg,
    )
