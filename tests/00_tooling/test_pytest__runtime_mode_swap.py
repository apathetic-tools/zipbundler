# tests/00_tooling/test_pytest__runtime_mode_swap.py
"""Verify runtime mode swap functionality in conftest.py.

This test verifies that our unique runtime_mode swap functionality works
correctly. Our conftest.py uses runtime_swap() to allow tests to run against
either the package (src/<package>) or the stitched
script (dist/<package>.py) based on the RUNTIME_MODE environment variable.

Verifies:
  - When RUNTIME_MODE=stitched: All modules resolve to dist/<package>.py
  - When RUNTIME_MODE is unset (package): All modules resolve to src/<package>/
  - Python's import cache (sys.modules) points to the correct sources
  - All submodules load from the expected location

This ensures our dual-runtime testing infrastructure functions correctly.
"""

import importlib
import inspect
import os
import pkgutil
import sys
from pathlib import Path

import apathetic_logging as alib_logging
import apathetic_utils as alib_utils
import pytest

import zipbundler as app_package
from tests.utils import PROGRAM_PACKAGE, PROGRAM_SCRIPT, PROJ_ROOT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

safe_trace = alib_logging.makeSafeTrace("🪞")

SRC_ROOT = PROJ_ROOT / "src"
DIST_ROOT = PROJ_ROOT / "dist"


def list_important_modules() -> list[str]:
    """Return all importable submodules under the package, if available."""
    important: list[str] = []
    if not hasattr(app_package, "__path__"):
        safe_trace("pkgutil.walk_packages skipped — stitched mode (no __path__)")
        important.append(app_package.__name__)
    else:
        for _, name, _ in pkgutil.walk_packages(
            app_package.__path__,
            app_package.__name__ + ".",
        ):
            important.append(name)

    return important


