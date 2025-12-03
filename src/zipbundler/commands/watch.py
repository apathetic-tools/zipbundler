# src/zipbundler/commands/watch.py

"""Handle the watch subcommand."""

import argparse
from pathlib import Path

from zipbundler.actions import watch_for_changes
from zipbundler.build import build_zipapp
from zipbundler.constants import DEFAULT_WATCH_INTERVAL
from zipbundler.logs import getAppLogger


def handle_watch_command(args: argparse.Namespace) -> int:
    """Handle the watch subcommand."""
    logger = getAppLogger()

    if not args.source:
        logger.error("source is required for watch command")
        return 1

    if not args.output:
        logger.error("output is required for watch command")
        return 1

    try:
        packages = [Path(p) for p in args.source]
        output = Path(args.output)

        # Determine watch interval
        interval = (
            args.interval if args.interval is not None else DEFAULT_WATCH_INTERVAL
        )

        # Build rebuild function
        def rebuild() -> None:
            build_zipapp(
                output=output,
                packages=packages,
                entry_point=args.entry_point,
                shebang=args.shebang or "#!/usr/bin/env python3",
                compress=args.compress,
                exclude=args.exclude,
                main_guard=getattr(args, "main_guard", True),
            )

        # Start watching
        watch_for_changes(
            rebuild_func=rebuild,
            packages=packages,
            output=output,
            interval=interval,
            exclude=args.exclude,
        )
    except (ValueError, FileNotFoundError) as e:
        logger.errorIfNotDebug(str(e))
        return 1
    except Exception as e:  # noqa: BLE001
        logger.criticalIfNotDebug("Unexpected error: %s", e)
        return 1
    else:
        return 0
