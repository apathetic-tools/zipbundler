# src/zipbundler/build.py
"""Core build functionality for creating zipapp bundles."""

import stat
import zipfile
from pathlib import Path

from .logs import getAppLogger


def build_zipapp(
    output: Path,
    packages: list[Path],
    entry_point: str | None = None,
    shebang: str = "#!/usr/bin/env python3",
) -> None:
    """Build a zipapp-compatible zip file.

    Args:
        output: Output file path for the zipapp
        packages: List of package directories to include
        entry_point: Entry point code to write to __main__.py.
            If None, no __main__.py is created.
        shebang: Shebang line to prepend to the zip file

    Raises:
        ValueError: If output path is invalid or packages are empty
    """
    logger = getAppLogger()

    if not packages:
        xmsg = "At least one package must be provided"
        raise ValueError(xmsg)

    output.parent.mkdir(parents=True, exist_ok=True)

    logger.debug("Building zipapp: %s", output)
    logger.debug("Packages: %s", [str(p) for p in packages])
    logger.debug("Entry point: %s", entry_point)

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        # Write entry point if provided
        if entry_point is not None:
            zf.writestr("__main__.py", entry_point)
            logger.debug("Wrote __main__.py with entry point")

        # Add all Python files from packages
        for pkg in packages:
            pkg_path = Path(pkg).resolve()
            if not pkg_path.exists():
                logger.warning("Package path does not exist: %s", pkg_path)
                continue

            for f in pkg_path.rglob("*.py"):
                # Calculate relative path from package parent
                arcname = f.relative_to(pkg_path.parent)
                zf.write(f, arcname)
                logger.trace("Added file: %s -> %s", f, arcname)

    # Prepend shebang
    data = output.read_bytes()
    output.write_bytes(shebang.encode() + b"\n" + data)

    # Make executable
    output.chmod(output.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    logger.info("Created zipapp: %s", output)
