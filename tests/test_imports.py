import importlib

import pytest

from conftest import REPO_ROOT

# kage/modules and kage/inline have no __init__.py, so pkgutil.walk_packages would skip them
MODULES = sorted(
    ".".join(path.relative_to(REPO_ROOT).with_suffix("").parts)
    for path in (REPO_ROOT / "kage").rglob("*.py")
    if path.name not in {"__init__.py", "__main__.py"}  # __main__ starts the userbot
)


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    # catches imports of names that were renamed or removed elsewhere
    importlib.import_module(name)
