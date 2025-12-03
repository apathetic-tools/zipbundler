import argparse
import sys
from pathlib import Path

from .build import build_zipapp
from .logs import getAppLogger


def main(args: list[str] | None = None) -> int:
    """Main entry point for the zipbundler CLI."""
    logger = getAppLogger()
    parser = argparse.ArgumentParser(
        description="Bundle your packages into a runnable, importable zip"
    )

    parser.add_argument(
        "source",
        nargs="+",
        help="Source package directories to include in the zip",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output file path for the zipapp (.pyz extension recommended)",
    )
    parser.add_argument(
        "-m",
        "--main",
        dest="entry_point",
        help=(
            "Entry point for the zipapp. Can be a module:function "
            "(e.g., 'mymodule:main') or a module (e.g., 'mymodule'). "
            "If not specified, no __main__.py is created."
        ),
    )
    parser.add_argument(
        "-p",
        "--python",
        default="#!/usr/bin/env python3",
        help="Shebang line (default: '#!/usr/bin/env python3')",
    )

    parsed_args = parser.parse_args(args)

    # Convert entry point format
    entry_point: str | None = None
    if parsed_args.entry_point:
        if ":" in parsed_args.entry_point:
            # Format: module:function -> from module import function; function()
            module, function = parsed_args.entry_point.split(":", 1)
            entry_point = f"from {module} import {function}; {function}()"
        else:
            # Format: module -> import module; module.main()
            module = parsed_args.entry_point
            entry_point = f"import {module}; {module}.main()"

    try:
        packages = [Path(p) for p in parsed_args.source]
        output = Path(parsed_args.output)

        build_zipapp(
            output=output,
            packages=packages,
            entry_point=entry_point,
            shebang=parsed_args.python,
        )
    except (ValueError, FileNotFoundError) as e:
        logger.errorIfNotDebug(str(e))
        return 1
    except Exception as e:  # noqa: BLE001
        logger.criticalIfNotDebug("Unexpected error: %s", e)
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
