# tests/conftest.py
"""Shared test setup for project.

Each pytest run now targets a single runtime mode:
- Normal mode (default): uses src/{{project_name}}
- Standalone mode: uses dist/{{project_script_name}}.py when RUNTIME_MODE=singlefile
- Zipapp mode: uses dist/{{project_script_name}}.pyz when RUNTIME_MODE=zipapp

Switch mode with: RUNTIME_MODE=singlefile pytest or RUNTIME_MODE=zipapp pytest
"""

import os
from collections.abc import Generator

import apathetic_utils as mod_apathetic_utils
import pytest
from apathetic_logging import makeSafeTrace

import {{project_name}}.logs as mod_logs
from tests.utils import BUNDLER_SCRIPT, PROGRAM_PACKAGE, PROGRAM_SCRIPT, PROJ_ROOT


TEST_TRACE = makeSafeTrace("⚡️")

# early jank hook
mod_apathetic_utils.runtime_swap(
    root=PROJ_ROOT,
    package_name=PROGRAM_PACKAGE,
    script_name=PROGRAM_SCRIPT,
    bundler_script=BUNDLER_SCRIPT,
)

# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_logger_level() -> Generator[None, None, None]:
    """Reset logger level to default (INFO) before each test for isolation.

    In singlefile mode, the logger is a module-level singleton that persists
    between tests. This fixture ensures the logger level is reset to INFO
    (the default) before each test, preventing test interference.
    """
    # Get the app logger and reset to default level
    logger = mod_logs.getAppLogger()
    # Reset to INFO (default) - this ensures tests start with a known state
    logger.setLevel("info")
    yield
    # After test, reset again to ensure clean state for next test
    logger.setLevel("info")


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _mode() -> str:
    return os.getenv("RUNTIME_MODE", "installed")


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
        if "debug" in item.keywords:
            item.add_marker(
                pytest.mark.skip(reason="Skipped debug test (use -k debug to run)"),
            )


def _filter_runtime_mode_tests(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    mode = _mode()

    # file → number of tests
    included_map: dict[str, int] = {}
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

        if runtime_marker and runtime_marker == mode:
            file_path = str(item.fspath)
            # Make path relative to project root dir
            if file_path.startswith(root):
                file_path = os.path.relpath(file_path, root)
                for tp in testpaths:
                    if file_path.startswith(tp.rstrip("/") + os.sep):
                        file_path = file_path[len(tp.rstrip("/") + os.sep) :]
                        break

            included_map[file_path] = included_map.get(file_path, 0) + 1

    # Store results for later reporting
    config._included_map = included_map  # type: ignore[attr-defined] # noqa: SLF001
    config._runtime_mode = mode  # type: ignore[attr-defined] # noqa: SLF001


# ----------------------------------------------------------------------
# Hooks
# ----------------------------------------------------------------------


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
    mode = getattr(config, "_runtime_mode", "installed")

    if not included_map:
        return

    total_tests = sum(included_map.values())
    print(
        f"🧪 Included {total_tests} {mode}-specific tests"
        f" across {len(included_map)} files:",
    )
    for path, count in sorted(included_map.items()):
        print(f"   • ({count}) {path}")
