import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent


def pytest_configure(config):
    sys.path.insert(0, str(REPO_ROOT))
    sandbox = tempfile.mkdtemp(prefix="kage-tests-")
    # kage.log opens "kage.log" in the cwd at import time, and utils.get_base_dir()
    # is cwd + "/kage" (kage.modules.test creates debug_modules/ there)
    os.makedirs(os.path.join(sandbox, "kage"))
    os.chdir(sandbox)
    # kage.main builds Kage() on import: it parses sys.argv and writes a run marker and
    # sessions/ into the data root. kage.main also resolves the loader<->dispatcher import cycle.
    with mock.patch.object(sys, "argv", ["kage", "--data-root", sandbox]):
        import kage.main  # noqa: F401
