# src/zipbundler/commands/build.py

"""Handle the build subcommand."""

import argparse
import importlib.util
import os
from importlib.metadata import distributions as _distributions
from pathlib import Path

from apathetic_utils import cast_hint, has_glob_chars

from zipbundler.build import build_zipapp
from zipbundler.commands.validate import resolve_output_path_from_config
from zipbundler.config import (
    MetadataConfig,
    OptionsConfig,
    OutputConfig,
    load_and_validate_config,
)
from zipbundler.constants import DEFAULT_DISABLE_BUILD_TIMESTAMP
from zipbundler.logs import getAppLogger
from zipbundler.utils import (
    load_gitignore_patterns,
    resolve_excludes,
    resolve_gitignore,
    resolve_includes,
)


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
                "Looking for .zipbundler.py, .zipbundler.jsonc, or pyproject.toml. "
                "Use 'zipbundler init' to create a config file."
            )
            logger.error(msg)
            return 1

        config_path, config, validation = result

        if not validation.valid:
            return 1

        # Extract packages
        packages_list: list[str] = config.get("packages", [])

        # CLI args override config
        if hasattr(args, "include") and args.include:
            packages_list = args.include

        if not packages_list:
            logger.error("No packages specified in configuration")
            return 1

        packages = _resolve_packages(packages_list, cwd)
        if not packages:
            logger.error("No valid packages found from patterns: %s", packages_list)
            return 1

        # Resolve includes from config and CLI args with proper path semantics
        # - config includes are relative to config file directory
        # - CLI includes (--include, --add-include) are relative to cwd
        config_dir = config_path.parent.resolve()
        # Cast to dict[str, object] for resolve_includes function
        raw_config = cast_hint(dict[str, object], config)
        resolved_includes = resolve_includes(
            raw_config, args=args, config_dir=config_dir, cwd=cwd
        )

        # Separate includes into packages and additional files
        additional_includes: list[tuple[Path, Path | None]] = []
        for inc in resolved_includes:
            full_path = inc["path"]
            if isinstance(full_path, Path):
                full_path_resolved = full_path
            else:
                # Path is relative to root
                full_path_resolved = (inc["root"] / full_path).resolve()

            dest = inc.get("dest")

            # Try to resolve as a package pattern first
            # (handles cases like 'extra/pkg2' or glob patterns)
            try:
                rel_to_cwd = full_path_resolved.relative_to(cwd)
                resolved_pkgs = _resolve_package_pattern(str(rel_to_cwd), cwd)
            except ValueError:
                # full_path_resolved is outside cwd, skip package resolution
                resolved_pkgs = []

            if resolved_pkgs:
                # It's a package directory (or glob pattern matching dirs)
                for pkg in resolved_pkgs:
                    if pkg not in packages:
                        packages.append(pkg)
                        logger.debug(
                            "Added package from include (origin: %s): %s",
                            inc["origin"],
                            pkg,
                        )
            elif full_path_resolved.is_file():
                # It's a file - track for inclusion
                additional_includes.append((full_path_resolved, dest))
                logger.debug(
                    "Added file from include (origin: %s): %s -> %s",
                    inc["origin"],
                    full_path_resolved,
                    dest or full_path_resolved.name,
                )
            else:
                # Path doesn't exist or is an unresolved glob
                logger.warning(
                    "Include path does not exist or is unresolved: %s",
                    full_path_resolved,
                )

        # Extract output path
        output_config: OutputConfig | None = config.get("output")
        output_path = resolve_output_path_from_config(
            output_config  # type: ignore[arg-type]
        )
        logger.debug(
            "Resolved output path from config: %s",
            output_path,
        )
        output = (cwd / output_path).resolve()

        # Extract entry point
        entry_point_str: str | None = config.get("entry_point")
        entry_point_code: str | None = None
        if entry_point_str:
            entry_point_code = extract_entry_point_code(entry_point_str)

        # Resolve excludes from config and CLI args with proper path semantics
        # - config excludes are relative to config file directory
        # - CLI excludes (--exclude, --add-exclude) are relative to cwd
        excludes = resolve_excludes(
            raw_config, args=args, config_dir=config_dir, cwd=cwd
        )

        # Load and merge .gitignore patterns if enabled
        respect_gitignore = resolve_gitignore(raw_config, args=args)
        if respect_gitignore:
            gitignore_path = config_dir / ".gitignore"
            patterns = load_gitignore_patterns(gitignore_path)
            if patterns:
                logger.trace(
                    "[build_command] Adding %d .gitignore patterns to excludes",
                    len(patterns),
                )
                for pattern in patterns:
                    exc = {
                        "path": pattern,
                        "root": config_dir,
                        "origin": "gitignore",
                    }
                    excludes.append(exc)  # type: ignore[arg-type]

        # Extract metadata
        metadata_config: MetadataConfig | None = config.get("metadata")
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
        options: OptionsConfig | None = config.get("options")
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
                elif isinstance(shebang_val, bool) and shebang_val:  # pyright: ignore[reportUnnecessaryIsInstance]
                    # If shebang is just True, use default
                    pass
                elif not shebang_val:
                    # If shebang is False, don't add shebang
                    shebang = None

            # Compression
            compression_val = options.get("compression")
            if compression_val is not None:
                if isinstance(compression_val, str):  # pyright: ignore[reportUnnecessaryIsInstance]
                    compression = compression_val
                elif isinstance(compression_val, bool):  # pyright: ignore[reportUnnecessaryIsInstance]
                    # Backward compatibility: True -> "deflate", False -> "stored"
                    compression = "deflate" if compression_val else "stored"
            # Default to "stored" if not specified
            if compression is None:
                compression = "stored"

            # Compression level
            if "compression_level" in options:
                compression_level_val = options["compression_level"]
                if isinstance(compression_level_val, int):  # pyright: ignore[reportUnnecessaryIsInstance]
                    compression_level = compression_level_val

            # Main guard
            if "main_guard" in options:
                main_guard_val = options["main_guard"]
                if isinstance(main_guard_val, bool):  # pyright: ignore[reportUnnecessaryIsInstance]
                    main_guard = main_guard_val

        # Resolve disable_build_timestamp (CLI + env var + default)
        # Priority: CLI arg > env var > default
        if (
            hasattr(args, "disable_build_timestamp")
            and args.disable_build_timestamp is not None
        ):
            # CLI arg was provided
            disable_build_timestamp = bool(args.disable_build_timestamp)
        else:
            # Check environment variable
            env_disable = os.getenv("DISABLE_BUILD_TIMESTAMP")
            if env_disable is not None:
                # Parse boolean from string (accept "true", "1", "yes", "on")
                disable_build_timestamp = env_disable.lower() in (
                    "true",
                    "1",
                    "yes",
                    "on",
                )
            else:
                # Use default from constants
                disable_build_timestamp = DEFAULT_DISABLE_BUILD_TIMESTAMP

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
            exclude=excludes,
            main_guard=main_guard,
            dry_run=getattr(args, "dry_run", False),
            metadata=metadata,
            force=getattr(args, "force", False),
            additional_includes=additional_includes if additional_includes else None,
            disable_build_timestamp=disable_build_timestamp,
        )
    except (FileNotFoundError, ValueError, TypeError) as e:
        logger.errorIfNotDebug(str(e))
        return 1
    except Exception as e:  # noqa: BLE001
        logger.criticalIfNotDebug("Unexpected error: %s", e)
        return 1
    else:
        return 0
