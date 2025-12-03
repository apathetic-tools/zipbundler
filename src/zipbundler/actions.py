# src/zipbundler/actions.py

import re
import subprocess
import time
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

from .constants import DEFAULT_WATCH_INTERVAL
from .logs import getAppLogger
from .meta import Metadata


def _get_metadata_from_header(script_path: Path) -> tuple[str, str]:
    """Extract version and commit from standalone script.

    Prefers in-file constants (__version__, __commit__) if present;
    falls back to commented header tags.
    """
    logger = getAppLogger()
    version = "unknown"
    commit = "unknown"

    logger.trace("reading commit from header:", script_path)

    with suppress(Exception):
        text = script_path.read_text(encoding="utf-8")

        # --- Prefer Python constants if defined ---
        const_version = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", text)
        const_commit = re.search(r"__commit__\s*=\s*['\"]([^'\"]+)['\"]", text)
        if const_version:
            version = const_version.group(1)
        if const_commit:
            commit = const_commit.group(1)

        # --- Fallback: header lines ---
        if version == "unknown" or commit == "unknown":
            for line in text.splitlines():
                if line.startswith("# Version:") and version == "unknown":
                    version = line.split(":", 1)[1].strip()
                elif line.startswith("# Commit:") and commit == "unknown":
                    commit = line.split(":", 1)[1].strip()

    return version, commit


def get_metadata() -> Metadata:
    """Return (version, commit) tuple for this tool.

    - Standalone script → parse from header
    - Source installed → read pyproject.toml + git
    """
    script_path = Path(__file__)
    logger = getAppLogger()
    logger.trace("get_metadata ran from:", Path(__file__).resolve())

    # --- Heuristic: standalone script lives outside `src/` ---
    if globals().get("__STANDALONE__", False):
        version, commit = _get_metadata_from_header(script_path)
        logger.trace(f"got standalone version {version} with commit {commit}")
        return Metadata(version, commit)

    # --- Modular / source installed case ---

    # Source package case
    version = "unknown"
    commit = "unknown"

    # Try pyproject.toml for version
    root = Path(__file__).resolve().parents[2]
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        logger.trace(f"trying to read metadata from {pyproject}")
        text = pyproject.read_text()
        match = re.search(r'(?m)^\s*version\s*=\s*["\']([^"\']+)["\']', text)
        if match:
            version = match.group(1)

    # Try git for commit
    with suppress(Exception):
        logger.trace("trying to get commit from git")
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],  # noqa: S607
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        commit = result.stdout.strip()

    logger.trace(f"got package version {version} with commit {commit}")
    return Metadata(version, commit)


def collect_watched_files(
    packages: list[Path],
    exclude: list[str] | None = None,
) -> list[Path]:
    """Collect all Python files from packages for watching.

    Args:
        packages: List of package directories to watch
        exclude: Optional list of glob patterns for files/directories to exclude

    Returns:
        List of unique sorted file paths to watch
    """
    from .build import list_files  # noqa: PLC0415

    exclude_patterns = exclude or []
    files = list_files(packages, exclude=exclude_patterns)

    # Return unique sorted list of file paths
    return sorted({file_path for file_path, _arcname in files})


def watch_for_changes(
    rebuild_func: Callable[[], None],
    packages: list[Path],
    output: Path,
    interval: float = DEFAULT_WATCH_INTERVAL,
    exclude: list[str] | None = None,
) -> None:
    """Poll file modification times and rebuild when changes are detected.

    Features:
    - Skips files inside the build's output directory.
    - Re-expands package patterns every loop to detect newly created files.
    - Polling interval defaults to 1 second (tune 0.5–2.0 for balance).
    Stops on KeyboardInterrupt.

    Args:
        rebuild_func: Function to call when changes are detected
        packages: List of package directories to watch
        output: Output file path (files inside this path are ignored)
        interval: Polling interval in seconds
        exclude: Optional list of glob patterns for files/directories to exclude
    """
    logger = getAppLogger()
    logger.info(
        "👀 Watching for changes (interval=%.2fs)... Press Ctrl+C to stop.", interval
    )

    # Discover files at start
    included_files = collect_watched_files(packages, exclude)

    mtimes: dict[Path, float] = {
        f: f.stat().st_mtime for f in included_files if f.exists()
    }

    # Resolve output path to ignore (can be directory or file)
    out_path = output.resolve()

    rebuild_func()  # initial build

    try:
        while True:
            time.sleep(interval)

            # 🔁 re-expand every tick so new/removed files are tracked
            included_files = collect_watched_files(packages, exclude)

            logger.trace(f"[watch] Checking {len(included_files)} files for changes")

            changed: list[Path] = []
            for f in included_files:
                # skip files that are inside or equal to the output path
                if f == out_path or (out_path.exists() and f.is_relative_to(out_path)):
                    continue  # ignore output files/folders
                old_m = mtimes.get(f)
                if not f.exists():
                    if old_m is not None:
                        changed.append(f)
                        mtimes.pop(f, None)
                    continue
                new_m = f.stat().st_mtime
                if old_m is None or new_m > old_m:
                    changed.append(f)
                    mtimes[f] = new_m

            if changed:
                logger.info(
                    "\n🔁 Detected %d modified file(s). Rebuilding...", len(changed)
                )
                rebuild_func()
                # refresh timestamps after rebuild
                mtimes = {f: f.stat().st_mtime for f in included_files if f.exists()}
    except KeyboardInterrupt:
        logger.info("\n🛑 Watch stopped.")
