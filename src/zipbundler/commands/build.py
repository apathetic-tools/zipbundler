# src/zipbundler/commands/build.py

"""Handle the build subcommand."""

import argparse
import importlib.util
from importlib.metadata import distributions as _distributions
from pathlib import Path
from typing import Any

from apathetic_utils import has_glob_chars

from zipbundler.build import build_zipapp
from zipbundler.commands.validate import (
    find_config,
    load_config,
    validate_config_structure,
)
from zipbundler.logs import getAppLogger


def _resolve_installed_package(package_name: str) -> Path | None:
    """Resolve an installed package by name to its location.

    Uses importlib.util.find_spec to find the package location. If the package
    is found, returns the Path to the package directory.

    Args:
        package_name: Name of the installed package (e.g., "apathetic_utils")

    Returns:
        Path to the package directory if found, None otherwise
    """
    logger = getAppLogger()

    # Try importlib.util.find_spec (most reliable method)
    try:
        spec = importlib.util.find_spec(package_name)
        if spec is not None and spec.origin is not None:
            origin_path = Path(spec.origin)
            # If origin is a file (e.g., __init__.py), use its parent directory
            package_path = origin_path.parent if origin_path.is_file() else origin_path
            if package_path.exists() and package_path.is_dir():
                logger.debug(
                    "Resolved installed package '%s' to: %s",
                    package_name,
                    package_path,
                )
                return package_path
    except Exception as e:  # noqa: BLE001
        logger.trace(
            "Error finding package '%s' via importlib.util: %s", package_name, e
        )

    # Fallback: try importlib.metadata for distribution-based lookup
    try:
        # Check all distributions for a matching package
        for dist in _distributions():
            # Check if the distribution name matches (normalize names)
            dist_name = getattr(dist.metadata, "Name", "") or ""
            normalized_dist = dist_name.lower().replace("-", "_")
            normalized_pkg = package_name.lower().replace("-", "_")
            if dist_name and normalized_dist == normalized_pkg:
                try:
                    # Get the root of the distribution
                    dist_file_path = dist.locate_file("")
                    dist_path = Path(str(dist_file_path))
                    # Look for the package directory within the distribution
                    # The package name might be different from the distribution name
                    possible_paths = [
                        dist_path / package_name,
                        dist_path / package_name.replace("-", "_"),
                        dist_path / dist_name.replace("-", "_"),
                    ]
                    for possible_path in possible_paths:
                        if possible_path.exists() and possible_path.is_dir():
                            logger.debug(
                                "Resolved installed package '%s' to: %s",
                                package_name,
                                possible_path,
                            )
                            return possible_path
                    # If no exact match, return the distribution root
                    if dist_path.exists():
                        logger.debug(
                            "Resolved installed package '%s' to distribution root: %s",
                            package_name,
                            dist_path,
                        )
                        return Path(dist_path)
                except Exception as e:  # noqa: BLE001
                    logger.trace("Error locating package '%s': %s", package_name, e)
    except Exception as e:  # noqa: BLE001
        logger.trace(
            "Error finding package '%s' via importlib.metadata: %s", package_name, e
        )

    return None


