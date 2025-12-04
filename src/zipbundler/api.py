# src/zipbundler/api.py

"""Programmatic API for zipbundler."""

import shutil
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from apathetic_utils import find_all_packages_under_path, has_glob_chars

from .actions import watch_for_changes
from .build import build_zipapp, extract_archive_to_tempdir, list_files
from .commands.build import extract_entry_point_code
from .commands.validate import resolve_output_path_from_config
from .commands.zipapp_style import is_archive_file
from .config import (
    load_and_validate_config,
)
from .constants import DEFAULT_WATCH_INTERVAL
from .logs import getAppLogger


def _resolve_packages_for_api(  # noqa: C901, PLR0912
    packages: list[str], cwd: Path
) -> list[Path]:
    """Resolve multiple package patterns to actual package paths.

    Args:
        packages: List of package patterns
        cwd: Current working directory

    Returns:
        List of unique resolved package Path objects
    """
    logger = getAppLogger()
    all_packages: list[Path] = []

    for pattern in packages:
        # Handle glob patterns ending with /**/*.py - extract base directory
        if pattern.endswith(("/**/*.py", "\\**\\*.py")):
            base_str = pattern.rsplit("/**/*.py", 1)[0].rsplit("\\**\\*.py", 1)[0]
            base_path = (cwd / base_str).resolve()
            if (
                base_path.exists()
                and base_path.is_dir()
                and base_path not in all_packages
            ):
                all_packages.append(base_path)
            continue

        # Check if pattern has glob characters
        if has_glob_chars(pattern):
            if "*" in pattern:
                parts = pattern.split("*", 1)
                glob_root_str = parts[0].rstrip("/\\") if parts[0] else ""
                glob_root = (cwd / glob_root_str).resolve() if glob_root_str else cwd
                if glob_root.exists():
                    try:
                        matches = list(glob_root.glob(pattern))
                        seen: set[Path] = set()
                        for match in matches:
                            if match.is_dir():
                                resolved_path = match.resolve()
                                if resolved_path not in seen:
                                    seen.add(resolved_path)
                                    if resolved_path not in all_packages:
                                        all_packages.append(resolved_path)
                            elif match.is_file() and match.suffix == ".py":
                                parent = match.parent.resolve()
                                if parent not in seen:
                                    seen.add(parent)
                                    if parent not in all_packages:
                                        all_packages.append(parent)
                    except Exception as e:  # noqa: BLE001
                        logger.warning("Error globbing pattern '%s': %s", pattern, e)
            continue

        # Simple path - resolve relative to cwd
        full_path = (cwd / pattern).resolve()
        if full_path.exists() and full_path.is_dir():
            if full_path not in all_packages:
                all_packages.append(full_path)
        # Try to find packages under the path
        elif full_path.exists():
            found = find_all_packages_under_path(full_path)
            for pkg_name in found:
                # Convert package name to Path
                pkg_path = (full_path / pkg_name.replace(".", "/")).resolve()
                if (
                    pkg_path.exists()
                    and pkg_path.is_dir()
                    and pkg_path not in all_packages
                ):
                    all_packages.append(pkg_path)

    if not all_packages:
        logger.warning("No packages resolved from patterns: %s", packages)

    return all_packages


@dataclass
class BuildResult:
    """Result from a build operation."""

    output_path: Path
    """Path to created zip file."""
    file_count: int
    """Number of files included."""
    size_bytes: int
    """Size of zip file in bytes."""
    duration: float
    """Build duration in seconds."""


def create_archive(  # noqa: PLR0912
    source: str | Path,
    target: str | Path | None = None,
    *,
    interpreter: str | None = None,
    main: str | None = None,
    filter: Callable[[str], bool] | None = None,  # noqa: A002
    compressed: bool = False,
) -> Path:
    """Create a zipapp archive matching Python's zipapp.create_archive() API.

    This function is 100% compatible with Python's zipapp.create_archive() and can
    be used as a drop-in replacement.

    Args:
        source: Source directory or existing archive
        target: Output archive path (required if source is archive)
        interpreter: Python interpreter path for shebang (default: None)
        main: Main entry point as module:function or module (default: None)
        filter: Filter function for files (default: None, not yet implemented)
        compressed: Enable compression (default: False)

    Returns:
        Path to created archive

    Raises:
        ValueError: Invalid arguments
        FileNotFoundError: Source not found
    """
    logger = getAppLogger()
    source_path = Path(source).resolve()

    if not source_path.exists():
        msg = f"Source not found: {source_path}"
        raise FileNotFoundError(msg)

    # Determine target path
    if target is None:
        if is_archive_file(source_path):
            msg = "target is required when source is an archive"
            raise ValueError(msg)
        # Default target: source name with .pyz extension
        target_path = source_path.with_suffix(".pyz")
    else:
        target_path = Path(target).resolve()

    # Handle filter parameter (not yet implemented in build_zipapp)
    if filter is not None:
        logger.warning("filter parameter is not yet implemented, ignoring")

    # Check if source is an archive
    temp_dir: Path | None = None
    if is_archive_file(source_path):
        logger.debug("Source is an archive file, extracting to temporary directory")
        try:
            temp_dir = extract_archive_to_tempdir(source_path)
            packages = [temp_dir]
        except (FileNotFoundError, ValueError) as e:
            msg = f"Failed to extract archive: {e}"
            raise ValueError(msg) from e
    elif source_path.is_dir():
        packages = [source_path]
    else:
        msg = f"Source must be a directory or .pyz archive file: {source_path}"
        raise ValueError(msg)

    # Extract entry point code
    entry_point_code: str | None = None
    if main:
        entry_point_code = extract_entry_point_code(main)

    # Convert interpreter to shebang
    if interpreter:
        shebang = interpreter if interpreter.startswith("#!") else f"#!{interpreter}"
    else:
        shebang = None

    # Convert compressed to compression method
    compression = "deflate" if compressed else "stored"

    # Build the zipapp
    try:
        build_zipapp(
            output=target_path,
            packages=packages,
            entry_point=entry_point_code,
            shebang=shebang,
            compression=compression,
        )
    finally:
        # Clean up temporary directory if we created one
        if temp_dir and temp_dir.exists():
            logger.debug("Cleaning up temporary directory: %s", temp_dir)
            shutil.rmtree(temp_dir, ignore_errors=True)

    return target_path


