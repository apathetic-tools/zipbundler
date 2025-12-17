# tests/utils/constants.py
"""Package metadata constants for test utilities."""

from pathlib import Path


#: Project root directory (tests/utils/constants.py -> project root)
PROJ_ROOT = Path(__file__).resolve().parent.parent.parent.resolve()

#: Package name used for imports and module paths
PROGRAM_PACKAGE = "zipbundler"

#: Script name for the stitched distribution
PROGRAM_SCRIPT = "zipbundler"

#: Config file name (used by patch_everywhere for stitch detection)
PROGRAM_CONFIG = "zipbundler"

#: Path to the bundler script (relative to project root)
#: Uses the serger CLI installed in the environment, not a local bin script.
BUNDLER_SCRIPT = "serger"

#: Stitch hints for patch_everywhere (paths that indicate stitched modules)
PATCH_STITCH_HINTS = {"/dist/", "stitched", f"{PROGRAM_SCRIPT}.py"}

DEFAULT_TEST_LOG_LEVEL = "test"

#: Lint test: packages disallowed from `from ... import` statements in tests.
#: All imports from these packages must use `import <package>.<module> as mod_<module>`
#: format. This is required for runtime_swap and patch_everywhere to work correctly.
DISALLOWED_PACKAGES = [
    PROGRAM_PACKAGE,
    "apathetic_utils",
    "apathetic_logging",
    "apathetic_schema",
]
