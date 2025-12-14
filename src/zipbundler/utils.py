"""Utility functions for path resolution and include handling."""

from pathlib import Path

from zipbundler.config.config_types import IncludeResolved, OriginType


def make_include_resolved(
    path: Path | str,
    root: Path,
    origin: OriginType,
    *,
    dest: Path | None = None,
    pattern: str | None = None,
) -> IncludeResolved:
    """Create an IncludeResolved dictionary.

    Args:
        path: File or directory path (absolute or relative to root)
        root: Root directory for resolving relative paths
        origin: Source of the include (cli or config)
        dest: Optional custom destination in the output zip
        pattern: Original pattern before resolution (for logging)

    Returns:
        IncludeResolved dictionary
    """
    # Build result dict with optional fields only when present
    result_dict: dict[str, object] = {
        "path": path,
        "root": root,
        "origin": origin,
    }
    if pattern is not None:
        result_dict["pattern"] = pattern
    if dest is not None:
        result_dict["dest"] = dest

    return result_dict  # type: ignore[return-value]


def parse_include_with_dest(
    raw: str, context_root: Path
) -> tuple[IncludeResolved, bool]:
    """Parse include string with optional :dest suffix.

    Handles the "path:dest" format where path and dest are separated by a colon.
    Special handling for Windows drive letters (e.g., C:, D:).

    Args:
        raw: Raw include string, may contain ":dest" suffix
        context_root: Root directory for path resolution (cwd for CLI args)

    Returns:
        Tuple of (IncludeResolved, has_dest) where has_dest indicates
        if a destination was parsed from the input
    """
    has_dest = False
    path_str = raw
    dest_str: str | None = None

    # Handle "path:dest" format - split on last colon
    if ":" in raw:
        parts = raw.rsplit(":", 1)
        path_part, dest_part = parts[0], parts[1]

        # Check if this is a Windows drive letter (C:, D:, etc.)
        # Drive letters are 1-2 chars, possibly with backslash
        is_drive_letter = len(path_part) <= 2 and (  # noqa: PLR2004
            len(path_part) == 1 or path_part.endswith("\\")
        )

        if not is_drive_letter:
            # Valid dest separator found
            path_str = path_part
            dest_str = dest_part
            has_dest = True

    # Normalize the path: resolve relative paths to absolute
    full_path = (context_root / path_str).resolve()
    root = context_root.resolve()

    # Create IncludeResolved
    inc = make_include_resolved(
        full_path,
        root,
        "cli",
        pattern=raw,
    )

    # Add destination if specified
    if dest_str:
        inc["dest"] = Path(dest_str)

    return inc, has_dest