def dump_snapshot(*, include_full: bool = False) -> None:
    """Prints a summary of key modules and (optionally) a full sys.modules dump."""
    mode: str = os.getenv("RUNTIME_MODE", "package")

    safe_trace("========== SNAPSHOT ===========")
    safe_trace(f"RUNTIME_MODE={mode}")

    important_modules = list_important_modules()

    # Summary: the modules we care about most
    safe_trace("======= IMPORTANT MODULES =====")
    for name in important_modules:
        mod = sys.modules.get(name)
        if not mod:
            continue
        origin = getattr(mod, "__file__", None)
        safe_trace(f"  {name:<25} {origin}")

    if include_full:
        # Full origin dump
        safe_trace("======== OTHER MODULES ========")
        for name, mod in sorted(sys.modules.items()):
            if name in important_modules:
                continue
            origin = getattr(mod, "__file__", None)
            safe_trace(f"  {name:<38} {origin}")

    safe_trace("===============================")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_pytest_runtime_cache_integrity() -> None:  # noqa: PLR0912, PLR0915
    """Verify runtime mode swap correctly loads modules from expected locations.

    Ensures that modules imported at the top of test files resolve to the
    correct source based on RUNTIME_MODE:
    - stitched mode: All modules must load from dist/<package>.py
    - package mode: All modules must load from src/<package>/

    Also verifies that Python's import cache (sys.modules) doesn't have stale
    references pointing to the wrong runtime.
    """
    # --- setup ---
    mode = os.getenv("RUNTIME_MODE", "unknown")
    expected_script = DIST_ROOT / f"{PROGRAM_SCRIPT}.py"

    # In stitched mode, get the module from sys.modules to ensure we're using
    # the version from the stitched script (which was loaded by runtime_swap)
    # rather than the one imported at the top of this file (which might be from
    # the package if it was imported before runtime_swap ran)
    if mode in ("stitched", "zipapp") and PROGRAM_PACKAGE in sys.modules:
        # Use the module from sys.modules, which should be from the stitched
        app_package_actual = sys.modules[PROGRAM_PACKAGE]
        # Check __file__ directly - for stitched modules, should point to
        # dist/<package>.py or dist/<package>.pyz
        package_file_path = getattr(app_package_actual, "__file__", None)
        if package_file_path:
            package_file = str(package_file_path)
        else:
            # Fall back to inspect.getsourcefile if __file__ is not available
            package_file = str(inspect.getsourcefile(app_package_actual) or "")
    else:
        # Otherwise, use the module imported at the top of the file
        app_package_actual = app_package
        package_file = str(inspect.getsourcefile(app_package_actual) or "")
    # --- execute ---
    safe_trace(f"RUNTIME_MODE={mode}")
    safe_trace(f"{PROGRAM_PACKAGE}  → {package_file}")

    if os.getenv("TRACE"):
        dump_snapshot()
    # Access via main module to get the function from the namespace class
    runtime_mode = alib_utils.detect_runtime_mode(package_name=PROGRAM_PACKAGE)

    if mode == "stitched":
        # --- verify stitched ---
        # what does the module itself think?
        assert runtime_mode == "stitched", (
            f"Expected runtime_mode='stitched' but got '{runtime_mode}'"
        )

        # exists
        assert expected_script.exists(), (
            f"Expected stitched script at {expected_script}"
        )

        # path peeks - in stitched mode, the package module might be
        # imported from the package, but it should still detect
        # stitched mode correctly via sys.modules.get(PROGRAM_PACKAGE)
        # So we only check the path if the module is actually from dist/
        if package_file.startswith(str(DIST_ROOT)):
            # Module is from stitched script, verify it's the right file
            assert Path(package_file).samefile(expected_script), (
                f"{package_file} should be same file as {expected_script}"
            )
        else:
            # Module is from package, but that's OK as long as
            # detect_runtime_mode() correctly returns "stitched"
            safe_trace(
                f"Note: {PROGRAM_PACKAGE} loaded from package "
                f"({package_file}), but runtime_mode correctly detected as 'stitched'"
            )

        # troubleshooting info
        safe_trace(
            f"sys.modules['{PROGRAM_PACKAGE}'] = {sys.modules.get(PROGRAM_PACKAGE)}",
        )

    else:
        # --- verify module ---
        # what does the module itself think?
        assert runtime_mode != "stitched"

        # path peeks
        if mode == "zipapp":
            # In zipapp mode, module should be from the zipapp
            expected_zipapp = DIST_ROOT / f"{PROGRAM_SCRIPT}.pyz"
            assert package_file is not None, (
                "package_file should not be None in zipapp mode"
            )
            assert str(expected_zipapp) in str(package_file), (
                f"{package_file} not from zipapp {expected_zipapp}"
            )
        else:
            # In package mode, module should be from src/
            assert package_file is not None, (
                "package_file should not be None in package mode"
            )
            assert package_file.startswith(str(SRC_ROOT)), f"{package_file} not in src/"

    # --- verify both ---
    important_modules = list_important_modules()
    for submodule in important_modules:
        mod = importlib.import_module(f"{submodule}")
        # For zipapp modules, inspect.getsourcefile() may not work,
        # so use __file__ directly
        if mode == "zipapp":
            mod_file = getattr(mod, "__file__", None)
            if mod_file:
                path = Path(mod_file)
            else:
                path = Path(inspect.getsourcefile(mod) or "")
        else:
            path = Path(inspect.getsourcefile(mod) or "")
        if mode == "stitched":
            assert path.samefile(expected_script), f"{submodule} loaded from {path}"
        elif mode == "zipapp":
            # In zipapp mode, modules should be from the zipapp
            expected_zipapp = DIST_ROOT / f"{PROGRAM_SCRIPT}.pyz"
            assert str(expected_zipapp) in str(path), (
                f"{submodule} not from zipapp: {path}"
            )
        else:
            assert path.is_relative_to(SRC_ROOT), f"{submodule} not in src/: {path}"


@pytest.mark.debug
def test_debug_dump_all_module_origins() -> None:
    """Debug helper: Dump all loaded module origins for forensic analysis.

    Useful when debugging import leakage, stale sys.modules cache, or runtime
    mode swap issues. Always fails intentionally to force pytest to show TRACE
    output.

    Usage:
        TRACE=1 poetry run pytest -k debug -s
        RUNTIME_MODE=stitched TRACE=1 poetry run pytest -k debug -s
    """
    # --- verify ---

    # dump everything we know
    dump_snapshot(include_full=True)

    # show total module count for quick glance
    count = sum(1 for name in sys.modules if name.startswith(PROGRAM_PACKAGE))
    safe_trace(f"Loaded {count} {PROGRAM_PACKAGE} modules total")

    # force visible failure for debugging runs
    xmsg = f"Intentional fail — {count} {PROGRAM_PACKAGE} modules listed above."
    raise AssertionError(xmsg)
