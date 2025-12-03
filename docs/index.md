---
layout: default
title: Python-Apathetic-Template
description: Presets for guiding agentic AI workflows.
---

# Python-Apathetic-Template 🧭

**Presets for guiding agentic AI workflows.**  
*Because tasks shouldn't get lost in translation.*

Python-Apathetic-Template provides a curated collection of AI guidance presets that you can selectively enable for your IDE integrations. Similar to how ruff lets you choose which linting rules to enable, Python-Apathetic-Template lets you pick and choose which rules, workflows, and commands to activate.

## Quick Start

Install Python-Apathetic-Template:

```bash
# Using poetry
poetry add python-apathetic-template

# Using pip
pip install python-apathetic-template
```

Enable presets in your project:

```bash
python-apathetic-template enable --rules code-quality --workflows testing
python-apathetic-template sync
```

## Key Features

- **Selective presets** — Choose only the rules, workflows, and commands you need
- **IDE integration** — Works with Cursor, Claude Desktop, and similar tools
- **Ruff-like interface** — Familiar `select` and `ignore` configuration model
- **Zero dependencies** — Lightweight and focused
- **Modular** — Enable or disable presets independently
- **Configurable** — Customize presets to match your project's needs

## What are Presets?

Python-Apathetic-Template offers three types of presets:

- **Preset Rules**: Pre-configured prompt rules that get added to each AI interaction
  - Code quality standards
  - Testing best practices
  - Documentation guidelines
  - Security considerations

- **Preset Workflows**: Common workflows you can point an AI assistant to
  - Setting up new features
  - Refactoring patterns
  - Debugging strategies
  - Code review checklists

- **Preset Commands**: Ready-to-use commands for common development tasks
  - Generate test files
  - Create documentation
  - Run code quality checks
  - Format and lint code

## Documentation

- **[Getting Started](/python-apathetic-template/getting-started)** — Installation and first steps
- **[Configuration](/python-apathetic-template/configuration)** — How to enable and configure presets
- **[CLI Reference](/python-apathetic-template/cli-reference)** — Command-line options and usage
- **[API Documentation](/python-apathetic-template/api)** — Programmatic API for integrations
- **[Examples](/python-apathetic-template/examples)** — Real-world usage examples

## License

[MIT-aNOAI License](https://github.com/apathetic-tools/python-apathetic-template/blob/main/LICENSE)

You're free to use, copy, and modify the library under the standard MIT terms.  
The additional rider simply requests that this project not be used to train or fine-tune AI/ML systems until the author deems fair compensation frameworks exist.  
Normal use, packaging, and redistribution for human developers are unaffected.

---

<p align="center">
  <sub>😐 <a href="https://apathetic-tools.github.io/">Apathetic Tools</a> © <a href="https://github.com/apathetic-tools/python-apathetic-template/blob/main/LICENSE">MIT-aNOAI</a></sub>
</p>

