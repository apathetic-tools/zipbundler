<!-- Roadmap.md -->
# 🧭 Roadmap

**Important Clarification**: Zipbundler provides Bundle your packages into a runnable, importable zip

## Key Points

Some of these we just want to consider, and may not want to implement.

## 🎯 Core Features

### Phase 1: Basic Zip Bundling
- **Package Discovery**: Automatically discover Python packages in a directory
- **zipapp-Compatible Zip Creation**: Create `.pyz` files compatible with Python's `zipapp` module
- **Flat Structure**: Preserve original package paths without transformations
- **Import Support**: Ensure zip files are importable via `zipimport` and `importlib`
- **Entry Point Support**: Allow specifying entry points for executable zips
- **zipapp-style CLI**: Support `python -m zipapp` compatible command-line interface with full feature parity:
  - `-o, --output`: Output file path
  - `-p, --python`: Shebang line (interpreter path)
  - `-m, --main`: Main entry point (module:function or module)
  - `-c, --compress`: Enable compression (deflate method)
  - `--info`: Display interpreter from existing archive
  - Support reading existing `.pyz` archives as SOURCE
- **Basic CLI**: Simple command-line interface for bundling

### Phase 2: Configuration System
- **Config File Support**: `.zipbundler.jsonc` or `pyproject.toml` integration
- **Package Selection**: Configure which packages to include
- **Exclude Patterns**: Support glob patterns for excluding files/directories
- **Output Path**: Configurable output directory and filename
- **Shebang Control**: Option to enable/disable shebang insertion
- **Main Guard Control**: Option to enable/disable `if __name__ == "__main__"` insertion
- **Entry Point Configuration**: Define entry points in config file

### Phase 3: Advanced Features
- **Dependency Resolution**: Include dependencies from installed packages
- **Metadata Preservation**: Preserve package metadata and version info
- **Compression Options**: Support different compression levels
- **Watch Mode**: Rebuild zip on file changes
- **Dry Run Mode**: Preview what would be bundled without creating zip

## 🧰 CLI Commands

- `zipbundler build` - Build zip from current directory or config
- `zipbundler init` - Create a default `.zipbundler.jsonc` config file
- `zipbundler list` - List packages that would be included
- `zipbundler validate` - Validate configuration file
- `zipbundler watch` - Watch for changes and rebuild automatically
- **zipapp-style CLI** - Support `python -m zipapp` compatible interface:
  - `zipbundler SOURCE -o OUTPUT` - Specify source and output
  - `-p, --python SHEBANG` - Set shebang line (e.g., `"/usr/bin/env python3"`)
  - `-m, --main ENTRY_POINT` - Set main entry point (e.g., `"myapp:main"`)
  - `--compress` - Enable compression
  - Example: `zipbundler src/myapp -o app.pyz -p "/usr/bin/env python3" -m "myapp:main"`

## ⚙️ Configuration Features

### Configuration File Structure (`.zipbundler.jsonc`)
```jsonc
{
  // Packages to include (glob patterns or package names)
  "packages": [
    "src/my_package/**/*.py",
    "my_other_package"
  ],
  
  // Files/directories to exclude (glob patterns)
  "exclude": [
    "**/__pycache__/**",
    "**/*.pyc",
    "**/tests/**",
    "**/.git/**"
  ],
  
  // Output configuration
  "output": {
    "path": "dist/my_package.zip",
    "name": "my_package"  // Optional: override zip name
  },
  
  // Entry point for executable zip
  "entry_point": "my_package.__main__:main",
  
  // Control code generation
  "options": {
    "shebang": true,           // Insert shebang line (default: true)
    "main_guard": true,         // Insert if __name__ == "__main__" guard (default: true)
    "compression": "deflate"   // zipfile compression method (default: "deflate")
  },
  
  // Metadata
  "metadata": {
    "display_name": "My Package",
    "description": "Package description",
    "version": "1.0.0"
  }
}
```

## 🔌 API Implementation

- **Programmatic API**: Python API for bundling from code
- **Config Parser**: Parse and validate configuration files
- **Package Scanner**: Discover and scan Python packages
- **Zip Builder**: Core logic for creating zip files
- **Entry Point Handler**: Handle entry point generation
- **Code Generator**: Generate shebang and main guard code

## 📦 Preset Library

- **Common Patterns**: Preset configs for common project structures
- **Template Configs**: Starter configs for different use cases

## 🧪 Testing

- **Unit Tests**: Test core bundling functionality
- **Integration Tests**: Test with real package structures
- **Config Validation Tests**: Test configuration parsing
- **Import Tests**: Verify zip files are importable
- **Entry Point Tests**: Test executable zip functionality

## 📚 Documentation

- **Getting Started Guide**: Quick start tutorial
- **Configuration Reference**: Complete config file documentation
- **CLI Reference**: All command-line options
- **API Documentation**: Programmatic API reference
- **Examples**: Real-world usage examples
- **Best Practices**: Recommended patterns and workflows

## 🚀 Deployment

- **PyPI Package**: Publish to PyPI
- **GitHub Releases**: Automated releases
- **Documentation Site**: Deploy docs to GitHub Pages

## 💡 Future Ideas

- **Multi-format Support**: Support other archive formats
- **Incremental Builds**: Only rebuild changed files
- **Plugin System**: Extensible architecture for custom handlers
- **CI/CD Integration**: GitHub Actions, GitLab CI templates

## 🔧 Development Infrastructure

- **Self-hosting**: Use zipbundler to bundle itself
- **CI/CD Pipeline**: Automated testing and releases
- **Code Quality**: Linting, type checking, formatting

> See [REJECTED.md](REJECTED.md) for experiments and ideas that were explored but intentionally not pursued.

---

> ✨ *AI was used to help draft language, formatting, and code — plus we just love em dashes.*

<p align="center">
  <sub>😐 <a href="https://apathetic-tools.github.io/">Apathetic Tools</a> © <a href="./LICENSE">MIT-a-NOAI</a></sub>
</p>
