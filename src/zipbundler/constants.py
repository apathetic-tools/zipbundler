# src/zipbundler/constants.py
"""Central constants used across the project."""

RUNTIME_MODES = {
    "stitched",  # single concatenated file wiht module-shims
    "package",  # poetry-installed / pip-installed / importable
    "zipapp",  # .pyz bundle
}

# --- env keys ---
DEFAULT_ENV_LOG_LEVEL: str = "LOG_LEVEL"
DEFAULT_ENV_RESPECT_GITIGNORE: str = "RESPECT_GITIGNORE"
DEFAULT_ENV_WATCH_INTERVAL: str = "WATCH_INTERVAL"
DEFAULT_ENV_DISABLE_BUILD_TIMESTAMP: str = "DISABLE_BUILD_TIMESTAMP"
DEFAULT_ENV_COMPRESS: str = "COMPRESS"

# --- program defaults ---
DEFAULT_LOG_LEVEL: str = "info"
DEFAULT_WATCH_INTERVAL: float = 1.0  # seconds
DEFAULT_RESPECT_GITIGNORE: bool = True
DEFAULT_COMPRESS: bool = True

# --- config defaults ---
DEFAULT_STRICT_CONFIG: bool = True
DEFAULT_OUT_DIR: str = "dist"
DEFAULT_DRY_RUN: bool = False
DEFAULT_USE_PYPROJECT_METADATA: bool = True

DEFAULT_COMMENTS_MODE: str = "keep"  # Keep all comments (default comments mode)
DEFAULT_DOCSTRING_MODE: str = "keep"  # Keep all docstrings (default docstring mode)
DEFAULT_SOURCE_BASES: list[str] = [
    "src",
    "lib",
    "packages",
]  # Default directories to search for packages
DEFAULT_MAIN_MODE: str = "auto"  # Automatically detect and generate __main__ block
DEFAULT_MAIN_NAME: str | None = None  # Auto-detect main function (default)
DEFAULT_DISABLE_BUILD_TIMESTAMP: bool = False  # Use real timestamps by default
BUILD_TIMESTAMP_PLACEHOLDER: str = "<build-timestamp>"  # Placeholder
DEFAULT_LICENSE_FALLBACK: str = (
    "All rights reserved. See additional license files if distributed "
    "alongside this file for additional terms."
)
