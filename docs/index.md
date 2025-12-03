---
layout: default
title: Zipbundler
description: Bundle your packages into a runnable, importable zip
---

# Zipbundler 🗜️

**Bundle your packages into a runnable, importable zip.**  
*Because installation is optional.*

Zipbundler creates **zipapp-compatible** `.pyz` files that are both runnable and importable. Unlike [shiv](https://github.com/linkedin/shiv) or [pex](https://github.com/pantsbuild/pex), zipbundler produces standard zipapp files compatible with Python's built-in `zipimport` module.

## Quick Start

Install Zipbundler:

```bash
# Using poetry
poetry add zipbundler

# Using pip
pip install zipbundler
```

**zipapp-style CLI (100% compatible with `python -m zipapp`):**
```bash
# All zipapp options supported
zipbundler src/myapp -o app.pyz -p "/usr/bin/env python3" -m "myapp:main" -c
zipbundler app.pyz --info  # Display interpreter from archive
```

**Or use configuration:**
```bash
zipbundler init
zipbundler build
```

## Key Features

- **zipapp Compatible** — Produces standard `.pyz` files compatible with Python's `zipapp` module
- **Importable** — Files can be imported using `zipimport` or `importlib`
- **Flat Structure** — Preserves original package paths without transformations
- **zipapp-style CLI** — Compatible with `python -m zipapp` command-line interface
- **Configurable** — Flexible configuration via `.zipbundler.jsonc` or `pyproject.toml`
- **Entry Points** — Support for executable zip files with custom entry points
- **Watch Mode** — Automatically rebuild on file changes

## Documentation

- **[Getting Started](/zipbundler/getting-started)** — Installation and quick start guide
- **[Configuration Reference](/zipbundler/configuration)** — Complete configuration file documentation
- **[CLI Reference](/zipbundler/cli-reference)** — All command-line options and usage
- **[API Reference](/zipbundler/api)** — Programmatic API for Python integration
- **[Examples](/zipbundler/examples)** — Real-world usage examples and patterns

## License

[MIT-a-NOAI License](https://github.com/apathetic-tools/zipbundler/blob/main/LICENSE)

You're free to use, copy, and modify the library under the standard MIT terms.  
The additional rider simply requests that this project not be used to train or fine-tune AI/ML systems until the author deems fair compensation frameworks exist.  
Normal use, packaging, and redistribution for human developers are unaffected.

---

<p align="center">
  <sub>😐 <a href="https://apathetic-tools.github.io/">Apathetic Tools</a> © <a href="https://github.com/apathetic-tools/zipbundler/blob/main/LICENSE">MIT-a-NOAI</a></sub>
</p>

