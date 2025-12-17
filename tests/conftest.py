# tests/conftest.py
"""Shared test setup for project.

Each pytest run now targets a single runtime mode:
- Package mode (default): uses src/<package> when RUNTIME_MODE=package
- Stitched mode: uses dist/<package>.py when RUNTIME_MODE=stitched
- Zipapp mode: uses dist/<package>.pyz when RUNTIME_MODE=zipapp

Switch mode with: RUNTIME_MODE=stitched pytest or RUNTIME_MODE=zipapp pytest
"""

import os
from collections.abc import Generator

import apathetic_logging as alib_logging
import apathetic_utils as alib_utils
import pytest

from tests.utils import (
    DEFAULT_TEST_LOG_LEVEL,
    PROGRAM_PACKAGE,
    PROGRAM_SCRIPT,
    PROJ_ROOT,
)


# early jank hook, must happen before importing the <package>
# so we get the stitched/zipapp version in the right mode
alib_utils.runtime_swap(
    root=PROJ_ROOT,
    package_name=PROGRAM_PACKAGE,
    script_name=PROGRAM_SCRIPT,
)

from tests.utils import (  # noqa: E402
    direct_logger,
    module_logger,
)


# These fixtures are intentionally re-exported so pytest can discover them.
__all__ = [
    "direct_logger",
    "module_logger",
]

safe_trace = alib_logging.makeSafeTrace("⚡️")


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_logger_level() -> Generator[None, None, None]:
    """Reset logger level to default (INFO) before each test for isolation.

    In stitched mode, the logger is a module-level singleton that persists
    between tests. This fixture ensures the logger level is reset to INFO
    (the default) before each test, preventing test interference.
    """
    # Get the app logger and reset to default level
    logger = alib_logging.getLogger()
    # Reset to INFO (default) - this ensures tests start with a known state
    logger.setLevel(DEFAULT_TEST_LOG_LEVEL)
    yield
    # After test, reset again to ensure clean state for next test
    logger.setLevel(DEFAULT_TEST_LOG_LEVEL)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _mode() -> str:
    return os.getenv("RUNTIME_MODE", "package")


def _filter_debug_tests(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    # detect if the user is filtering for debug tests
    keywords = config.getoption("-k") or ""
    running_debug = "debug" in keywords.lower()

    if running_debug:
        return  # user explicitly requested them, don't skip

    for item in items:
        # Check for the actual @pytest.mark.debug marker, not just "debug" in keywords
        # (parametrized values can add "debug" to keywords, causing false positives)
        if item.get_closest_marker("debug") is not None:
            item.add_marker(
                pytest.mark.skip(reason="Skipped debug test (use -k debug to run)"),
            )


def _filter_runtime_mode_tests(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    mode = _mode()
    # Check if verbose mode is enabled (verbose > 0 means user wants verbose output)
    verbose = getattr(config.option, "verbose", 0)
    is_quiet = verbose <= 0

    # Only track included tests if not in quiet mode (for later reporting)
    included_map: dict[str, int] | None = {} if not is_quiet else None
    root = str(config.rootpath)
    testpaths: list[str] = config.getini("testpaths") or []

    # Identify mode-specific files by a custom variable defined at module scope
    for item in list(items):
        mod = item.getparent(pytest.Module)
        if mod is None or not hasattr(mod, "obj"):
            continue

        runtime_marker = getattr(mod.obj, "__runtime_mode__", None)

        if runtime_marker and runtime_marker != mode:
            items.remove(item)
            continue

        # Only track if not in quiet mode
        if runtime_marker and runtime_marker == mode and included_map is not None:
            file_path = str(item.fspath)
            # Make path relative to project root dir
            if file_path.startswith(root):
                file_path = os.path.relpath(file_path, root)
                for tp in testpaths:
                    if file_path.startswith(tp.rstrip("/") + os.sep):
                        file_path = file_path[len(tp.rstrip("/") + os.sep) :]
                        break

            included_map[file_path] = included_map.get(file_path, 0) + 1

    # Store results for later reporting (only if not in quiet mode)
    if included_map is not None:
        config._included_map = included_map  # type: ignore[attr-defined]  # noqa: SLF001
        config._runtime_mode = mode  # type: ignore[attr-defined]  # noqa: SLF001


# ----------------------------------------------------------------------
# Hooks
# ----------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest options based on verbosity."""
    verbose = getattr(config.option, "verbose", 0)
    if verbose <= 0:
        # In quiet mode, modify reportchars to exclude skipped tests ('s')
        # The -ra flag in pytest.ini shows all, but hide skipped in quiet mode
        reportchars = getattr(config.option, "reportchars", "")
        if reportchars == "a":
            # 'a' means "all except passed", change to exclude skipped and passed output
            # Use explicit chars: f (failed), E (error), x (xfailed), X (xpassed)
            config.option.reportchars = "fExX"
        elif "s" in reportchars or "P" in reportchars:
            # Remove 's' (skipped) and 'P' (passed with output) in quiet mode
            config.option.reportchars = reportchars.replace("s", "").replace("P", "")


def pytest_report_header(config: pytest.Config) -> str:  # noqa: ARG001 # pyright: ignore[reportUnknownParameterType]
    mode = _mode()
    return f"Runtime mode: {mode}"


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Filter and record runtime-specific tests for later reporting.

    also automatically skips debug tests unless asked for
    """
    _filter_debug_tests(config, items)
    _filter_runtime_mode_tests(config, items)


def pytest_unconfigure(config: pytest.Config) -> None:
    """Print summary of included runtime-specific tests at the end."""
    included_map: dict[str, int] = getattr(config, "_included_map", {})
    mode = getattr(config, "_runtime_mode", "package")

    if not included_map:
        return

    # Only print if pytest is not in quiet mode (verbose > 0 means verbose mode)
    verbose = getattr(config.option, "verbose", 0)
    if verbose <= 0:
        return

    total_tests = sum(included_map.values())
    print(
        f"🧪 Included {total_tests} {mode}-specific tests"
        f" across {len(included_map)} files:",
    )
    for path, count in sorted(included_map.items()):
        print(f"   • ({count}) {path}")
