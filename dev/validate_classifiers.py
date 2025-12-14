#!/usr/bin/env python3
"""Validate PyPI classifiers in pyproject.toml using trove-classifiers."""

import sys
from pathlib import Path


try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Python 3.10 and earlier
    except ImportError:
        print(
            "ERROR: Need tomli package for Python 3.10 or use Python 3.11+",
            file=sys.stderr,
        )
        sys.exit(1)

from trove_classifiers import classifiers


def load_pyproject() -> dict:
    """Load pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        return tomllib.load(f)


def validate_classifiers() -> int:
    """Validate classifiers in pyproject.toml. Returns 0 if all valid, 1 if errors."""
    valid_classifiers = set(classifiers)
    pyproject = load_pyproject()
    project_classifiers = pyproject.get("project", {}).get("classifiers", [])

    if not project_classifiers:
        print("No classifiers found in pyproject.toml")
        return 0

    errors = [
        classifier
        for classifier in project_classifiers
        if classifier not in valid_classifiers
    ]

    if errors:
        print("ERROR: Invalid classifiers found:", file=sys.stderr)
        for classifier in errors:
            print(f"  - {classifier}", file=sys.stderr)
        print(
            f"\nTotal: {len(errors)} invalid classifier(s) "
            f"out of {len(project_classifiers)}",
            file=sys.stderr,
        )
        return 1

    print(f"✓ All {len(project_classifiers)} classifier(s) are valid")
    return 0


if __name__ == "__main__":
    sys.exit(validate_classifiers())