def build_zip(  # noqa: C901, PLR0912, PLR0913, PLR0915
    config_path: str | Path | None = None,
    *,
    packages: list[str] | None = None,
    exclude: list[str] | None = None,
    output_path: str | Path | None = None,
    entry_point: str | None = None,
    interpreter: str | None = None,
    main_guard: bool = True,
    compressed: bool = False,
    compression: str | None = None,
    compression_level: int | None = None,
    metadata: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> BuildResult:
    """Build a zip file from configuration or parameters.

    Args:
        config_path: Path to configuration file (optional if parameters provided)
        packages: List of package paths/patterns (optional if config_path provided)
        exclude: List of exclude patterns (optional)
        output_path: Output zip file path (optional if config_path provided)
        entry_point: Entry point for executable zip (equivalent to 'main' in zipapp)
        interpreter: Python interpreter path for shebang
            (equivalent to 'interpreter' in zipapp)
        main_guard: If True, wrap entry point in if __name__ == "__main__": guard
        compressed: Enable compression (equivalent to 'compressed' in zipapp)
        compression: Compression method ("deflate", "stored", "bzip2", "lzma")
        compression_level: Compression level 0-9 for deflate (default: 6)
        metadata: Optional dictionary with metadata fields (display_name,
            description, version, author, license)
        cwd: Current working directory for resolving relative paths
            (default: current dir)

    Returns:
        BuildResult with output_path, file_count, size_bytes, and duration

    Raises:
        ValueError: Invalid arguments or configuration
        FileNotFoundError: Config file not found
    """
    start_time = time.time()

    if cwd is None:
        cwd = Path.cwd().resolve()

    # Load config if provided
    config: dict[str, Any] | None = None
    if config_path:
        result = load_and_validate_config(
            config_path=str(config_path),
            cwd=cwd,
            strict=False,
        )
        if result is None:
            msg = f"Configuration file not found: {config_path}"
            raise FileNotFoundError(msg)
        _config_file, root_config, validation = result
        # root_config is RootConfig (TypedDict), treat as dict for compatibility
        config = root_config  # type: ignore[assignment]
        if not validation.valid:
            error_msg = "; ".join(validation.errors + validation.strict_warnings)
            msg = f"Configuration validation failed: {error_msg}"
            raise ValueError(msg)

    # Merge config with parameters (parameters override config)
    if config:
        packages = packages or config.get("packages", [])
        exclude = exclude if exclude is not None else config.get("exclude")
        entry_point = entry_point or config.get("entry_point")
        metadata = metadata or config.get("metadata")

        # Extract output path from config
        if output_path is None:
            output_config: dict[str, Any] | None = config.get("output")
            output_path = resolve_output_path_from_config(output_config)

        # Extract options from config
        options: dict[str, Any] | None = config.get("options")
        if options:
            # Shebang/interpreter
            if interpreter is None and "shebang" in options:
                shebang_val = options["shebang"]
                if isinstance(shebang_val, str):
                    if shebang_val.startswith("#!"):
                        interpreter = shebang_val[2:]  # Remove #!
                    else:
                        interpreter = shebang_val
                elif isinstance(shebang_val, bool) and not shebang_val:
                    interpreter = None

            # Compression
            if compression is None:
                compression_val = options.get("compression")
                if compression_val is not None:
                    if isinstance(compression_val, str):
                        compression = compression_val
                    elif isinstance(compression_val, bool):
                        compression = "deflate" if compression_val else "stored"
                else:
                    compression = "stored"

            # Compression level
            if compression_level is None and "compression_level" in options:
                compression_level_val = options.get("compression_level")
                if isinstance(compression_level_val, int):
                    compression_level = compression_level_val

            # Main guard
            if "main_guard" in options:
                main_guard_val = options.get("main_guard")
                if isinstance(main_guard_val, bool):
                    main_guard = main_guard_val
    else:
        # No config, use defaults
        if not packages:
            msg = "packages must be provided if config_path is not specified"
            raise ValueError(msg)
        if output_path is None:
            output_path = Path("dist/bundle.pyz")
        if compression is None:
            compression = "deflate" if compressed else "stored"

    # Resolve output path relative to cwd
    output_path_obj = Path(output_path)
    if not output_path_obj.is_absolute():
        output_path = (cwd / output_path_obj).resolve()
    else:
        output_path = output_path_obj.resolve()

    # Resolve packages - ensure packages is not None
    if packages is None:
        msg = "packages must be provided"
        raise ValueError(msg)
    resolved_packages = _resolve_packages_for_api(packages, cwd)
    if not resolved_packages:
        msg = f"No valid packages found from patterns: {packages}"
        raise ValueError(msg)

    # Extract entry point code
    entry_point_code: str | None = None
    if entry_point:
        entry_point_code = extract_entry_point_code(entry_point)

    # Convert interpreter to shebang
    if interpreter:
        shebang = interpreter if interpreter.startswith("#!") else f"#!{interpreter}"
    else:
        shebang = None

    # Build the zipapp
    build_zipapp(
        output=output_path,
        packages=resolved_packages,
        entry_point=entry_point_code,
        shebang=shebang,
        compression=compression,
        compression_level=compression_level,
        exclude=exclude,
        main_guard=main_guard,
        metadata=metadata,
        force=False,  # API doesn't expose force, use default incremental behavior
    )

    # Calculate result
    duration = time.time() - start_time
    file_count = len(list_files(resolved_packages, exclude=exclude))
    if entry_point_code:
        file_count += 1  # Include __main__.py
    size_bytes = output_path.stat().st_size

    return BuildResult(
        output_path=output_path,
        file_count=file_count,
        size_bytes=size_bytes,
        duration=duration,
    )


def watch(  # noqa: PLR0912
    config_path: str | Path | None = None,
    *,
    packages: list[str] | None = None,
    output_path: str | Path | None = None,
    exclude: list[str] | None = None,
    interval: float = DEFAULT_WATCH_INTERVAL,
    callback: Callable[[BuildResult], None] | None = None,
    cwd: Path | None = None,
) -> None:
    """Watch for file changes and rebuild automatically.

    Args:
        config_path: Path to configuration file (optional if parameters provided)
        packages: List of package paths/patterns (optional if config_path provided)
        output_path: Output zip file path (optional if config_path provided)
        exclude: List of exclude patterns (optional)
        interval: Polling interval in seconds (default: 1.0)
        callback: Optional callback function called after each rebuild
            with BuildResult
        cwd: Current working directory for resolving relative paths
            (default: current dir)

    Raises:
        ValueError: Invalid arguments or configuration
        FileNotFoundError: Config file not found
    """
    if cwd is None:
        cwd = Path.cwd().resolve()

    # Build initial configuration
    # We need to resolve packages and output_path for watch_for_changes
    if config_path:
        result = load_and_validate_config(
            config_path=str(config_path),
            cwd=cwd,
            strict=False,
        )
        if result is None:
            msg = f"Configuration file not found: {config_path}"
            raise FileNotFoundError(msg)
        _config_file, config, validation = result
        if not validation.valid:
            error_msg = "; ".join(validation.errors + validation.strict_warnings)
            msg = f"Configuration validation failed: {error_msg}"
            raise ValueError(msg)

        # Extract packages and output from config
        if packages is None:
            packages = config.get("packages", [])
        if exclude is None:
            exclude = config.get("exclude")
        if output_path is None:
            output_config_raw = config.get("output")
            output_config: dict[str, Any] | None = output_config_raw  # type: ignore[assignment]
            output_path = resolve_output_path_from_config(output_config)

    if not packages:
        msg = "packages must be provided if config_path is not specified"
        raise ValueError(msg)
    if output_path is None:
        output_path = resolve_output_path_from_config(None)

    # Resolve output path relative to cwd
    if not isinstance(output_path, Path):
        output_path = Path(output_path)
    if not output_path.is_absolute():
        output_path = (cwd / output_path).resolve()
    else:
        output_path = output_path.resolve()

    # Resolve packages - packages is guaranteed to be non-None here
    assert packages is not None  # noqa: S101
    resolved_packages = _resolve_packages_for_api(packages, cwd)
    if not resolved_packages:
        msg = f"No valid packages found from patterns: {packages}"
        raise ValueError(msg)

    # Create rebuild function
    def rebuild() -> None:
        result = build_zip(
            packages=packages,
            exclude=exclude,
            output_path=output_path,
            cwd=cwd,
        )
        if callback:
            callback(result)

    # Start watching
    watch_for_changes(
        rebuild_func=rebuild,
        packages=resolved_packages,
        output=output_path,
        interval=interval,
        exclude=exclude,
    )
