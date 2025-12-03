# src/zipbundler/actions.py

import re
import subprocess
from contextlib import suppress
from pathlib import Path

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