def _resolve_package_pattern(pattern: str, cwd: Path) -> list[Path]:  # noqa: C901, PLR0912, PLR0915
    """Resolve a package pattern to actual package paths.

    Handles:
    - Simple paths: "src/my_package" -> [Path("src/my_package")]
    - Glob patterns ending with /**/*.py: "src/**/*.py" -> [Path("src")]
    - Installed packages: "apathetic_utils" -> [Path to installed package]

    Args:
        pattern: Package pattern (path, glob, or installed package name)
        cwd: Current working directory for resolving relative paths

    Returns:
        List of resolved package Path objects
    """
    logger = getAppLogger()
    resolved: list[Path] = []

    # Handle glob patterns ending with /**/*.py - extract base directory
    # This is the most common pattern in configs
    if pattern.endswith(("/**/*.py", "\\**\\*.py")):
        # Extract base directory before /**/*.py
        base_str = pattern.rsplit("/**/*.py", 1)[0].rsplit("\\**\\*.py", 1)[0]
        base_path = (cwd / base_str).resolve()
        if base_path.exists() and base_path.is_dir():
            resolved.append(base_path)
            logger.trace("Resolved pattern '%s' to package: %s", pattern, base_path)
        else:
            logger.warning(
                "Pattern '%s' resolved to non-existent directory: %s",
                pattern,
                base_path,
            )
        return resolved

    # Check if pattern has glob characters (other than /**/*.py)
    if has_glob_chars(pattern):
        # For other glob patterns, try to find the base directory
        # Split on first glob char to find root
        if "*" in pattern:
            # Find the root of the glob pattern
            parts = pattern.split("*", 1)
            if parts[0]:
                glob_root_str = parts[0].rstrip("/\\")
                glob_root = (cwd / glob_root_str).resolve() if glob_root_str else cwd
            else:
                glob_root = cwd

            if glob_root.exists():
                # Use pathlib glob to find matching paths
                try:
                    matches = list(glob_root.glob(pattern))
                    # Collect unique parent directories of Python files,
                    # or directories themselves
                    seen: set[Path] = set()
                    for match in matches:
                        if match.is_dir():
                            resolved_path = match.resolve()
                            if resolved_path not in seen:
                                seen.add(resolved_path)
                                resolved.append(resolved_path)
                        elif match.is_file() and match.suffix == ".py":
                            # If it's a Python file, use its parent directory
                            parent = match.parent.resolve()
                            if parent not in seen:
                                seen.add(parent)
                                resolved.append(parent)
                except Exception as e:  # noqa: BLE001
                    logger.warning("Error globbing pattern '%s': %s", pattern, e)
            else:
                logger.warning(
                    "Glob root does not exist for pattern '%s': %s", pattern, glob_root
                )
    else:
        # Simple path - resolve relative to cwd
        full_path = (cwd / pattern).resolve()
        if full_path.exists():
            if full_path.is_dir():
                resolved.append(full_path)
            else:
                logger.warning("Pattern '%s' is a file, not a directory", pattern)
        # Path doesn't exist - try resolving as installed package name
        # Only try if pattern doesn't look like a path
        # (no slashes, no dots as path separators)
        elif "/" not in pattern and "\\" not in pattern and not pattern.startswith("."):
            # Try to resolve as installed package
            installed_path = _resolve_installed_package(pattern)
            if installed_path is not None:
                resolved.append(installed_path)
                logger.debug(
                    "Resolved pattern '%s' as installed package: %s",
                    pattern,
                    installed_path,
                )
            else:
                logger.warning(
                    "Pattern '%s' resolved to non-existent path and is not an "
                    "installed package: %s",
                    pattern,
                    full_path,
                )
        else:
            logger.warning(
                "Pattern '%s' resolved to non-existent path: %s",
                pattern,
                full_path,
            )

    return resolved


def _resolve_packages(packages: list[str], cwd: Path) -> list[Path]:
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
        resolved = _resolve_package_pattern(pattern, cwd)
        for pkg in resolved:
            if pkg not in all_packages:
                all_packages.append(pkg)
                logger.debug("Resolved package pattern '%s' to: %s", pattern, pkg)

    if not all_packages:
        logger.warning("No packages resolved from patterns: %s", packages)

    return all_packages


def extract_entry_point_code(entry_point: str) -> str:
    """Extract entry point code from entry point string.

    Args:
        entry_point: Entry point in format "module:function" or "module"

    Returns:
        Python code to execute the entry point
    """
    if ":" in entry_point:
        module, function = entry_point.rsplit(":", 1)
        return f"from {module} import {function}\n{function}()"
    # Just module - import and run __main__ or main
    code_lines = [
        f"import {entry_point}",
        f"if hasattr({entry_point}, '__main__'):",
        f"    {entry_point}.__main__()",
        f"elif hasattr({entry_point}, 'main'):",
        f"    {entry_point}.main()",
    ]
    return "\n".join(code_lines)


