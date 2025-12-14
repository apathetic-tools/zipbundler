# src/zipbundler/commands/watch.py

"""Handle the watch subcommand."""

import argparse
from pathlib import Path

from zipbundler.actions import watch_for_changes
from zipbundler.build import build_zipapp
from zipbundler.constants import DEFAULT_WATCH_INTERVAL
from zipbundler.logs import getAppLogger
from zipbundler.utils import resolve_excludes


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
