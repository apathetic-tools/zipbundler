# src/zipbundler/config/config_types.py

"""Configuration type definitions for zipbundler.

This module defines TypedDict schemas for all configuration structures.
"""

from typing import Literal, TypedDict


# --- Literal types for enums ---

CompressionMethod = Literal["deflate", "stored", "bzip2", "lzma"]


# --- Nested configuration types ---


class OutputConfig(TypedDict, total=False):
    """Output configuration for the zip file.

    Fields:
        path: Full path to output zip file (takes precedence over directory and name)
        directory: Output directory (default: "dist"). Used with name to generate path
        name: Optional name override for the zip file. When used with directory,
            generates {directory}/{name}.pyz
    """

    path: str
    directory: str
    name: str


class OptionsConfig(TypedDict, total=False):
    """Options configuration for zip file creation.

    Fields:
        shebang: Shebang line for the zip file. Can be:
            - True: Use default shebang
            - False: No shebang
            - str: Custom shebang path (with or without #!)
        main_guard: If True, wrap entry point in `if __name__ == "__main__":` guard
        compression: Compression method to use (default: "stored")
        compression_level: Compression level 0-9 (only valid with "deflate")
    """

    shebang: bool | str
    main_guard: bool
    compression: CompressionMethod
    compression_level: int  # 0-9


class MetadataConfig(TypedDict, total=False):
    """Metadata configuration for the zip file.

    Fields:
        display_name: Display name for the package
        description: Description of the package
        version: Version string
        author: Author information
        license: License information
    """

    display_name: str
    description: str
    version: str
    author: str
    license: str


# --- Root configuration type ---


class RootConfig(TypedDict, total=False):
    """Root configuration for zipbundler.

    Fields:
        packages: Required list of package paths or glob patterns to include
        exclude: Optional list of glob patterns for files/directories to exclude
        entry_point: Optional entry point in format "module.path:function" or
            "module.path"
        output: Optional output configuration
        options: Optional options configuration
        metadata: Optional metadata configuration
    """

    packages: list[str]  # Required
    exclude: list[str]
    entry_point: str
    output: OutputConfig
    options: OptionsConfig
    metadata: MetadataConfig
