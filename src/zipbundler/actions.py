# src/zipbundler/actions.py

import re
import time
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

from apathetic_utils import detect_runtime_mode, load_toml, run_with_output

from .config.config_types import PathResolved
from .constants import DEFAULT_WATCH_INTERVAL
from .logs import getAppLogger
from .meta import PROGRAM_PACKAGE, Metadata


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
    runtime_mode = detect_runtime_mode(PROGRAM_PACKAGE)
    if runtime_mode == "standalone":
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
        with suppress(Exception):
            data = load_toml(pyproject)
            if isinstance(data, dict):
                # Try project.version first (PEP 621)
                project_raw = data.get("project")
                if isinstance(project_raw, dict):
                    version_from_project = project_raw.get("version")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                    if isinstance(version_from_project, str):
                        version = version_from_project
                # Fallback to tool.poetry.version or [tool.zipbundler] version
                if version == "unknown":
                    tool_raw = data.get("tool")
                    if isinstance(tool_raw, dict):
                        poetry_raw = tool_raw.get("poetry")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                        if isinstance(poetry_raw, dict):
                            version_from_poetry = poetry_raw.get("version")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                            if isinstance(version_from_poetry, str):
                                version = version_from_poetry

    # Try git for commit
    with suppress(Exception):
        logger.trace("trying to get commit from git")
        result = run_with_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            check=True,
        )
        if result.stdout:
            commit = result.stdout.strip()

    logger.trace(f"got package version {version} with commit {commit}")
    return Metadata(version, commit)


def collect_watched_files(
    packages: list[Path],
    exclude: list[PathResolved] | None = None,
) -> list[Path]:
    """Collect all Python files from packages for watching.

    Args:
        packages: List of package directories to watch
        exclude: Optional list of resolved exclude patterns (PathResolved objects)

    Returns:
        List of unique sorted file paths to watch
    """
    from .build import list_files  # noqa: PLC0415

    excludes = exclude or []
    files = list_files(packages, exclude=excludes)

    # Return unique sorted list of file paths
    return sorted({file_path for file_path, _arcname in files})


def watch_for_changes(
    rebuild_func: Callable[[], None],
    packages: list[Path],
    output: Path,
    interval: float = DEFAULT_WATCH_INTERVAL,
    exclude: list[PathResolved] | None = None,
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
        exclude: Optional list of resolved exclude patterns (PathResolved objects)
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
