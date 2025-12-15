# src/zipbundler/commands/watch.py

"""Handle the watch subcommand."""

import argparse
from pathlib import Path

from zipbundler.actions import watch_for_changes
from zipbundler.build import build_zipapp
from zipbundler.constants import DEFAULT_RESPECT_GITIGNORE, DEFAULT_WATCH_INTERVAL
from zipbundler.logs import getAppLogger
from zipbundler.utils import (
    load_gitignore_patterns,
    resolve_excludes,
)


def handle_watch_command(args: argparse.Namespace) -> int:
    """Handle the watch subcommand."""
    logger = getAppLogger()

    if not args.include:
        logger.error("source is required for watch command")
        return 1

    if not args.output:
        logger.error("output is required for watch command")
        return 1

    try:
        packages = [Path(p) for p in args.include]
        output = Path(args.output)
        cwd = Path.cwd()

        # Determine watch interval
        interval = args.watch if args.watch is not None else DEFAULT_WATCH_INTERVAL

        # Resolve excludes from CLI arguments (no config file in watch mode)
        # Watch only uses CLI excludes, so config=None and config_dir=cwd
        excludes = resolve_excludes(None, args=args, config_dir=cwd, cwd=cwd)

        # Load and merge .gitignore patterns if enabled
        # Check CLI flag first, then default to DEFAULT_RESPECT_GITIGNORE
        cli_gitignore: object = getattr(args, "respect_gitignore", None)
        if cli_gitignore is not None and isinstance(cli_gitignore, bool):
            respect_gitignore = cli_gitignore
        else:
            respect_gitignore = DEFAULT_RESPECT_GITIGNORE
        if respect_gitignore:
            gitignore_path = cwd / ".gitignore"
            patterns = load_gitignore_patterns(gitignore_path)
            if patterns:
                logger.trace(
                    "[watch_command] Adding %d .gitignore patterns to excludes",
                    len(patterns),
                )
                for pattern in patterns:
                    exc = {
                        "path": pattern,
                        "root": cwd,
                        "origin": "gitignore",
                    }
                    excludes.append(exc)  # type: ignore[arg-type]

        # Build rebuild function
        def rebuild() -> None:
            compression = "deflate" if getattr(args, "compress", False) else "stored"
            build_zipapp(
                output=output,
                packages=packages,
                entry_point=args.entry_point,
                shebang=args.shebang or "#!/usr/bin/env python3",
                compression=compression,
                exclude=excludes,
                main_guard=getattr(args, "main_guard", True),
                force=False,  # Watch handles change detection, use incremental builds
            )

        # Start watching
        watch_for_changes(
            rebuild_func=rebuild,
            packages=packages,
            output=output,
            interval=interval,
            exclude=excludes,
        )
    except (ValueError, FileNotFoundError) as e:
        logger.errorIfNotDebug(str(e))
        return 1
    except Exception as e:  # noqa: BLE001
        logger.criticalIfNotDebug("Unexpected error: %s", e)
        return 1
    else:
        return 0
