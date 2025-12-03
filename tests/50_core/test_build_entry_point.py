# tests/50_core/test_build_entry_point.py
"""Tests for entry point support in zipapp building."""

import zipfile
from pathlib import Path

import pytest

import zipbundler.build as mod_build


def test_build_zipapp_with_entry_point(tmp_path: Path) -> None:
    """Test building a zipapp with an entry point (default main_guard=True)."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def main():\n    print('Hello')\n")

    output = tmp_path / "app.pyz"
    entry_point = "from mypackage.module import main; main()"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=entry_point,
    )

    # Verify zip file was created
    assert output.exists()
    assert output.is_file()

    # Verify __main__.py contains entry point wrapped in main guard (default)
    with zipfile.ZipFile(output, "r") as zf:
        assert "__main__.py" in zf.namelist()
        main_content = zf.read("__main__.py").decode()
        assert "if __name__ == '__main__':" in main_content
        assert entry_point in main_content

    # Verify shebang was prepended
    content = output.read_bytes()
    assert content.startswith(b"#!/usr/bin/env python3\n")

    # Verify executable permissions
    assert output.stat().st_mode & 0o111  # Check if any execute bit is set


def test_build_zipapp_without_entry_point(tmp_path: Path) -> None:
    """Test building a zipapp without an entry point."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def func():\n    pass\n")

    output = tmp_path / "app.pyz"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=None,
    )

    # Verify zip file was created
    assert output.exists()

    # Verify __main__.py was NOT created
    with zipfile.ZipFile(output, "r") as zf:
        assert "__main__.py" not in zf.namelist()


def test_build_zipapp_with_module_entry_point(tmp_path: Path) -> None:
    """Test building a zipapp with module:function entry point format."""
    # Create a test package
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "main.py").write_text("def main():\n    return 0\n")

    output = tmp_path / "app.pyz"
    entry_point = "from mypackage.main import main; main()"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=entry_point,
    )

    # Verify zip file was created
    assert output.exists()

    # Verify __main__.py contains entry point wrapped in main guard (default)
    with zipfile.ZipFile(output, "r") as zf:
        main_content = zf.read("__main__.py").decode()
        assert "if __name__ == '__main__':" in main_content
        assert "from mypackage.main import main" in main_content
        assert "main()" in main_content


def test_build_zipapp_includes_all_python_files(tmp_path: Path) -> None:
    """Test that all Python files from packages are included."""
    # Create a test package with multiple files
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module1.py").write_text("def func1():\n    pass\n")
    (pkg_dir / "module2.py").write_text("def func2():\n    pass\n")
    (pkg_dir / "subdir").mkdir()
    (pkg_dir / "subdir" / "__init__.py").write_text("")
    (pkg_dir / "subdir" / "submodule.py").write_text("def subfunc():\n    pass\n")

    output = tmp_path / "app.pyz"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=None,
    )

    # Verify all Python files are included
    with zipfile.ZipFile(output, "r") as zf:
        names = zf.namelist()
        assert "mypackage/__init__.py" in names
        assert "mypackage/module1.py" in names
        assert "mypackage/module2.py" in names
        assert "mypackage/subdir/__init__.py" in names
        assert "mypackage/subdir/submodule.py" in names


def test_build_zipapp_custom_shebang(tmp_path: Path) -> None:
    """Test building a zipapp with a custom shebang."""
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")

    output = tmp_path / "app.pyz"
    custom_shebang = "#!/usr/bin/env python3.12"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=None,
        shebang=custom_shebang,
    )

    # Verify custom shebang was prepended
    content = output.read_bytes()
    assert content.startswith(custom_shebang.encode() + b"\n")


def test_build_zipapp_empty_packages_raises_error(tmp_path: Path) -> None:
    """Test that building with empty packages list raises ValueError."""
    output = tmp_path / "app.pyz"

    with pytest.raises(ValueError, match="At least one package must be provided"):
        mod_build.build_zipapp(
            output=output,
            packages=[],
            entry_point=None,
        )


def test_build_zipapp_multiple_packages(tmp_path: Path) -> None:
    """Test building a zipapp with multiple packages."""
    # Create two test packages
    pkg1_dir = tmp_path / "package1"
    pkg1_dir.mkdir()
    (pkg1_dir / "__init__.py").write_text("")
    (pkg1_dir / "mod1.py").write_text("def func1():\n    pass\n")

    pkg2_dir = tmp_path / "package2"
    pkg2_dir.mkdir()
    (pkg2_dir / "__init__.py").write_text("")
    (pkg2_dir / "mod2.py").write_text("def func2():\n    pass\n")

    output = tmp_path / "app.pyz"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg1_dir, pkg2_dir],
        entry_point=None,
    )

    # Verify both packages are included
    with zipfile.ZipFile(output, "r") as zf:
        names = zf.namelist()
        assert "package1/__init__.py" in names
        assert "package1/mod1.py" in names
        assert "package2/__init__.py" in names
        assert "package2/mod2.py" in names


def test_build_zipapp_with_main_guard_enabled(tmp_path: Path) -> None:
    """Test building a zipapp with main_guard=True (default)."""
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def main():\n    print('Hello')\n")

    output = tmp_path / "app.pyz"
    entry_point = "from mypackage.module import main\nmain()"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=entry_point,
        main_guard=True,
    )

    # Verify __main__.py contains entry point wrapped in main guard
    with zipfile.ZipFile(output, "r") as zf:
        main_content = zf.read("__main__.py").decode()
        assert main_content.startswith("if __name__ == '__main__':")
        assert "    from mypackage.module import main" in main_content
        assert "    main()" in main_content
        # Verify proper indentation
        lines = main_content.splitlines()
        assert lines[0] == "if __name__ == '__main__':"
        assert lines[1].startswith("    ")


def test_build_zipapp_with_main_guard_disabled(tmp_path: Path) -> None:
    """Test building a zipapp with main_guard=False."""
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def main():\n    print('Hello')\n")

    output = tmp_path / "app.pyz"
    entry_point = "from mypackage.module import main; main()"

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=entry_point,
        main_guard=False,
    )

    # Verify __main__.py contains entry point without main guard
    with zipfile.ZipFile(output, "r") as zf:
        main_content = zf.read("__main__.py").decode()
        assert main_content == entry_point
        assert "if __name__ == '__main__':" not in main_content


def test_build_zipapp_main_guard_multiline_entry_point(tmp_path: Path) -> None:
    """Test main_guard with multi-line entry point code."""
    pkg_dir = tmp_path / "mypackage"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "module.py").write_text("def main():\n    print('Hello')\n")

    output = tmp_path / "app.pyz"
    entry_point = (
        "import sys\n"
        "from mypackage.module import main\n"
        "if len(sys.argv) > 1:\n"
        "    main()\n"
        "else:\n"
        "    print('No args')"
    )

    mod_build.build_zipapp(
        output=output,
        packages=[pkg_dir],
        entry_point=entry_point,
        main_guard=True,
    )

    # Verify __main__.py contains multi-line entry point properly indented
    with zipfile.ZipFile(output, "r") as zf:
        main_content = zf.read("__main__.py").decode()
        assert main_content.startswith("if __name__ == '__main__':")
        # All lines should be indented
        lines = main_content.splitlines()
        assert lines[0] == "if __name__ == '__main__':"
        for line in lines[1:]:
            if line.strip():  # Skip empty lines
                assert line.startswith("    "), f"Line not indented: {line!r}"
