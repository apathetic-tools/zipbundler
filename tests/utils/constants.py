# tests/utils/constants.py
"""Package metadata constants for test utilities."""

from pathlib import Path


# Project root directory (tests/utils/constants.py -> project root)
PROJ_ROOT = Path(__file__).resolve().parent.parent.parent.resolve()

# Package name used for imports and module paths
PROGRAM_PACKAGE = "{{project_name}}"

# Script name for the single-file distribution
PROGRAM_SCRIPT = "{{project_script_name}}"

# Config file name (used by patch_everywhere for stitch detection)
PROGRAM_CONFIG = "{{project_script_name}}"

# Bundler command hint (used for help messages in runtime utilities)
# The actual build is performed via `python -m serger` using .serger.jsonc.
BUNDLER_SCRIPT = "python -m serger"

# Stitch hints for patch_everywhere (paths that indicate stitched modules)
PATCH_STITCH_HINTS = {"/dist/", "standalone", f"{PROGRAM_SCRIPT}.py"}