def handle_build_command(args: argparse.Namespace) -> int:  # noqa: C901, PLR0911, PLR0912, PLR0915
    """Handle the build subcommand."""
    logger = getAppLogger()

    cwd = Path.cwd().resolve()
    config_path = find_config(getattr(args, "config", None), cwd)

    if not config_path:
        msg = (
            "No configuration file found. "
            "Looking for .zipbundler.jsonc or pyproject.toml. "
            "Use 'zipbundler init' to create a config file."
        )
        logger.error(msg)
        return 1

    try:
        logger.debug("Loading configuration from: %s", config_path)
        config = load_config(config_path)

        # Validate config structure
        strict = getattr(args, "strict", False)
        is_valid, errors, warnings = validate_config_structure(
            config, cwd, strict=strict
        )

        if not is_valid:
            if errors:
                logger.error(
                    "Configuration validation failed with %d error(s):", len(errors)
                )
                for error in errors:
                    logger.error("  • %s", error)
            if warnings and strict:
                logger.error(
                    "Configuration validation failed with %d warning(s) (strict mode):",
                    len(warnings),
                )
                for warning in warnings:
                    logger.error("  • %s", warning)
            return 1

        if warnings:
            logger.warning("Configuration has %d warning(s):", len(warnings))
            for warning in warnings:
                logger.warning("  • %s", warning)

        # Extract packages
        packages_list: list[str] = config.get("packages", [])
        if not packages_list:
            logger.error("No packages specified in configuration")
            return 1

        packages = _resolve_packages(packages_list, cwd)
        if not packages:
            logger.error("No valid packages found from patterns: %s", packages_list)
            return 1

        # Extract output path
        output_config: dict[str, Any] | None = config.get("output")
        if output_config:  # pyright: ignore[reportUnnecessaryIsInstance]
            output_path_str: str | None = output_config.get("path")
        else:
            output_path_str = None

        if not output_path_str:
            # Default output path
            output_path_str = "dist/bundle.zip"
            logger.debug("No output path specified, using default: %s", output_path_str)

        output = (cwd / output_path_str).resolve()

        # Extract entry point
        entry_point_str: str | None = config.get("entry_point")
        entry_point_code: str | None = None
        if entry_point_str:
            entry_point_code = extract_entry_point_code(entry_point_str)

        # Extract exclude patterns
        exclude: list[str] | None = config.get("exclude")
        if exclude and not isinstance(exclude, list):  # pyright: ignore[reportUnnecessaryIsInstance]
            logger.warning("exclude field must be a list, ignoring")
            exclude = None

        # Extract metadata
        metadata_config: dict[str, Any] | None = config.get("metadata")
        metadata: dict[str, str] | None = None
        if metadata_config:
            if not isinstance(metadata_config, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
                logger.warning("metadata field must be an object, ignoring")
            else:
                # Convert metadata dict to dict[str, str],
                # filtering out non-string values
                metadata = {}
                for key, value in metadata_config.items():
                    if isinstance(value, str):
                        metadata[key] = value
                    else:
                        logger.warning("metadata.%s must be a string, ignoring", key)

        # Extract options
        options: dict[str, Any] | None = config.get("options")
        shebang: str | None = "#!/usr/bin/env python3"
        compression: str | None = None
        compression_level: int | None = None
        main_guard = True

        if options:  # pyright: ignore[reportUnnecessaryIsInstance]
            # Shebang
            if "shebang" in options:
                shebang_val = options["shebang"]
                if isinstance(shebang_val, str):
                    if shebang_val.startswith("#!"):
                        shebang = shebang_val
                    else:
                        shebang = f"#!{shebang_val}"
                elif isinstance(shebang_val, bool) and shebang_val:
                    # If shebang is just True, use default
                    pass
                elif not shebang_val:
                    # If shebang is False, don't add shebang
                    shebang = None

            # Compression
            compression_val = options.get("compression")
            if compression_val is not None:
                if isinstance(compression_val, str):
                    compression = compression_val
                elif isinstance(compression_val, bool):
                    # Backward compatibility: True -> "deflate", False -> "stored"
                    compression = "deflate" if compression_val else "stored"
            # Default to "stored" if not specified
            if compression is None:
                compression = "stored"

            # Compression level
            if "compression_level" in options:
                compression_level_val = options["compression_level"]
                if isinstance(compression_level_val, int):
                    compression_level = compression_level_val

            # Main guard
            if "main_guard" in options:
                main_guard_val = options["main_guard"]
                if isinstance(main_guard_val, bool):
                    main_guard = main_guard_val

        # CLI args override config
        if hasattr(args, "output") and args.output:
            output = Path(args.output).resolve()
        if hasattr(args, "entry_point") and args.entry_point:
            entry_point_code = extract_entry_point_code(args.entry_point)
        if hasattr(args, "shebang"):
            # Handle --no-shebang (False) or --python/-p (string)
            if args.shebang is False:
                shebang = None
            elif args.shebang:
                if args.shebang.startswith("#!"):
                    shebang = args.shebang
                else:
                    shebang = f"#!{args.shebang}"
        if hasattr(args, "compress") and args.compress is not None:
            # CLI --compress flag: True -> "deflate", False -> "stored"
            compression = "deflate" if args.compress else "stored"
        if hasattr(args, "compression_level") and args.compression_level is not None:
            compression_level = args.compression_level
            # compression_level only applies to deflate, ensure compression is deflate
            if compression != "deflate":
                compression = "deflate"
        if hasattr(args, "exclude") and args.exclude:
            exclude = args.exclude
        if hasattr(args, "main_guard") and args.main_guard is not None:
            main_guard = args.main_guard
        if hasattr(args, "dry_run") and args.dry_run:
            # Handle dry_run if provided
            pass

        # Build the zipapp
        logger.info("Building zipapp from configuration: %s", config_path.name)
        build_zipapp(
            output=output,
            packages=packages,
            entry_point=entry_point_code,
            shebang=shebang,
            compression=compression,
            compression_level=compression_level,
            exclude=exclude,
            main_guard=main_guard,
            dry_run=getattr(args, "dry_run", False),
            metadata=metadata,
        )
    except (FileNotFoundError, ValueError, TypeError) as e:
        logger.errorIfNotDebug(str(e))
        return 1
    except Exception as e:  # noqa: BLE001
        logger.criticalIfNotDebug("Unexpected error: %s", e)
        return 1
    else:
        return 0
