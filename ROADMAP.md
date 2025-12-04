<!-- Roadmap.md -->
# 🧭 Roadmap

**Important Clarification**: Zipbundler provides Bundle your packages into a runnable, importable zip

## Key Points

Some of these we just want to consider, and may not want to implement.

## 🎯 Core Features

### Phase 1: Basic Zip Bundling
- **Package Discovery**: Automatically discover Python packages in a directory ✅
- **zipapp-Compatible Zip Creation**: Create `.pyz` files compatible with Python's `zipapp` module
- **Flat Structure**: Preserve original package paths without transformations
- **Import Support**: Ensure zip files are importable via `zipimport` and `importlib`
- **Basic CLI**: Simple command-line interface for bundling

### Phase 2: Configuration System
- **Config File Support**: `.zipbundler.py`, `.zipbundler.jsonc`, or `pyproject.toml` integration (searches current directory and parent directories) ✅
- **Output Path**: Configurable output directory and filename ✅
- **Entry Point Configuration**: Define entry points in config file ✅
- **Metadata Auto-Detection**: `init` command auto-detects metadata from `pyproject.toml` when creating config files ✅

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
    "directory": "build",  // Optional: output directory (default: "dist")
    "name": "my_package"  // Optional: used to generate default path ({directory}/{name}.pyz) when path is not specified
  },
  
  // Entry point for executable zip
  "entry_point": "my_package.__main__:main",
  
  // Control code generation
  "options": {
    "shebang": true,           // Insert shebang line (default: true)
    "compression": "deflate",   // zipfile compression method: "deflate", "stored", "bzip2", "lzma" (default: "stored") ✅
    "compression_level": 6     // Compression level 0-9 for deflate (default: 6) ✅
  },
  
  // Metadata
  "metadata": {
    "display_name": "My Package",
    "description": "Package description",
    "version": "1.0.0"
  }
}
```

## 🧰 CLI Commands

## 🔌 API Implementation

- **Config Parser**: Parse and validate configuration files
- **Package Scanner**: Discover and scan Python packages
- **Zip Builder**: Core logic for creating zip files
- **Entry Point Handler**: Handle entry point generation
- **Code Generator**: Generate shebang and entry point code

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
