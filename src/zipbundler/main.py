import argparse
import sys
from pathlib import Path

from .build import build_zipapp, get_interpreter
from .logs import getAppLogger


def main(args: list[str] | None = None) -> int:  # noqa: C901, PLR0911, PLR0912, PLR0915
    """Main entry point for the zipbundler CLI."""
    logger = getAppLogger()
    parser = argparse.ArgumentParser(
        description="Bundle your packages into a runnable, importable zip"
    )

    parser.add_argument(
        "source",
        nargs="*",
        help=(
            "Source package directories to include in the zip "
            "(or existing .pyz archive for --info)"
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path for the zipapp (.pyz extension recommended)",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Display the interpreter from an existing archive",
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

    # Handle --info flag
    if parsed_args.info:
        if not parsed_args.source:
            parser.error("--info requires a source archive file")
        if len(parsed_args.source) > 1:
            parser.error("--info requires exactly one source archive file")
        if parsed_args.output:
            parser.error("--info does not accept --output")

        try:
            archive = Path(parsed_args.source[0])
            interpreter = get_interpreter(archive)
            if interpreter is None:
                sys.stdout.write("No interpreter specified in archive\n")
                return 1
            sys.stdout.write(f"{interpreter}\n")
            return 0
        except (FileNotFoundError, ValueError) as e:
            logger.errorIfNotDebug(str(e))
            return 1
        except Exception as e:  # noqa: BLE001
            logger.criticalIfNotDebug("Unexpected error: %s", e)
            return 1
        else:
            sys.stdout.write(f"{interpreter}\n")
            return 0

    # Normal build mode
    if not parsed_args.source:
        parser.error("source is required when not using --info")
    if not parsed_args.output:
        parser.error("--output is required when not using --info")

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
